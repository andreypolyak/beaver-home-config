from base import Base

SENSORS = ["bedroom_bed_occupancy", "bedroom_theo_bed_occupancy"]


class BedOccupancy(Base):

  def initialize(self):
    for sensor in SENSORS:
      self.listen_state(self.on_change, f"binary_sensor.{sensor}", new="off", old="on")
    self.listen_state(self.on_change, "binary_sensor.bedroom_door")
    self.listen_state(self.on_theo_bed_occupancy, "binary_sensor.bedroom_theo_bed_occupancy", new="on", old="off")


  def on_change(self, entity, attribute, old, new, kwargs):
    if self.sleeping_scene != "night" or self.living_scene == "night":
      return
    for sensor in SENSORS:
      if self.entity_is_on(f"binary_sensor.{sensor}"):
        return
    if self.entity_is_off("binary_sensor.bedroom_door"):
      return
    elif self.entity_is_on("input_boolean.alarm_ringing"):
      return
    self.log("Turning on day scene in sleeping zone because beds are not occupied")
    self.set_sleeping_scene("day")


  def on_theo_bed_occupancy(self, entity, attribute, old, new, kwargs):
    if self.now_is_between("20:00:00", "10:00:00") and self.sleeping_scene == "day":
      self.log("Turning on night scene in sleeping zone because Theo bed was occupied")
      self.set_sleeping_scene("night")
