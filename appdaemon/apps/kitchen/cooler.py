from base import Base


class Cooler(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_change, "light.ha_group_kitchen", immediate=True)
    self.listen_state(self.on_change, "input_select.living_scene")
    self.listen_state(self.on_change, "cover.kitchen_cover", attribute="current_position")


  def on_change(self, entity, attribute, old, new, kwargs):
    is_cover_closed = self.get_state("cover.kitchen_cover", attribute="current_position") == 0
    is_lights_off = self.is_entity_off("light.ha_group_kitchen")
    is_night_with_open_cover = self.get_living_scene() == "night" and is_lights_off and not is_cover_closed
    if self.get_living_scene() == "away" or is_night_with_open_cover:
      self.turn_off_entity("switch.kitchen_cooler_plug")
    else:
      self.turn_on_entity("switch.kitchen_cooler_plug")
