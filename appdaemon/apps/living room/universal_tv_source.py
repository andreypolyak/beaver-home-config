import appdaemon.plugins.hass.hassapi as hass


class UniversalTvSource(hass.Hass):

  def initialize(self):
    self.entity = "input_select.current_universal_tv_source"
    self.listen_state(self.on_apple_tv_change, "media_player.living_room_apple_tv")
    self.listen_state(self.on_playstation_4_change, "media_player.playstation_4")
    self.listen_state(self.on_tv_turn_off, "binary_sensor.living_room_tv", new="off")


  def on_apple_tv_change(self, entity, attribute, old, new, kwargs):
    self.call_service("input_select/select_option", entity_id=self.entity, option="apple_tv")


  def on_playstation_4_change(self, entity, attribute, old, new, kwargs):
    self.call_service("input_select/select_option", entity_id=self.entity, option="playstation_4")


  def on_tv_turn_off(self, entity, attribute, old, new, kwargs):
    self.call_service("input_select/select_option", entity_id=self.entity, option="apple_tv")
