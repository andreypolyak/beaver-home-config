import appdaemon.plugins.hass.hassapi as hass


class Cooler(hass.Hass):

  def initialize(self):
    self.listen_state(self.process, "light.ha_group_kitchen")
    self.listen_state(self.process, "input_select.living_scene")
    self.listen_state(self.process, "input_select.nearest_person_location")
    self.turn_on_cooler()


  def process(self, entity, attribute, old, new, kwargs):
    nearest_person_location = self.get_state("input_select.nearest_person_location")
    lights_on = self.get_state("light.ha_group_kitchen") == "on"
    living_scene = self.get_state("input_select.living_scene")
    if (
      (nearest_person_location != "not_home" and living_scene == "away")
      or (living_scene == "night" and not lights_on)
    ):
      self.turn_off_cooler()
    else:
      self.turn_on_cooler()


  def turn_on_cooler(self):
    self.call_service("switch/turn_on", entity_id="switch.kitchen_cooler_plug")


  def turn_off_cooler(self):
    self.call_service("switch/turn_off", entity_id="switch.kitchen_cooler_plug")
