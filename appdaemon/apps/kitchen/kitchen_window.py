from room_window import RoomWindow


class KitchenWindow(RoomWindow):

  def initialize(self):
    self.room = "kitchen"
    self.zone = "living"
    self.co2_sensor = "sensor.living_room_co2"
    self.temperature_sensor = "sensor.kitchen_temperature"
    self.balcony_temperature_sensor = "sensor.balcony_temperature"
    self.action_sensors = ["binary_sensor.kitchen_vent"]
    self.occupancy_sensors = ["binary_sensor.kitchen_chair_1_occupancy", "binary_sensor.kitchen_chair_2_occupancy"]
    self.room_init()


  def calculate_position(self):
    co2 = self.get_int_state(self.co2_sensor)
    temperature = self.get_float_state(self.temperature_sensor)
    balcony_temperature = self.get_float_state(self.balcony_temperature_sensor)
    if co2 is None or temperature is None or balcony_temperature is None:
      return (None, None)
    scene_last_changed_str = self.get_state("input_boolean.scene_living_night", attribute="last_changed")
    scene_last_changed = self.convert_utc(scene_last_changed_str).timestamp()

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

    if self.person_sitting_near and balcony_temperature < 5:
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

    if self.entity_is_on("binary_sensor.kitchen_vent"):
      position += 40
      reason += ", vent on"

    if (
      self.get_delta_ts(scene_last_changed) < 3600
      and self.living_scene == "day"
      and balcony_temperature < 5
      and self.person_sitting_near
    ):
      position = 0
      reason = "person_sitting_near after night"

    return (position, reason)
