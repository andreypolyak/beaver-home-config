import appdaemon.plugins.hass.hassapi as hass
import math
import datetime

DELAY = 120
SAT_STEP = 2
MAX_LUX = 300
MIN_LUX = 10
MORNING_START = 6
MORNING_END = 12
PCT = 0.2


class CircadianUpdate(hass.Hass):

  def initialize(self):
    self.changed_ts = 0
    self.listen_state(self.on_lights_off, "light.ha_group_all")
    self.run_every(self.process, "now", 60)


  def process(self, kwargs):
    new_saturation = self.calculate_saturation()
    if not new_saturation:
      self.log("Balcony illuminance sensor is unavailable. Using saturation values from adaptive lighting integration")
      new_saturation = self.get_state("switch.adaptive_lighting_default", attribute="hs_color")[1]
    kelvin = self.calculate_kelvin(new_saturation)
    old_saturation = self.get_old_saturation()
    if self.get_state("light.ha_group_all") == "on":
      if abs(new_saturation - old_saturation) > SAT_STEP:
        if new_saturation > old_saturation:
          new_saturation = old_saturation + SAT_STEP
        elif new_saturation < old_saturation:
          new_saturation = old_saturation - SAT_STEP
    if new_saturation != old_saturation:
      self.set_saturation(new_saturation, kelvin)


  def calculate_saturation(self):
    try:
      lux = float(int(self.get_state("sensor.balcony_illuminance")))
      last_seen = float(self.get_state("sensor.balcony_illuminance", attribute="last_seen"))
    except ValueError:
      return None
    if self.get_now_ts() - last_seen > 7200:
      return None
    if lux >= MAX_LUX:
      return 0
    elif lux < MIN_LUX:
      return 100
    else:
      saturation = int(math.ceil((MAX_LUX - lux) / ((MAX_LUX - MIN_LUX) / (100 / SAT_STEP - 1)))) * SAT_STEP
      saturation = saturation * self.calculate_morning_coeff()
      return saturation


  def calculate_morning_coeff(self):
    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
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


  def calculate_kelvin(self, saturation):
    kelvin = 2000 + saturation * ((6500 - 2000) / 100)
    return kelvin

  def set_saturation(self, new_saturation, kelvin):
    if new_saturation == self.get_old_saturation:
      return
    if self.get_state("light.ha_group_all") == "on":
      if (self.get_now_ts() - self.changed_ts) < DELAY:
        return
    self.changed_ts = self.get_now_ts()
    self.call_service("input_number/set_value", entity_id="input_number.circadian_saturation", value=new_saturation)
    self.call_service("input_number/set_value", entity_id="input_number.circadian_kelvin", value=kelvin)


  def get_old_saturation(self):
    return int(float(self.get_state("input_number.circadian_saturation")))


  def on_lights_off(self, entity, attribute, old, new, kwargs):
    self.process({})
