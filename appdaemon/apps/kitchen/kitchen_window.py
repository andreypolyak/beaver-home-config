from room_window import RoomWindow


class KitchenWindow(RoomWindow):

  def initialize(self):
    self.room = "kitchen"
    self.zone = "living"
    self.co2_sensor = "sensor.living_room_co2"
    self.temperature_sensor = "sensor.kitchen_temperature"
    self.action_sensors = ["binary_sensor.kitchen_vent"]
    self.occupancy_sensors = ["binary_sensor.kitchen_chair_1_occupancy", "binary_sensor.kitchen_chair_2_occupancy"]
    self.room_init()


  def calculate_position(self):
    try:
      co2 = int(float(self.get_state(self.co2_sensor)))
      temperature = float(self.get_state(self.temperature_sensor))
      outside_temperature = float(self.get_state("sensor.balcony_temperature"))
      person_sitting_near = self.is_person_sitting_near()
      is_vent_on = self.get_state("binary_sensor.kitchen_vent") == "on"

      scene_last_changed_str = self.get_state("input_boolean.scene_living_night", attribute="last_changed")
      scene_last_changed = self.convert_utc(scene_last_changed_str).timestamp()
      night_diff = self.get_now_ts() - scene_last_changed
      living_scene = self.get_state("input_select.living_scene")


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

      if is_vent_on:
        position += 40
        reason += ", vent on"

      if night_diff < 3600 and living_scene == "day" and outside_temperature < 5 and person_sitting_near:
        position = 0
        reason = "person_sitting_near after night"

      return (position, reason)
    except (ValueError, TypeError):
      return (None, None)
