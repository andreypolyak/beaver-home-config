import appdaemon.plugins.hass.hassapi as hass


class MediaControl(hass.Hass):

  def initialize(self):
    self.sonos_devices = []
    media_players = self.get_state("media_player")
    for media_player in media_players.keys():
      if "_sonos" in media_player:
        self.sonos_devices.append(media_player)
    self.listen_state(self.on_scene_change, "input_select.living_scene")


  def on_scene_change(self, entity, attribute, old, new, kwargs):
    if new in ["night", "away"]:
      self.pause_all()


  def pause_all(self):
    for sonos_device in self.sonos_devices:
      self.call_service("media_player/media_pause", entity_id=sonos_device)
    for sonos_device in self.sonos_devices:
      self.call_service("sonos/unjoin", entity_id=sonos_device)
