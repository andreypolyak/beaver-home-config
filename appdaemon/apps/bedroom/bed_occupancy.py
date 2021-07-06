import appdaemon.plugins.hass.hassapi as hass

SENSORS = ["bedroom_bed_occupancy", "bedroom_theo_bed_occupancy"]


class BedOccupancy(hass.Hass):

  def initialize(self):
    for sensor in SENSORS:
      self.listen_state(self.on_change, f"binary_sensor.{sensor}", new="off", old="on")
    self.listen_state(self.on_change, "input_select.living_scene", new="day", old="night")
    self.listen_state(self.on_theo_bed_occupancy, "binary_sensor.bedroom_theo_bed_occupancy", new="on", old="off")


  def on_change(self, entity, attribute, old, new, kwargs):
    sleeping_scene = self.get_state("input_select.sleeping_scene")
    living_scene = self.get_state("input_select.living_scene")
    night_scene_in_living_zone_enough = self.get_state("binary_sensor.night_scene_in_living_zone_enough") == "on"
    if sleeping_scene != "night" or living_scene == "night":
      return
    for sensor in SENSORS:
      if self.get_state(f"binary_sensor.{sensor}") == "on":
        return
    if not night_scene_in_living_zone_enough:
      return
    self.log(f"Turning on day scene in sleeping zone because {entity} state changed")

  def on_theo_bed_occupancy(self, entity, attribute, old, new, kwargs):
    if self.now_is_between("20:00:00", "10:00:00") and self.get_scene("sleeping") == "day":
      self.log(f"Turning on night scene in sleeping zone because of occupancy in Theo bed")
      self.set_scene("sleeping", "night")
