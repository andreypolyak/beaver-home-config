from base import Base


class AC(Base):

  def initialize(self):
    super().initialize()
    self.handle = None
    self.handle_ts = 0
    self.check_handle = None
    self.turn_off_handle = None
    self.listen_state(self.on_change, "input_select.living_scene", immediate=True)
    self.listen_state(self.on_change, "binary_sensor.living_room_balcony_door")
    self.listen_state(self.on_change, "sensor.balcony_temperature")
    self.listen_state(self.on_change, "sensor.living_room_temperature")
    self.listen_state(self.on_change, "sensor.living_room_humidity")
    self.listen_state(self.on_change, "timer.ac_turn_off_disabled")
    self.listen_state(self.on_change, "timer.ac_turn_on_disabled")
    self.listen_event(self.on_manual_toggle, "manual_ac_toggle")
    self.listen_event(self.on_manual_on, "manual_ac_on")
    self.listen_event(self.on_manual_off, "manual_ac_off")


  def on_change(self, entity, attribute, old, new, kwargs):
    self.debounce({})


  def debounce(self, kwargs):
    if self.get_delta_ts(self.handle_ts) > 5:
      self.handle_ts = self.get_now_ts()
      self.cancel_handle(self.handle)
      self.change()
    else:
      self.cancel_handle(self.handle)
      self.handle = self.run_in(self.debounce, 5)


  def change(self):
    living_room_temperature = self.get_float_state("sensor.living_room_temperature")
    living_room_humidity = self.get_float_state("sensor.living_room_humidity")
    balcony_temperature = self.get_float_state("sensor.balcony_temperature")
    if living_room_temperature is None or living_room_humidity is None or balcony_temperature is None:
      return

    ac_turn_off_disabled = self.timer_is_active("ac_turn_off_disabled")
    ac_turn_on_disabled = self.timer_is_active("ac_turn_on_disabled")

    new_ac_state = False
    change_reason = ""

    if living_room_temperature >= 26 and balcony_temperature >= 15:
      change_reason = "living_room_temperature >= 26 and balcony_temperature >= 15"
      new_ac_state = True
    elif living_room_temperature >= 25 and balcony_temperature >= 25 and living_room_humidity < 60:
      change_reason = "living_room_temperature >= 25 and balcony_temperature >= 25 and living_room_humidity < 60"
      new_ac_state = True
    elif living_room_temperature >= 27 and balcony_temperature >= 20 and living_room_humidity < 60:
      change_reason = "living_room_temperature >= 27 and balcony_temperature >= 20 and living_room_humidity < 60"
      new_ac_state = True
    elif living_room_temperature >= 24 and balcony_temperature >= 25 and living_room_humidity >= 60:
      change_reason = "living_room_temperature >= 24 and balcony_temperature >= 25 and living_room_humidity >= 60"
      new_ac_state = True
    elif living_room_temperature >= 26 and balcony_temperature >= 20 and living_room_humidity >= 60:
      change_reason = "living_room_temperature >= 26 and balcony_temperature >= 20 and living_room_humidity >= 60"
      new_ac_state = True
    elif living_room_temperature < 21 and balcony_temperature >= 25 and living_room_humidity < 60:
      change_reason = "living_room_temperature < 21 and balcony_temperature >= 25 and living_room_humidity < 60"
      new_ac_state = False
    elif living_room_temperature < 23 and balcony_temperature >= 15 and living_room_humidity < 60:
      change_reason = "living_room_temperature < 23 and balcony_temperature >= 20 and living_room_humidity < 60"
      new_ac_state = False
    elif living_room_temperature < 20 and balcony_temperature >= 25 and living_room_humidity >= 60:
      change_reason = "living_room_temperature < 20 and balcony_temperature >= 25 and living_room_humidity >= 60"
      new_ac_state = False
    elif living_room_temperature < 22 and balcony_temperature >= 15 and living_room_humidity >= 60:
      change_reason = "living_room_temperature < 22 and balcony_temperature >= 20 and living_room_humidity >= 60"
      new_ac_state = False

    if balcony_temperature < 15:
      change_reason = "balcony_temperature < 15"
      new_ac_state = False

    if self.living_scene == "away":
      change_reason = "away scene"
      new_ac_state = False

    if ac_turn_off_disabled:
      change_reason = "AC was manually turned on"
      new_ac_state = True

    if ac_turn_on_disabled:
      change_reason = "AC was manually turned off"
      new_ac_state = False

    if self.entity_is_on("binary_sensor.living_room_balcony_door"):
      change_reason = "balcony door is open"
      new_ac_state = False

    if new_ac_state and self.entity_is_off("binary_sensor.living_room_ac_door"):
      self.cancel_handle(self.turn_off_handle)
      self.log(f"AC was turned on because: {change_reason}")
      self.turn_on_ac()
    elif not new_ac_state and self.entity_is_on("binary_sensor.living_room_ac_door"):
      self.log(f"AC will be turned off because: {change_reason}")
      if not self.timer_running(self.turn_off_handle):
        self.turn_off_handle = self.run_in(self.turn_off_ac, 15)


  def on_manual_toggle(self, event_name, data, kwargs):
    if self.entity_is_on("binary_sensor.living_room_ac_door"):
      self.manual_off()
    else:
      self.manual_on()


  def on_manual_on(self, event_name, data, kwargs):
    self.manual_on()


  def on_manual_off(self, event_name, data, kwargs):
    self.manual_off()


  def manual_on(self):
    self.timer_cancel("ac_turn_on_disabled")
    self.timer_start("ac_turn_off_disabled", 1800)


  def manual_off(self):
    self.timer_cancel("ac_turn_off_disabled")
    self.timer_start("ac_turn_on_disabled", 1800)


  def turn_on_ac(self):
    self.turn_on_entity("script.ac_turn_on")
    self.cancel_handle(self.check_handle)
    self.check_handle = self.run_in(self.check_state, 10, expected_state=True)


  def turn_off_ac(self, kwargs):
    self.log("Turning off AC")
    self.turn_on_entity("script.ac_turn_off")
    self.cancel_handle(self.check_handle)
    self.check_handle = self.run_in(self.check_state, 10, expected_state=False)


  def check_state(self, kwargs):
    expected_state = kwargs["expected_state"]
    self.cancel_handle(self.check_handle)
    if expected_state and self.entity_is_off("binary_sensor.living_room_ac_door"):
      self.log("Turn on AC one more time")
      self.turn_on_entity("script.ac_turn_on")
    elif not expected_state and self.entity_is_on("binary_sensor.living_room_ac_door"):
      self.log("Turn off AC one more time")
      self.turn_on_entity("script.ac_turn_off")
