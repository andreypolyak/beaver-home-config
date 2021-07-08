from base import Base


class UniversalTvSource(Base):

  def initialize(self):
    super().initialize()
    self.entity = "input_select.current_universal_tv_source"
    self.listen_state(self.on_apple_tv_change, "media_player.living_room_apple_tv")
    self.listen_state(self.on_playstation_4_change, "media_player.playstation_4")
    self.listen_state(self.on_tv_turn_off, "binary_sensor.living_room_tv", new="off")


  def on_apple_tv_change(self, entity, attribute, old, new, kwargs):
    self.select_option(self.entity, "apple_tv")


  def on_playstation_4_change(self, entity, attribute, old, new, kwargs):
    self.select_option(self.entity, "playstation_4")


  def on_tv_turn_off(self, entity, attribute, old, new, kwargs):
    self.select_option(self.entity, "apple_tv")
