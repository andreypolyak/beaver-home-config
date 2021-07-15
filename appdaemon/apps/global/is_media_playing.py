from base import Base


class IsMediaPlaying(Base):

  def initialize(self):
    super().initialize()
    self.handles = {}
    self.sonos_devices = []
    self.find_all_sonos_devices()
    for sonos_device in self.sonos_devices:
      self.handles[sonos_device] = None
      self.listen_state(self.on_sonos_change, sonos_device)
    self.handles["living_room_tv"] = None
    self.listen_state(self.on_tv_change, "binary_sensor.living_room_tv")
    self.listen_state(self.on_party_on, "input_select.living_scene", new="party")
    self.run_every(self.check_state, "now", 120)


  def find_all_sonos_devices(self):
    self.sonos_devices = []
    for media_player in self.get_state("media_player"):
      if "sonos" in media_player:
        sonos_device = media_player.replace("media_player.", "")
        self.sonos_devices.append(sonos_device)


  def on_tv_change(self, entity, attribute, old, new, kwargs):
    self.check_tv_state()


  def on_sonos_change(self, entity, attribute, old, new, kwargs):
    self.check_sonos_state(entity.replace("media_player.", ""))


  def check_state(self, kwargs):
    for device in self.sonos_devices:
      self.check_sonos_state(device)
    self.check_tv_state()


  def set_not_playing(self, kwargs):
    device = kwargs["device"]
    self.turn_off_entity(f"input_boolean.{device}_playing")


  def on_party_on(self, entity, attribute, old, new, kwargs):
    for device in self.sonos_devices:
      self.cancel_handle(self.handles[device])
      self.set_not_playing({"device": device})
      self.cancel_handle(self.handles["living_room_tv"])
    self.set_not_playing({"device": "living_room_tv"})


  def check_tv_state(self):
    if self.get_living_scene() == "party":
      return
    if self.is_entity_on("binary_sensor.living_room_tv"):
      self.turn_on_entity("input_boolean.living_room_tv_playing")
      self.turn_off_entity("input_boolean.living_room_sonos_playing")
      return
    self.cancel_handle(self.handles["living_room_tv"])
    self.handles["living_room_tv"] = self.run_in(self.set_not_playing, 60, device="living_room_tv")


  def check_sonos_state(self, entity):
    if self.get_living_scene() == "party":
      return
    sonos_state = self.get_state(f"media_player.{entity}")
    device = entity.replace("media_player.", "")
    if sonos_state == "playing" and device == "living_room_sonos" and self.is_entity_on("binary_sensor.living_room_tv"):
      return
    if sonos_state == "playing":
      self.log(f"Device {device} is playing")
      self.cancel_handle(self.handles[device])
      self.turn_on_entity(f"input_boolean.{device}_playing")
    elif sonos_state == "paused":
      self.log(f"Device {device} is paused")
      self.cancel_handle(self.handles[device])
      self.handles[device] = self.run_in(self.set_not_playing, 60, device=device)
