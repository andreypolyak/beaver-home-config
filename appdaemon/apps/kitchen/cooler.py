import appdaemon.plugins.hass.hassapi as hass


class Cooler(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    for entity in self.persons.get_all_person_location_entities():
      self.listen_state(self.process, entity)
    self.listen_state(self.process, "light.ha_group_kitchen")
    self.listen_state(self.process, "input_select.living_scene")
    self.turn_on_cooler()


  def process(self, entity, attribute, old, new, kwargs):
    people_inside_district = self.persons.is_any_person_inside_location("district")
    lights_on = self.get_state("light.ha_group_kitchen") == "on"
    living_scene = self.get_state("input_select.living_scene")
    if (not people_inside_district and living_scene == "away") or (living_scene == "night" and not lights_on):
      self.turn_off_cooler()
    else:
      self.turn_on_cooler()


  def turn_on_cooler(self):
    self.call_service("switch/turn_on", entity_id="switch.kitchen_cooler_plug")


  def turn_off_cooler(self):
    self.call_service("switch/turn_off", entity_id="switch.kitchen_cooler_plug")
