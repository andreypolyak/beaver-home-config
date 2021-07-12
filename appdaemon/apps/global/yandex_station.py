from base import Base

SONOS_MIN_VOLUME = 0.11
# Meditation playlist id
ALARM_DIALOG_PLAYLIST_ID = "2383988"


class YandexStation(Base):

  def initialize(self):
    super().initialize()
    self.handle = None
    self.sonos_volume = None
    self.stop_required = {}
    entity = "media_player.living_room_yandex_station"
    self.listen_state(self.on_living_room_alice_state, entity, attribute="alice_state")
    self.rooms = []
    for media_player in self.get_state("media_player"):
      if media_player.endswith("_yandex_station"):
        self.rooms.append(media_player.replace("media_player.", "").replace("_yandex_station", ""))
    for room in self.rooms:
      self.stop_required[room] = False
      entity = f"media_player.{room}_yandex_station"
      self.listen_state(self.on_playing, entity, new="playing")
      self.listen_state(self.on_stop_speaking, entity, attribute="alice_state", old="SPEAKING", new="LISTENING")
      self.listen_state(self.on_busy, entity, attribute="alice_state", new="BUSY")
      self.listen_state(self.on_idle, entity, attribute="alice_state", new="IDLE")
    self.listen_event(self.on_yandex_speak_text, "yandex_speak_text")
    self.listen_event(self.on_yandex_speak_text, "telegram_text")
    self.listen_event(self.on_yandex_intent, "yandex_intent")


  def on_yandex_intent(self, event_name, data, kwargs):
    self.log(f"Initial data: {data}")
    dialog_name = self.get_state("input_text.active_dialog")
    if len(dialog_name) > 0:
      self.fire_event(dialog_name, data=data)


  def on_busy(self, entity, attribute, old, new, kwargs):
    busy_entity = entity
    for room in self.rooms:
      if room in busy_entity:
        self.select_option("input_select.last_active_yandex_station", room)


  def on_idle(self, entity, attribute, old, new, kwargs):
    if old == "BUSY":
      return
    active_room = self.get_state("input_select.last_active_yandex_station")
    if self.is_dialog_active() and active_room in entity:
      self.cancel_handle(self.handle)
      self.handle = self.run_in(self.exit_dialog, 1, entity=entity)


  def exit_dialog(self, kwargs):
    entity = kwargs["entity"]
    active_room = self.get_state("input_select.last_active_yandex_station")
    if self.is_dialog_active() and active_room in entity:
      self.volume_set(entity, 0)
      self.turn_off_entity(entity)
      self.set_value("input_text.active_dialog", "")


  def on_playing(self, entity, attribute, old, new, kwargs):
    entity_picture = self.get_state(entity, attribute="entity_picture")
    self.log("Stop music from Yandex Station")
    self.media_pause(entity)
    if ALARM_DIALOG_PLAYLIST_ID in entity_picture and not self.is_dialog_active():
      self.fire_event("alarm_dialog")


  def on_living_room_alice_state(self, entity, attribute, old, new, kwargs):
    sonos_entity = "media_player.living_room_sonos"
    if new in ["SPEAKING", "BUSY"]:
      sonos_volume = self.get_float_state(sonos_entity, attribute="volume_level")
      if sonos_volume != SONOS_MIN_VOLUME:
        self.sonos_volume = sonos_volume
        self.log(f"Setting old Sonos volume {self.sonos_volume}")
        self.volume_set(sonos_entity, SONOS_MIN_VOLUME)
    elif new == "IDLE":
      self.log(f"Updating Sonos volume {self.sonos_volume}")
      if self.sonos_volume:
        self.volume_set(sonos_entity, self.sonos_volume)


  def on_yandex_speak_text(self, event_name, data, kwargs):
    self.log("Start announcing on Yandex Station")
    if "room" not in data:
      room = "living_room"
    else:
      room = data["room"]
    if self.get_state(f"sensor.{room}_yandex_station_connection") != "ok":
      return
    self.stop_required[room] = True
    extra = {}
    if "volume_level" in data:
      extra = {"volume_level": data["volume_level"]}
    self.play_media(f"media_player.{room}_yandex_station", data["text"], "dialog", extra=extra)


  def on_stop_speaking(self, entity, attribute, old, new, kwargs):
    room = entity.replace("media_player.", "").replace("_yandex_station", "")
    if self.stop_required[room]:
      self.log("Stopping yandex")
      self.stop_required[room] = False
      self.turn_off_entity(entity)


  def is_dialog_active(self):
    return self.get_state("input_text.active_dialog") != ""
