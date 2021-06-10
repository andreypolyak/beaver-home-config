import appdaemon.plugins.hass.hassapi as hass
import math

DELAY = 120
STEP = 2
MAX = 300
MIN = 10


class CircadianUpdate(hass.Hass):

  def initialize(self):
    self.changed_ts = 0
    self.listen_state(self.on_lights_off, "light.ha_group_all")
    self.run_every(self.process, "now", 60)


  def calculate_saturation(self):
    try:
      lux = float(int(self.get_state("sensor.balcony_illuminance")))
    except ValueError:
      return None
    if lux >= MAX:
      return 0
    elif lux < MIN:
      return 100
    else:
      saturation = int(math.ceil((MAX - lux) / ((MAX - MIN) / (100 / STEP - 1)))) * STEP
      return saturation

  def calculate_kelvin(self, saturation):
    kelvin = 2000 + saturation * ((6500 - 2000) / 100)
    return kelvin


  def process(self, kwargs):
    new_saturation = self.calculate_saturation()
    if not new_saturation:
      # use circadian sensor
      return
    kelvin = self.calculate_kelvin(new_saturation)
    old_saturation = self.get_old_saturation()
    if self.get_state("light.ha_group_all") == "on":
      if abs(new_saturation - old_saturation) > STEP:
        if new_saturation > old_saturation:
          new_saturation = old_saturation + STEP
        elif new_saturation < old_saturation:
          new_saturation = old_saturation - STEP
    if new_saturation != old_saturation:
      self.set_saturation(new_saturation, kelvin)


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
