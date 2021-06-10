import appdaemon.plugins.hass.hassapi as hass


class Cooler(hass.Hass):

  def initialize(self):
    self.listen_state(self.on_scene_change, "input_select.living_scene")
    self.listen_state(self.on_lights_off, "light.ha_group_kitchen", new="off")
    binary_sensors = self.get_state("binary_sensor")
    for binary_sensor in binary_sensors:
      if binary_sensor.endswith("_motion") and "kitchen" in binary_sensor:
        self.listen_state(self.on_motion, binary_sensor, new="on", old="off")
    self.turn_on_cooler({})


  def on_lights_off(self, entity, attribute, old, new, kwargs):
    if self.get_state("input_select.living_scene") == "night":
      self.turn_off_cooler({})


  def on_scene_change(self, entity, attribute, old, new, kwargs):
    if new in ["night", "away"]:
      self.turn_off_cooler({})
    else:
      self.turn_on_cooler({})


  def on_motion(self, entity, attribute, old, new, kwargs):
    if self.get_state("input_select.living_scene") != "away":
      self.turn_on_cooler({})


  def turn_on_cooler(self, kwargs):
    self.call_service("switch/turn_on", entity_id="switch.kitchen_cooler_plug")


  def turn_off_cooler(self, kwargs):
    self.call_service("switch/turn_off", entity_id="switch.kitchen_cooler_plug")
