from base import Base


class Coffee(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_start_coffee, "switch.kitchen_coffee_plug", new="on")
    self.listen_state(self.on_finish_coffee, "switch.kitchen_coffee_plug", new="off")
    self.listen_state(self.on_all_away, "input_select.living_scene", new="away")
    self.listen_state(self.on_lid_open, "binary_sensor.kitchen_coffee_door", new="on", old="off")
    self.listen_state(self.on_lid_close, "binary_sensor.kitchen_coffee_door", new="off", old="on")
    self.listen_state(self.on_alarm_ringing, "input_boolean.alarm_ringing", new="on", old="off")
    self.listen_event(self.on_timer_finished, "timer.finished", entity_id="timer.coffee")


  def on_start_coffee(self, entity, attribute, old, new, kwargs):
    self.log("Coffee was turned on")
    self.turn_off_entity("input_boolean.coffee_prepared")
    self.timer_start("coffee", 7200)


  def on_finish_coffee(self, entity, attribute, old, new, kwargs):
    self.log("Coffee was turned off")
    self.timer_cancel("coffee")


  def on_all_away(self, entity, attribute, old, new, kwargs):
    self.timer_cancel("coffee")
    if self.is_entity_on("switch.kitchen_coffee_plug"):
      self.log("Turning off coffee because everyone left")
      self.turn_off_entity("switch.kitchen_coffee_plug")


  def on_lid_open(self, entity, attribute, old, new, kwargs):
    if self.is_entity_on("switch.kitchen_coffee_plug"):
      self.log("Turning off coffee because lid was opened")
      self.timer_cancel("coffee")
      self.turn_off_entity("switch.kitchen_coffee_plug")


  def on_lid_close(self, entity, attribute, old, new, kwargs):
    turned_on_ts = int(self.get_state("input_datetime.coffee_turned_on", attribute="timestamp"))
    if self.now_is_between("16:00:00", "04:00:00"):
      self.turn_on_entity("input_boolean.coffee_prepared")
    elif self.now_is_between("04:00:00", "13:00:00") and self.get_delta_ts(turned_on_ts) > 43200:
      self.turn_on_coffee()


  def on_alarm_ringing(self, entity, attribute, old, new, kwargs):
    is_coffee_prepared = self.is_entity_on("input_boolean.coffee_prepared")
    is_lid_closed = self.is_entity_off("binary_sensor.kitchen_coffee_door")
    if is_coffee_prepared and is_lid_closed:
      self.turn_on_coffee()


  def on_timer_finished(self, event_name, data, kwargs):
    self.log("Turning off coffee by timer")
    self.turn_off_entity("switch.kitchen_coffee_plug")


  def turn_on_coffee(self):
    self.log("Turning on coffee")
    self.set_current_datetime("input_datetime.coffee_turned_on")
    self.turn_on_entity("switch.kitchen_coffee_plug")
