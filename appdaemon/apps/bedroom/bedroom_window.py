from room_window import RoomWindow


class BedroomWindow(RoomWindow):

  def initialize(self):
    self.room = "bedroom"
    self.zone = "sleeping"
    self.co2_sensor = "sensor.bedroom_co2"
    self.temperature_sensor = "sensor.bedroom_temperature"
    self.balcony_temperature_sensor = "sensor.balcony_temperature"
    self.action_sensors = []
    self.occupancy_sensors = ["binary_sensor.bedroom_chair_occupancy"]
    self.room_init()


  def calculate_position(self):
    co2 = self.get_int_state(self.co2_sensor)
    temperature = self.get_float_state(self.temperature_sensor)
    balcony_temperature = self.get_float_state(self.balcony_temperature_sensor)
    if co2 is None or temperature is None or balcony_temperature is None:
      return (None, None)
    person_sitting_near = self.is_person_sitting_near()
    is_alarm_soon = self.is_alarm_soon()

    position = 100
    reason = "default state"

    if balcony_temperature < 15:
      reason = f"outside_temperature < 15, co2 = {co2}"
      if co2 > 1000:
        position = 100
      elif co2 < 400:
        position = 20
      else:
        position = round((co2 - 400) * 0.133) + 20

    if person_sitting_near and balcony_temperature < 5:
      position -= 10
      reason += ", person_sitting_near"

    if balcony_temperature < -5:
      position -= 30
      reason += ", outside_temperature < -5"
    elif balcony_temperature < 0:
      position -= 20
      reason += ", outside_temperature < 0"
    elif balcony_temperature < 5:
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
      and self.get_sleeping_scene() == "day"
      and self.is_entity_off(f"light.ha_group_{self.room}")
      and balcony_temperature > -5
    ):
      position += 40
      reason += ", preparation for night"

    if self.get_sleeping_scene() == "night" and balcony_temperature > -5:
      position += 20
      reason += ", sleeping_scene = night"
      if is_alarm_soon:
        position = 100
        reason = "alarm soon"

    return (position, reason)


  def is_alarm_soon(self):
    for person_name in self.get_all_person_names(with_alarm=True):
      if self.is_entity_off(f"input_boolean.alarm_{person_name}"):
        continue
      alarm_time = self.parse_datetime(self.get_state(f"input_datetime.alarm_{person_name}"), aware=True)
      current_time = self.get_now()
      if (alarm_time - current_time).seconds < 1800:
        return True
    return False
