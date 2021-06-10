import appdaemon.plugins.hass.hassapi as hass


class WashingMachine(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    self.last_changed = 0
    self.listen_state(self.on_median_power_change, "sensor.washing_machine_plug_median_power")
    self.listen_state(self.on_power_change, "sensor.bathroom_washing_machine_plug_power")
    self.listen_state(self.on_max_power_change, "sensor.washing_machine_plug_max_power")
    self.listen_state(self.on_door_change, "binary_sensor.bathroom_washing_machine_door")
    self.listen_state(self.on_action, "input_select.washing_machine_status", new="full")
    self.listen_state(self.on_action, "input_select.sleeping_scene")
    self.listen_state(self.on_action, "input_select.living_scene")
    for person_name in self.persons.get_all_person_names():
      entity = f"input_select.{person_name}_location"
      if not self.entity_exists(entity):
        continue
      self.listen_state(self.on_action, entity, new="home")
    self.run_every(self.action, "now", 600)


  def on_power_change(self, entity, attribute, old, new, kwargs):
    try:
      power_int = int(float(new))
    except (TypeError, ValueError):
      return
    delta = self.get_now_ts() - self.last_changed
    if power_int > 100 and self.get_state("input_select.washing_machine_status") == "empty" and delta >= 120:
      self.last_changed = self.get_now_ts()
      self.call_service("input_select/select_option", entity_id="input_select.washing_machine_status", option="washing")


  def on_max_power_change(self, entity, attribute, old, new, kwargs):
    try:
      power_int = int(float(new))
    except (TypeError, ValueError):
      return
    delta = self.get_now_ts() - self.last_changed
    if power_int > 80 and self.get_state("input_select.washing_machine_status") == "full" and delta >= 120:
      self.last_changed = self.get_now_ts()
      self.call_service("input_select/select_option", entity_id="input_select.washing_machine_status", option="washing")


  def on_median_power_change(self, entity, attribute, old, new, kwargs):
    try:
      power_int = int(float(new))
    except (TypeError, ValueError):
      return
    delta = self.get_now_ts() - self.last_changed
    if power_int < 10 and self.get_state("input_select.washing_machine_status") == "washing" and delta >= 120:
      self.last_changed = self.get_now_ts()
      self.call_service("input_select/select_option", entity_id="input_select.washing_machine_status", option="full")


  def on_door_change(self, entity, attribute, old, new, kwargs):
    if new == "on" and self.get_state("input_select.washing_machine_status") != "empty":
      self.log("Setting Empty state")
      self.call_service("input_select/select_option", entity_id="input_select.washing_machine_status", option="empty")


  def on_action(self, entity, attribute, old, new, kwargs):
    self.action({})


  def notify_on_full(self):
    is_not_sleeping = self.get_state("input_select.sleeping_scene") != "night"
    is_not_away = self.get_state("input_select.living_scene") != "away"
    if is_not_sleeping and is_not_away:
      self.persons.send_notification("home_or_none", "👖 Clothes are done", "washing_machine",
                                     sound="Bloom.caf", min_delta=3600)


  def action(self, kwargs):
    if self.get_state("input_select.washing_machine_status") == "full":
      self.notify_on_full()
