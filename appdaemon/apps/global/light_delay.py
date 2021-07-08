from base import Base


class LightDelay(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_scene_change, "input_select.living_scene", immediate=True)
    self.listen_state(self.on_scene_change, "input_select.sleeping_scene")


  def on_scene_change(self, entity, attribute, old, new, kwargs):
    if self.get_living_scene() in ["dark_cinema", "party", "night"]:
      self.turn_on_entity("input_boolean.living_zone_min_delay")
      self.turn_on_entity("input_boolean.sleeping_zone_min_delay")
    else:
      self.turn_off_entity("input_boolean.living_zone_min_delay")
      if self.get_sleeping_scene() == "night":
        self.turn_on_entity("input_boolean.sleeping_zone_min_delay")
      else:
        self.turn_off_entity("input_boolean.sleeping_zone_min_delay")
