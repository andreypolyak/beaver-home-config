from room_window import RoomWindow
from datetime import datetime


class BedroomWindow(RoomWindow):

  def initialize(self):
    self.room = "bedroom"
    self.zone = "sleeping"
    self.co2_sensor = "sensor.bedroom_co2"
    self.temperature_sensor = "sensor.bedroom_temperature"
    self.action_sensors = []
    self.occupancy_sensors = ["binary_sensor.bedroom_chair_occupancy"]
    self.room_init()


  def calculate_position(self):
    try:
      co2 = int(float(self.get_state(self.co2_sensor)))
      temperature = float(self.get_state(self.temperature_sensor))
      outside_temperature = float(self.get_state("sensor.balcony_temperature"))
      person_sitting_near = self.is_person_sitting_near()
      sleeping_scene = self.get_state("input_select.sleeping_scene")
      is_alarm_soon = self.is_alarm_soon()
      lights_off = self.get_state(f"light.ha_group_{self.room}") == "off"

      position = 100
      reason = "default state"

      if outside_temperature < 15:
        reason = f"outside_temperature < 15, co2 = {co2}"
        if co2 > 1000:
          position = 100
        elif co2 < 400:
          position = 20
        else:
          position = round((co2 - 400) * 0.133) + 20

      if person_sitting_near and outside_temperature < 5:
        position -= 10
        reason += ", person_sitting_near"

      if outside_temperature < -5:
        position -= 30
        reason += ", outside_temperature < -5"
      elif outside_temperature < 0:
        position -= 20
        reason += ", outside_temperature < 0"
      elif outside_temperature < 5:
        position -= 10
        reason += ", outside_temperature < 5"

      if temperature >= 25:
        position += 20
        reason += ", temperature >= 25"
      elif temperature >= 26:
        position += 40
        reason += ", temperature >= 26"
      elif temperature < 22:
        position -= 10
        reason += ", temperature < 22"

      if (
        self.now_is_between("20:00:00", "04:00:00")
        and sleeping_scene == "day"
        and lights_off
        and outside_temperature > -5
      ):
        position += 40
        reason += ", preparation for night"

      if sleeping_scene == "night" and outside_temperature > -5:
        position += 20
        reason += ", sleeping_scene = night"
        if is_alarm_soon:
          position = 100
          reason = "alarm soon"

      return (position, reason)
    except (ValueError, TypeError):
      return (None, None)


  def is_alarm_soon(self):
    for person_name in self.persons.get_all_person_names(with_alarm=True):
      if self.get_state(f"input_boolean.alarm_{person_name}") == "on":
        alarm_time = self.parse_time(self.get_state(f"input_datetime.alarm_{person_name}"))
        alarm_time_minutes = alarm_time.hour * 60 + alarm_time.minute
        current_time = datetime.now()
        current_time_minutes = current_time.hour * 60 + current_time.minute
        current_time_alarm_time_diff = alarm_time_minutes - current_time_minutes
        if (1 <= current_time_alarm_time_diff <= 30) or (-1439 <= current_time_alarm_time_diff <= -1410):
          return True
    return False
