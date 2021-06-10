import appdaemon.plugins.hass.hassapi as hass


class Coffee(hass.Hass):

  def initialize(self):
    self.listen_state(self.on_start_coffee, "switch.kitchen_coffee_plug", new="on")
    self.listen_state(self.on_finish_coffee, "switch.kitchen_coffee_plug", new="off")
    self.listen_state(self.on_all_away, "input_select.living_scene", new="away")
    self.listen_state(self.on_lid_open, "binary_sensor.kitchen_coffee_door", new="on", old="off")
    self.listen_state(self.on_lid_close, "binary_sensor.kitchen_coffee_door", new="off", old="on")
    self.listen_state(self.on_alarm_ringing, "input_boolean.alarm_ringing", new="on", old="off")
    self.listen_event(self.on_timer_finished, "timer.finished", entity_id="timer.coffee")


  def on_start_coffee(self, entity, attribute, old, new, kwargs):
    self.log("Coffee was turned on")
    self.call_service("input_boolean/turn_off", entity_id="input_boolean.coffee_prepared")
    self.call_service("timer/start", entity_id="timer.coffee", duration=7200)


  def on_finish_coffee(self, entity, attribute, old, new, kwargs):
    self.log("Coffee was turned off")
    self.call_service("timer/cancel", entity_id="timer.coffee")


  def on_all_away(self, entity, attribute, old, new, kwargs):
    self.call_service("timer/cancel", entity_id="timer.coffee")
    if self.get_state("switch.kitchen_coffee_plug") == "on":
      self.log("Turning off coffee because everyone left")
      self.call_service("switch/turn_off", entity_id="switch.kitchen_coffee_plug")


  def on_lid_open(self, entity, attribute, old, new, kwargs):
    if self.get_state("switch.kitchen_coffee_plug") == "on":
      self.log("Turning off coffee because lid was opened")
      self.call_service("timer/cancel", entity_id="timer.coffee")
      self.call_service("switch/turn_off", entity_id="switch.kitchen_coffee_plug")


  def on_lid_close(self, entity, attribute, old, new, kwargs):
    turned_on_ts = int(self.get_state("input_datetime.coffee_turned_on", attribute="timestamp"))
    if self.now_is_between("16:00:00", "04:00:00"):
      self.call_service("input_boolean/turn_on", entity_id="input_boolean.coffee_prepared")
    elif self.now_is_between("04:00:00", "13:00:00"):
      if (self.get_now_ts() - turned_on_ts) > (12 * 60 * 60):
        self.turn_on_coffee()


  def on_alarm_ringing(self, entity, attribute, old, new, kwargs):
    is_coffee_prepared = self.get_state("input_boolean.coffee_prepared") == "on"
    is_lid_closed = self.get_state("binary_sensor.kitchen_coffee_door") == "off"
    if is_coffee_prepared and is_lid_closed:
      self.turn_on_coffee()


  def on_timer_finished(self, event_name, data, kwargs):
    self.log("Turning off coffee by timer")
    self.call_service("switch/turn_off", entity_id="switch.kitchen_coffee_plug")


  def turn_on_coffee(self):
    self.log("Turning on coffee")
    self.call_service("input_datetime/set_datetime", entity_id="input_datetime.coffee_turned_on",
                      timestamp=self.get_now_ts())
    self.call_service("switch/turn_on", entity_id="switch.kitchen_coffee_plug")
