from base import Base


class Table(Base):

  def initialize(self):
    super().initialize()
    self.handle = None
    self.turned_off_ts = 0
    self.listen_state(self.on_power_change, "sensor.bedroom_table_plug_power")
    self.listen_event(self.on_fake_light_on, "turn_on_bedroom_table_switch")
    self.listen_event(self.on_fake_light_off, "turn_off_bedroom_table_switch")
    self.listen_state(self.on_switch_off, "switch.bedroom_table_plug", new="off", old="on")
    self.listen_state(self.on_light_change, "input_boolean.bedroom_table_lamp")


  def on_power_change(self, entity, attribute, old, new, kwargs):
    if self.is_invalid(new):
      return
    entity = "input_boolean.bedroom_table_lamp"
    if float(new) > 9 and self.get_delta_ts(self.turned_off_ts) > 3:
      if self.entity_is_off(entity):
        self.turn_on_entity(entity)
    else:
      if self.entity_is_on(entity):
        self.turn_off_entity(entity)


  def on_light_change(self, entity, attribute, old, new, kwargs):
    if new == "on":
      self.turn_on_entity("light.ha_template_individual_bedroom_table")
    else:
      self.turn_off_entity("light.ha_template_individual_bedroom_table")


  def on_fake_light_on(self, event_name, data, kwargs):
    self.turn_on_entity("switch.bedroom_table_plug")


  def on_fake_light_off(self, event_name, data, kwargs):
    self.turned_off_ts = self.get_now_ts()
    if self.entity_is_on("light.bedroom_table"):
      self.turn_off_entity("input_boolean.bedroom_table_lamp")
      self.turn_off_entity("light.ha_template_individual_bedroom_table")
      self.turn_off_entity("switch.bedroom_table_plug")


  def on_switch_off(self, entity, attribute, old, new, kwargs):
    self.cancel_handle(self.handle)
    self.handle = self.run_in(self.turn_on_switch, 3)


  def turn_on_switch(self, kwargs):
    self.turn_on_entity("switch.bedroom_table_plug")
