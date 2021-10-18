from base import Base
import math

DELAY = 180
SAT_STEP = 2
MAX_LUX = 200
MIN_LUX = 0
# From 06:00 to 12:00 decrease saturation by maximum 20% (100% max saturation at 6, 80% at 9, 100% at 12)
MORNING_START = 6
MORNING_END = 12
PCT = 0.2


class CircadianUpdate(Base):

  def initialize(self):
    super().initialize()
    self.changed_ts = 0
    self.listen_state(self.on_lights_off, "light.ha_group_all")
    self.run_every(self.process, "now+300", 30)


  def process(self, kwargs):
    new_saturation = self.saturation
    if new_saturation is None:
      self.log("Balcony illuminance sensor is unavailable. Using saturation values from adaptive lighting integration")
      new_saturation = round(self.get_state("switch.adaptive_lighting_default", attribute="hs_color")[1])
    old_saturation = self.get_int_state("input_number.circadian_saturation")
    if self.entity_is_on("light.ha_group_all"):
      if abs(new_saturation - old_saturation) > SAT_STEP:
        if new_saturation > old_saturation:
          new_saturation = old_saturation + SAT_STEP
        elif new_saturation < old_saturation:
          new_saturation = old_saturation - SAT_STEP
    if new_saturation != old_saturation:
      self.set_saturation(new_saturation)


  @property
  def saturation(self):
    lux = self.get_int_state("sensor.balcony_illuminance")
    if lux is None:
      self.log("Can't read balcony illuminance value")
      return None
    last_seen = self.get_int_state("sensor.balcony_illuminance", attribute="last_seen")
    if last_seen is None:
      self.log("Can't get last seen parameter for balcony illuminance sensor")
      return None
    if self.get_delta_ts(last_seen) > 7200:
      self.log("Balcony illuminance sensor last seen more than 2 hours ago")
      return None
    if lux >= MAX_LUX:
      return 0
    elif lux < MIN_LUX:
      return 100
    else:
      saturation = int(math.ceil((MAX_LUX - lux) / ((MAX_LUX - MIN_LUX) / (100 / SAT_STEP - 1)))) * SAT_STEP
      saturation = saturation * self.morning_coeff
      return saturation


  @property
  def morning_coeff(self):
    midnight = self.parse_datetime("00:00:00", aware=True)
    now = self.get_now()
    seconds = (now - midnight).seconds
    start_time = MORNING_START * 3600
    end_time = MORNING_END * 3600
    middle_time = (end_time - start_time) / 2 + start_time
    for i in range(0, 23):
      seconds = 3600 * i
      if seconds < start_time or seconds > end_time:
        morning_coeff = 1
      elif seconds >= start_time and seconds <= middle_time:
        morning_coeff = 1 - (1 - (middle_time - seconds) / (middle_time - start_time)) * PCT
      elif seconds > middle_time and seconds <= end_time:
        morning_coeff = 1 - (end_time - seconds) / (end_time - middle_time) * PCT
    return morning_coeff


  def set_saturation(self, new_saturation):
    if new_saturation == self.get_int_state("input_number.circadian_saturation"):
      return
    if self.entity_is_on("light.ha_group_all") and self.get_delta_ts(self.changed_ts) < DELAY:
      return
    self.changed_ts = self.get_now_ts()
    self.set_value("input_number.circadian_saturation", new_saturation)


  def on_lights_off(self, entity, attribute, old, new, kwargs):
    self.process({})
