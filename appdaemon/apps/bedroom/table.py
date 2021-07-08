from base import Base


class Table(Base):

  def initialize(self):
    super().initialize()
    self.handle = None
    self.turned_off_ts = 0
    self.listen_state(self.on_table_off, "switch.bedroom_table_plug", new="off", old="on")
    self.listen_event(self.turn_on_switch, "custom_event", custom_event_data="turn_on_bedroom_table_switch")
    self.listen_event(self.turn_off_switch, "custom_event", custom_event_data="turn_off_bedroom_table_switch")
    self.listen_state(self.on_power_change, "sensor.bedroom_table_plug_power")


  def on_power_change(self, entity, attribute, old, new, kwargs):
    if self.is_bad(new):
      return
    if float(new) > 9 and self.get_delta_ts(self.turned_off_ts) > 3:
      self.set_light_state("on")
    else:
      self.set_light_state("off")


  def on_table_off(self, entity, attribute, old, new, kwargs):
    self.cancel_handle(self.handle)
    self.handle = self.run_in(self.turn_on_table, 3)


  def turn_on_table(self, kwargs):
    self.turn_on_entity("switch.bedroom_table_plug")


  def turn_off_switch(self, event_name, data, kwargs):
    self.turned_off_ts = self.get_now_ts()
    if self.is_entity_on("light.bedroom_table"):
      self.set_light_state("off")
      self.turn_off_entity("switch.bedroom_table_plug")


  def turn_on_switch(self, event_name, data, kwargs):
    self.turn_on_entity("switch.bedroom_table_plug")


  def set_light_state(self, state):
    attributes = {"friendly_name": "Bedroom Table", "supported_features": 0}
    self.set_state("light.bedroom_table", state=state, attributes=attributes)
