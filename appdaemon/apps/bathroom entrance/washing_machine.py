from base import Base


class WashingMachine(Base):

  def initialize(self):
    super().initialize()
    self.last_changed = 0
    self.listen_state(self.on_median_power_change, "sensor.washing_machine_plug_median_power")
    self.listen_state(self.on_power_change, "sensor.bathroom_washing_machine_plug_power")
    self.listen_state(self.on_max_power_change, "sensor.washing_machine_plug_max_power")
    self.listen_state(self.on_door_change, "binary_sensor.bathroom_washing_machine_door")
    self.listen_state(self.on_action, "input_select.washing_machine_status", new="full")
    self.listen_state(self.on_action, "input_select.sleeping_scene")
    self.listen_state(self.on_action, "input_select.living_scene")
    for entity in self.get_all_person_location_entities():
      self.listen_state(self.on_action, entity, new="home")
    self.run_every(self.action, "now", 600)


  def on_power_change(self, entity, attribute, old, new, kwargs):
    power_int = self.get_float_state(new)
    if power_int is None:
      return
    if power_int > 100 and self.get_status() == "empty" and self.get_delta_ts(self.last_changed) >= 120:
      self.last_changed = self.get_now_ts()
      self.set_status("washing")


  def on_max_power_change(self, entity, attribute, old, new, kwargs):
    power_int = self.get_float_state(new)
    if power_int is None:
      return
    if power_int > 80 and self.get_status() == "full" and self.get_delta_ts(self.last_changed) >= 120:
      self.last_changed = self.get_now_ts()
      self.set_status("washing")


  def on_median_power_change(self, entity, attribute, old, new, kwargs):
    power_int = self.get_float_state(new)
    if power_int is None:
      return
    if power_int < 10 and self.get_status() == "washing" and self.get_delta_ts(self.last_changed) >= 120:
      self.last_changed = self.get_now_ts()
      self.set_status("full")


  def on_door_change(self, entity, attribute, old, new, kwargs):
    if new == "on" and self.get_status() != "empty":
      self.log("Setting Empty state")
      self.set_status("empty")


  def on_action(self, entity, attribute, old, new, kwargs):
    self.action({})


  def notify_on_full(self):
    is_not_sleeping = self.get_state("input_select.sleeping_scene") != "night"
    is_not_away = self.get_state("input_select.living_scene") != "away"
    if is_not_sleeping and is_not_away:
      message = "👖 Clothes are done"
      self.send_push("home_or_none", message, "washing_machine", sound="Bloom.caf", min_delta=3600)


  def action(self, kwargs):
    if self.get_status() == "full":
      self.notify_on_full()


  def get_status(self):
    self.get_state("input_select.washing_machine_status")


  def set_status(self, status):
    self.select_option("washing_machine_status", status)
