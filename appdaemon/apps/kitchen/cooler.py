from base import Base


class Cooler(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_change, "light.ha_group_kitchen", immediate=True)
    self.listen_state(self.on_change, "input_select.living_scene")


  def on_change(self, entity, attribute, old, new, kwargs):
    is_lights_off = self.is_entity_off("light.ha_group_kitchen")
    if self.get_living_scene() == "away" or (self.get_living_scene() == "night" and is_lights_off):
      self.turn_off_entity("switch.kitchen_cooler_plug")
    else:
      self.turn_on_entity("switch.kitchen_cooler_plug")
