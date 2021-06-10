import appdaemon.plugins.hass.hassapi as hass


class BathroomFan(hass.Hass):

  def initialize(self):
    self.listen_state(self.on_bathroom_door, "binary_sensor.bathroom_door")


  def on_bathroom_door(self, entity, attribute, old, new, kwargs):
    if new == "off":
      self.call_service("switch/turn_on", entity_id="switch.bathroom_fan")
    else:
      self.call_service("switch/turn_off", entity_id="switch.bathroom_fan")
