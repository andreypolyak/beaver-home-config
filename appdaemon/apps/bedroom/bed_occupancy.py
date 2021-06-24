import appdaemon.plugins.hass.hassapi as hass

SENSORS = ["bedroom_bed_occupancy", "bedroom_theo_bed_occupancy"]


class BedOccupancy(hass.Hass):

  def initialize(self):
    for sensor in SENSORS:
      self.listen_state(self.on_change, f"binary_sensor.{sensor}", new="off", old="on")
    self.listen_state(self.on_change, "input_select.living_scene", new="day", old="night")


  def on_change(self, entity, attribute, old, new, kwargs):
    sleeping_scene = self.get_state("input_select.sleeping_scene")
    living_scene = self.get_state("input_select.living_scene")
    if sleeping_scene != "night" or living_scene != "day":
      return
    for sensor in SENSORS:
      if self.get_state(f"binary_sensor.{sensor}") == "on":
        return
    self.log(f"Turning on day scene in sleeping zone because {entity} state changed")
    self.call_service("input_select/select_option", entity_id="input_select.sleeping_scene", option="day")
