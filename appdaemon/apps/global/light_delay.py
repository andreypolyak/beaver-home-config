from base import Base


class LightDelay(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_scene_change, "input_select.living_scene", immediate=True)
    self.listen_state(self.on_scene_change, "input_select.sleeping_scene")
    self.listen_state(self.on_scene_change, "binary_sensor.bedroom_door")


  def on_scene_change(self, entity, attribute, old, new, kwargs):
    if self.living_scene in ["dark_cinema", "party", "night"]:
      self.set_min_delay("living")
      self.set_min_delay("sleeping")
    else:
      if self.entity_is_off("binary_sensor.bedroom_door"):
        self.set_min_delay("living")
      else:
        self.cancel_min_delay("living")
      if self.sleeping_scene == "night":
        self.set_min_delay("sleeping")
      else:
        self.cancel_min_delay("sleeping")


  def set_min_delay(self, zone):
    self.turn_on_entity(f"input_boolean.{zone}_zone_min_delay")


  def cancel_min_delay(self, zone):
    self.turn_off_entity(f"input_boolean.{zone}_zone_min_delay")
