from base import Base


class Cooler(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_change, "light.ha_group_kitchen", immediate=True)
    self.listen_state(self.on_change, "input_select.nearest_person_location")
    self.listen_state(self.on_change, "input_select.living_scene")


  def on_change(self, entity, attribute, old, new, kwargs):
    persons_not_home = self.get_state("input_select.nearest_person_location") == "not_home"
    living_scene = self.living_scene
    lights_off = self.entity_is_off("light.ha_group_kitchen")
    if (living_scene == "away" and persons_not_home) or (living_scene == "night" and lights_off):
      self.turn_off_entity("switch.kitchen_cooler_plug")
    else:
      self.turn_on_entity("switch.kitchen_cooler_plug")
