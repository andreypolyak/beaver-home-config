import appdaemon.plugins.hass.hassapi as hass


class IsMediaPlaying(hass.Hass):

  def initialize(self):
    self.handles = {}
    self.sonos_devices = []
    media_players = self.get_state("media_player")
    for media_player in media_players.keys():
      if "_sonos" in media_player:
        device = media_player.replace("media_player.", "")
        self.sonos_devices.append(device)
        self.handles[device] = None
        self.listen_state(self.on_sonos_change, media_player)
    self.tv_devices = ["universal_apple_tv", "universal_playstation_4"]
    self.handles["living_room_tv"] = None
    for device in self.tv_devices:
      self.listen_state(self.on_tv_change, f"media_player.{device}")
    self.listen_state(self.on_party_on, "input_select.living_scene", new="party")
    self.run_every(self.check_state, "now", 600)


  def on_tv_change(self, entity, attribute, old, new, kwargs):
    self.check_tv_state()


  def on_sonos_change(self, entity, attribute, old, new, kwargs):
    self.log("Sonos change")
    self.check_sonos_state(entity.replace("media_player.", ""))


  def check_state(self, kwargs):
    for device in self.sonos_devices:
      self.check_sonos_state(device)
    self.check_tv_state()


  def set_not_playing(self, kwargs):
    device = kwargs["device"]
    self.call_service("input_boolean/turn_off", entity_id=f"input_boolean.{device}_playing")


  def on_party_on(self, entity, attribute, old, new, kwargs):
    for device in self.sonos_devices:
      self.cancel_media_handle(device)
      self.set_not_playing({"device": device})
      self.cancel_media_handle("living_room_tv")
    self.set_not_playing({"device": "living_room_tv"})


  def check_tv_state(self):
    self.log("Checking TV State")
    tv_source = self.get_state("input_select.current_universal_tv_source")
    tv_state = self.get_state(f"media_player.universal_{tv_source}")
    if self.get_state("input_select.living_scene") == "party":
      return
    is_tv_in_living_room_sonos = self.get_state("media_player.living_room_sonos", attribute="source") == "TV"
    if tv_state != "off":
      self.log("TV On")
      self.cancel_media_handle("living_room_tv")
      self.call_service("input_boolean/turn_on", entity_id="input_boolean.living_room_tv_playing")
      if is_tv_in_living_room_sonos:
        self.call_service("input_boolean/turn_off", entity_id="input_boolean.living_room_sonos_playing")
    elif tv_state == "off":
      self.log("TV Off")
      self.cancel_media_handle("living_room_tv")
      self.handles["living_room_tv"] = self.run_in(self.set_not_playing, 60, device="living_room_tv")


  def check_sonos_state(self, entity):
    sonos_state = self.get_state(f"media_player.{entity}")
    if self.get_state("input_select.living_scene") == "party":
      return
    device = entity.replace("media_player.", "")
    is_tv_in_living_room_sonos = self.get_state("media_player.living_room_sonos", attribute="source") == "TV"
    if (
      sonos_state == "playing"
      and (
        (device == "living_room_sonos" and not is_tv_in_living_room_sonos)
        or device != "living_room_sonos"
      )
    ):
      self.cancel_media_handle(device)
      self.call_service("input_boolean/turn_on", entity_id=f"input_boolean.{device}_playing")
    elif sonos_state == "paused":
      self.cancel_media_handle(device)
      self.handles[device] = self.run_in(self.set_not_playing, 60, device=device)


  def cancel_media_handle(self, device):
    if self.timer_running(self.handles[device]):
      self.cancel_timer(self.handles[device])
