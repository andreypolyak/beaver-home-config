from base import Base


class Cooler(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_change, "light.ha_group_kitchen", immediate=True)
    self.listen_state(self.on_change, "input_select.living_scene")
    self.listen_state(self.on_change, "input_select.nearest_person_location")


  def on_change(self, entity, attribute, old, new, kwargs):
    if (
      (self.get_nearest_person_location() != "not_home" and self.get_living_scene() == "away")
      or (self.get_living_scene() == "night" and self.is_entity_off("light.ha_group_kitchen"))
    ):
      self.turn_off_entity("switch.kitchen_cooler_plug")
    else:
      self.turn_on_entity("switch.kitchen_cooler_plug")
