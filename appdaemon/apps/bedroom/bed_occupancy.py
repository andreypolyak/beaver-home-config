from base import Base

SENSORS = ["bedroom_bed_occupancy", "bedroom_theo_bed_occupancy"]


class BedOccupancy(Base):

  def initialize(self):
    for sensor in SENSORS:
      self.listen_state(self.on_change, f"binary_sensor.{sensor}", new="off", old="on")
    self.listen_state(self.on_change, "input_select.living_scene", new="day", old="night")
    self.listen_state(self.on_theo_bed_occupancy, "binary_sensor.bedroom_theo_bed_occupancy", new="on", old="off")


  def on_change(self, entity, attribute, old, new, kwargs):
    if self.get_sleeping_scene() != "night" or self.get_living_scene() == "night":
      return
    for sensor in SENSORS:
      if self.is_entity_on(f"binary_sensor.{sensor}"):
        return
    if self.is_entity_off("binary_sensor.night_scene_enough"):
      return
    self.log(f"Turning on day scene in sleeping zone because {entity} state changed")
    self.set_sleeping_scene("day")


  def on_theo_bed_occupancy(self, entity, attribute, old, new, kwargs):
    if self.now_is_between("20:00:00", "10:00:00") and self.get_sleeping_scene() == "day":
      self.log("Turning on night scene in sleeping zone because Theo bed was occupied")
      self.set_sleeping_scene("night")
