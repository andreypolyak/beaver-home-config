import appdaemon.plugins.hass.hassapi as hass

SONOS_MIN_VOLUME = 0.11
# Meditation playlist id
ALARM_DIALOG_PLAYLIST_ID = "2383988"


class YandexStation(hass.Hass):

  def initialize(self):
    self.handle = None
    self.sonos_volume = None
    self.stop_required = {}
    self.listen_state(self.on_living_room_alice_state, "media_player.living_room_yandex_station",
                      attribute="alice_state")
    self.rooms = []
    media_players = self.get_state("media_player")
    for media_player in media_players:
      if media_player.endswith("_yandex_station"):
        self.rooms.append(media_player.replace("media_player.", "").replace("_yandex_station", ""))
    for room in self.rooms:
      self.stop_required[room] = False
      entity = f"media_player.{room}_yandex_station"
      self.listen_state(self.on_playing, entity, new="playing")
      self.listen_state(self.on_stop_speaking, entity, attribute="alice_state", old="SPEAKING", new="LISTENING")
      self.listen_state(self.on_busy, entity, attribute="alice_state", new="BUSY")
      self.listen_state(self.on_idle, entity, attribute="alice_state", new="IDLE")
      self.listen_state(self.on_alice_change, f"media_player.{room}_yandex_station", attribute="alice_state")
    self.listen_event(self.on_yandex_speak_text, "yandex_speak_text")
    self.listen_event(self.on_yandex_speak_text, "telegram_text")
    self.listen_event(self.on_yandex_intent, "yandex_intent")


  def on_yandex_intent(self, event_name, data, kwargs):
    self.log(f"Initial data: {data}")
    dialog_name = self.get_state("input_text.active_dialog")
    if len(dialog_name) > 0:
      self.fire_event(dialog_name, data=data)


  def on_alice_change(self, entity, attribute, old, new, kwargs):
    room = self.get_state("input_select.last_active_yandex_station")
    dialog_name = self.get_state("input_text.active_dialog")
    self.log(f"Entity: {entity}, new_alice_state: {old}->{new}, current_room: {room}, dialog_name: {dialog_name}")


  def on_busy(self, entity, attribute, old, new, kwargs):
    for room in self.rooms:
      if room in entity:
        self.call_service("input_select/select_option", entity_id="input_select.last_active_yandex_station",
                          option=room)


  def on_idle(self, entity, attribute, old, new, kwargs):
    if old == "BUSY":
      return
    active_room = self.get_state("input_select.last_active_yandex_station")
    if self.get_state("input_text.active_dialog") != "" and active_room in entity:
      if self.timer_running(self.handle):
        self.cancel_timer(self.handle)
      self.handle = self.run_in(self.exit_dialog, 1, entity=entity)


  def exit_dialog(self, kwargs):
    entity = kwargs["entity"]
    active_room = self.get_state("input_select.last_active_yandex_station")
    if self.get_state("input_text.active_dialog") != "" and active_room in entity:
      self.call_service("media_player/volume_set", entity_id=entity, volume_level=0)
      self.call_service("media_player/turn_off", entity_id=entity)
      self.call_service("input_text/set_value", entity_id="input_text.active_dialog", value="")


  def on_playing(self, entity, attribute, old, new, kwargs):
    entity_picture = self.get_state(entity, attribute="entity_picture")
    self.log("Stop music from Yandex Station")
    self.call_service("media_player/media_pause", entity_id=entity)
    if ALARM_DIALOG_PLAYLIST_ID in entity_picture and self.get_state("input_text.active_dialog") == "":
      self.fire_event("alarm_dialog")


  def on_living_room_alice_state(self, entity, attribute, old, new, kwargs):
    if new in ["SPEAKING", "BUSY"]:
      sonos_volume = float(self.get_state("media_player.living_room_sonos", attribute="volume_level"))
      if sonos_volume != SONOS_MIN_VOLUME:
        self.sonos_volume = sonos_volume
        self.log(f"Setting old Sonos volume {str(self.sonos_volume)}")
        self.call_service("media_player/volume_set", entity_id="media_player.living_room_sonos",
                          volume_level=SONOS_MIN_VOLUME)
    elif new == "IDLE":
      self.log(f"Updating Sonos volume {str(self.sonos_volume)}")
      if self.sonos_volume:
        self.call_service("media_player/volume_set", entity_id="media_player.living_room_sonos",
                          volume_level=self.sonos_volume)


  def on_yandex_speak_text(self, event_name, data, kwargs):
    self.log("Start announcing on Yandex Station")
    if "room" not in data:
      room = "living_room"
    else:
      room = data["room"]
    self.stop_required[room] = True
    args = {
      "entity_id": f"media_player.{room}_yandex_station",
      "media_content_id": data["text"],
      "media_content_type": "dialog"
    }
    if "volume_level" in data:
      args["extra"] = {"volume_level": data["volume_level"]}
    self.call_service("media_player/play_media", **args)


  def on_stop_speaking(self, entity, attribute, old, new, kwargs):
    room = entity.replace("media_player.", "").replace("_yandex_station", "")
    if self.stop_required[room]:
      self.log("Stopping yandex")
      self.stop_required[room] = False
      self.call_service("media_player/turn_off", entity_id=entity)
