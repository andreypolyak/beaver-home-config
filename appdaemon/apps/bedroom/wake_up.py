from base import Base


class WakeUp(Base):

  def initialize(self):
    super().initialize()
    self.handle = None
    self.wake_activity_ts = 0
    for binary_sensor in self.get_state("binary_sensor"):
      if "bedroom_door" in binary_sensor:
        self.listen_state(self.on_sleep_activity, binary_sensor, new="off", old="on")
        self.listen_state(self.on_wake_activity, binary_sensor, new="on", old="off")
      elif "bedroom_bed_top_occupancy" in binary_sensor:
        self.listen_state(self.on_sleep_activity, binary_sensor, new="on", old="off")
      elif "bedroom_theo_bed_occupancy" in binary_sensor:
        self.listen_state(self.on_sleep_activity, binary_sensor, new="on", old="off")
        self.listen_state(self.on_theo_bed_occupancy, "binary_sensor.bedroom_theo_bed_occupancy", new="on", old="off")
      elif not binary_sensor.endswith("_motion"):
        continue
      elif "bedroom_floor" in binary_sensor or "bedroom_table" in binary_sensor:
        self.listen_state(self.on_wake_activity, binary_sensor, new="on", old="off")
      elif "kitchen" in binary_sensor or "living_room" in binary_sensor:
        self.listen_state(self.on_living_zone_activity, binary_sensor, new="on", old="off")


  def on_wake_activity(self, entity, attribute, old, new, kwargs):
    self.log(f"Wake activity on {entity}")
    self.wake_activity_ts = self.get_now_ts()


  def on_sleep_activity(self, entity, attribute, old, new, kwargs):
    self.log(f"Sleep activity on {entity}, cancelling the wake process")
    self.cancel_handle(self.handle)


  def on_living_zone_activity(self, entity, attribute, old, new, kwargs):
    if (
      self.get_delta_ts(self.wake_activity_ts) < 10
      and self.entity_is_on("binary_sensor.bedroom_door")
      and self.entity_is_off("binary_sensor.bedroom_bed_top_occupancy")
      and self.entity_is_off("binary_sensor.bedroom_theo_bed_occupancy")
      and not self.timer_running(self.handle)
      and self.sleeping_scene == "night"
      and self.entity_is_on("binary_sensor.night_scene_enough")
    ):
      self.log(f"Living zone activity on {entity}, setting timer for wake process")
      self.handle = self.run_in(self.wake, 10)


  def wake(self, kwargs):
    if (
      self.entity_is_on("binary_sensor.bedroom_door")
      and self.entity_is_off("binary_sensor.bedroom_bed_top_occupancy")
      and self.entity_is_off("binary_sensor.bedroom_theo_bed_occupancy")
      and self.sleeping_scene == "night"
      and self.living_scene != "night"
    ):
      if self.entity_is_on("input_boolean.alarm_ringing"):
        self.log("Wake process -> finish alarm")
        self.fire_event("finish_alarm")
      else:
        self.log("Wake process -> turn on day scene")
        self.set_sleeping_scene("day")


  def on_theo_bed_occupancy(self, entity, attribute, old, new, kwargs):
    if self.now_is_between("20:00:00", "10:00:00") and self.sleeping_scene == "day":
      self.log("Turning on night scene in sleeping zone because Theo bed was occupied")
      self.set_sleeping_scene("night")
