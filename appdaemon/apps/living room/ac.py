import appdaemon.plugins.hass.hassapi as hass


class AC(hass.Hass):

  def initialize(self):
    self.handle = None
    self.handle_ts = 0
    self.check_handle = None
    self.listen_state(self.on_change, "input_select.nearest_person_location", immediate=True)
    self.listen_state(self.on_change, "binary_sensor.living_room_balcony_door")
    self.listen_state(self.on_change, "sensor.balcony_temperature")
    self.listen_state(self.on_change, "sensor.living_room_temperature")
    self.listen_state(self.on_change, "sensor.living_room_humidity")
    self.listen_state(self.on_change, "timer.ac_no_auto_off")
    self.listen_state(self.on_change, "timer.ac_no_auto_on")
    self.listen_event(self.on_manual_toggle, "custom_event", custom_event_data="manual_ac_toggle")
    self.listen_event(self.on_manual_on, "custom_event", custom_event_data="manual_ac_on")
    self.listen_event(self.on_manual_off, "custom_event", custom_event_data="manual_ac_off")


  def on_change(self, entity, attribute, old, new, kwargs):
    self.debounce({})


  def debounce(self, kwargs):
    current_ts = self.get_now_ts()
    if (current_ts - self.handle_ts) > 5:
      self.handle_ts = current_ts
      if self.timer_running(self.handle):
        self.cancel_timer(self.handle)
      self.change()
    else:
      if self.timer_running(self.handle):
        self.cancel_timer(self.handle)
      self.handle = self.run_in(self.debounce, 5)


  def change(self):
    try:
      is_ac_on = self.get_state("binary_sensor.living_room_ac_door") == "on"
      is_ac_off = self.get_state("binary_sensor.living_room_ac_door") == "off"
      is_balcony_open = self.get_state("binary_sensor.living_room_balcony_door") == "on"
      nearest_person_location = self.get_state("input_select.nearest_person_location")
      living_room_temperature = float(self.get_state("sensor.living_room_temperature"))
      living_room_humidity = float(self.get_state("sensor.living_room_humidity"))
      balcony_temperature = float(self.get_state("sensor.balcony_temperature"))
      is_no_off_timer_on = self.get_state("timer.ac_no_auto_off") == "active"
      is_no_on_timer_on = self.get_state("timer.ac_no_auto_on") == "active"

      new_ac_state = None
      change_reason = ""

      if living_room_temperature >= 26 and balcony_temperature >= 15:
        change_reason = "living_room_temperature >= 26 and balcony_temperature >= 15"
        new_ac_state = True
      elif living_room_temperature >= 23 and balcony_temperature >= 25 and living_room_humidity < 60:
        change_reason = "living_room_temperature >= 23 and balcony_temperature >= 25 and living_room_humidity < 60"
        new_ac_state = True
      elif living_room_temperature >= 25 and balcony_temperature >= 20 and living_room_humidity < 60:
        change_reason = "living_room_temperature >= 25 and balcony_temperature >= 20 and living_room_humidity < 60"
        new_ac_state = True
      elif living_room_temperature >= 22 and balcony_temperature >= 25 and living_room_humidity >= 60:
        change_reason = "living_room_temperature >= 22 and balcony_temperature >= 25 and living_room_humidity >= 60"
        new_ac_state = True
      elif living_room_temperature >= 24 and balcony_temperature >= 20 and living_room_humidity >= 60:
        change_reason = "living_room_temperature >= 24 and balcony_temperature >= 20 and living_room_humidity >= 60"
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

      if nearest_person_location == "not_home":
        change_reason = "no people at home"
        new_ac_state = False

      if is_no_off_timer_on:
        change_reason = "AC was manually turned on"
        new_ac_state = True

      if is_no_on_timer_on:
        change_reason = "AC was manually turned off"
        new_ac_state = False

      if is_balcony_open:
        change_reason = "balcony door is open"
        new_ac_state = False

      if new_ac_state is True and is_ac_off:
        self.log(f"AC was turned on because: {change_reason}")
        self.turn_on_ac()
      elif new_ac_state is False and is_ac_on:
        self.log(f"AC was turned off because: {change_reason}")
        self.turn_off_ac()
    except ValueError:
      pass


  def on_manual_toggle(self, event_name, data, kwargs):
    is_ac_on = self.get_state("binary_sensor.living_room_ac_door") == "on"
    if is_ac_on:
      self.manual_off()
    else:
      self.manual_on()


  def on_manual_on(self, event_name, data, kwargs):
    self.manual_on()


  def on_manual_off(self, event_name, data, kwargs):
    self.manual_off()


  def manual_on(self):
    self.call_service("timer/cancel", entity_id="timer.ac_no_auto_on")
    self.call_service("timer/start", entity_id="timer.ac_no_auto_off", duration=1800)


  def manual_off(self):
    self.call_service("timer/cancel", entity_id="timer.ac_no_auto_off")
    self.call_service("timer/start", entity_id="timer.ac_no_auto_on", duration=3600)


  def turn_on_ac(self):
    self.call_service("script/turn_on", entity_id="script.ac_turn_on")
    if self.timer_running(self.check_handle):
      self.cancel_timer(self.check_handle)
    self.check_handle = self.run_in(self.check_state, 10, is_on=True)


  def turn_off_ac(self):
    self.call_service("script/turn_on", entity_id="script.ac_turn_off")
    if self.timer_running(self.check_handle):
      self.cancel_timer(self.check_handle)
    self.check_handle = self.run_in(self.check_state, 10, is_on=False)


  def check_state(self, kwargs):
    is_ac_on = self.get_state("binary_sensor.living_room_ac_door") == "on"
    if self.timer_running(self.check_handle):
      self.cancel_timer(self.check_handle)
    if "is_on" in kwargs and kwargs["is_on"] and not is_ac_on:
      self.log("AC turned on (fix)")
      self.call_service("script/turn_on", entity_id="script.ac_turn_on")
    elif "is_on" in kwargs and not kwargs["is_on"] and is_ac_on:
      self.log("AC turned off (fix)")
      self.call_service("script/turn_on", entity_id="script.ac_turn_off")
