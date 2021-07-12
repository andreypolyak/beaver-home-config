from base import Base


class MediaControl(Base):

  def initialize(self):
    super().initialize()
    self.sonos_devices = []
    for media_player in self.get_state("media_player"):
      if "_sonos" in media_player:
        self.sonos_devices.append(media_player)
    self.listen_state(self.on_scene_change, "input_select.living_scene")


  def on_scene_change(self, entity, attribute, old, new, kwargs):
    if new in ["night", "away"]:
      self.pause_all()


  def pause_all(self):
    for sonos_device in self.sonos_devices:
      self.media_pause(sonos_device)
    self.sonos_unjoin("all")
