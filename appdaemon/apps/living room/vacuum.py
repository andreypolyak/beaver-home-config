import appdaemon.plugins.hass.hassapi as hass


class Vacuum(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    for entity in self.persons.get_all_person_location_entities():
      self.listen_state(self.on_person_change, entity)
    self.listen_state(self.on_vacuum_docked, "vacuum.rockrobo", new="docked")
    self.listen_state(self.on_vacuum_error, "vacuum.rockrobo", new="error")
    self.listen_state(self.on_vacuum_idle, "vacuum.rockrobo", new="idle")
    self.listen_state(self.on_vacuum_returning, "vacuum.rockrobo", new="returning")
    self.listen_state(self.on_vacuum_change, "vacuum.rockrobo")
    self.listen_state(self.on_manual_start, "script.vacuum_clean_all", new="on")
    self.listen_event(self.on_timer_finished, "timer.finished", entity_id="timer.vacuum_no_clean")


  def on_timer_finished(self, event_name, data, kwargs):
    self.call_service("input_boolean/turn_on", entity_id="input_boolean.vacuum_auto_clean")


  def on_person_change(self, entity, attribute, old, new, kwargs):
    autoclean_state = self.get_vacuum_auto_clean_state()
    if autoclean_state == "done_charging" and new in ["downstairs", "home"]:
      self.go_to_bin()
    all_persons_not_home = not self.persons.are_all_persons_inside_location("district")
    timestamp = int(self.get_state("input_datetime.vacuum_last_cleaned", attribute="timestamp"))
    day = int(self.get_state("input_datetime.vacuum_last_cleaned", attribute="day"))

    if (
        all_persons_not_home
        and self.get_state("input_select.living_scene") == "away"
        and self.get_state("vacuum.rockrobo") == "docked"
        and (self.get_now_ts() - timestamp > (6 * 60 * 60))
        and (day != int(self.datetime().strftime("%d")))
        and self.get_vacuum_auto_clean_state() == "idle"
    ):
      if self.get_state("input_boolean.vacuum_auto_clean") == "off":
        self.call_service("timer/start", entity_id="timer.vacuum_no_clean", duration=3600)
        self.log("Vacuum auto clean is turned off")
        return
      if self.get_state("timer.vacuum_no_clean") == "active":
        self.log("Vacuum no clean timer is active")
        return
      self.log("Starting automatical vacuum cleaning")
      self.call_service("script/turn_on", entity_id="script.vacuum_clean_all")
      self.start_vacuum()


  def start_vacuum(self):
    self.call_service("input_select/select_option", entity_id="input_select.vacuum_room_cleaning", option="all")
    self.set_vacuum_auto_clean_state("cleaning")


  def on_manual_start(self, entity, attribute, old, new, kwargs):
    self.log("Manual vacuum cleaning started")
    self.start_vacuum()


  def on_vacuum_returning(self, entity, attribute, old, new, kwargs):
    if self.get_vacuum_auto_clean_state() == "cleaning" and self.persons.is_anyone_home():
      self.log("Vacuum cleaning finished")
      self.set_vacuum_last_cleaned_ts()
      self.set_vacuum_auto_clean_state("done_charging")
      self.go_to_bin()


  def on_vacuum_error(self, entity, attribute, old, new, kwargs):
    if self.get_vacuum_auto_clean_state() == "cleaning":
      self.log("Vacuum cleaning ended with error")
      self.set_vacuum_auto_clean_state("error")
      self.set_vacuum_last_cleaned_ts()


  def on_vacuum_idle(self, entity, attribute, old, new, kwargs):
    if self.get_vacuum_auto_clean_state() == "cleaning":
      self.log("Vacuum hanged up")
      self.set_vacuum_auto_clean_state("error")
      self.set_vacuum_last_cleaned_ts()


  def on_vacuum_docked(self, entity, attribute, old, new, kwargs):
    if self.get_vacuum_auto_clean_state() == "cleaning":
      self.log("Vacuum cleaning finished")
      self.set_vacuum_last_cleaned_ts()
      self.set_vacuum_auto_clean_state("done_charging")
      if self.persons.is_anyone_home():
        self.go_to_bin()
    else:
      self.set_vacuum_auto_clean_state("idle")


  def on_vacuum_change(self, entity, attribute, old, new, kwargs):
    if new != "cleaning" and old == "cleaning":
      self.call_service("input_select/select_option", entity_id="input_select.vacuum_room_cleaning", option="none")


  def go_to_bin(self):
    self.log("Vacuum is moving to bin")
    self.call_service("script/turn_on", entity_id="script.vacuum_go_to_bin")
    self.set_vacuum_auto_clean_state("done_waiting")


  def set_vacuum_last_cleaned_ts(self):
    self.call_service("input_datetime/set_datetime", entity_id="input_datetime.vacuum_last_cleaned",
                      timestamp=self.get_now_ts())


  def set_vacuum_auto_clean_state(self, state):
    self.call_service("input_select/select_option", entity_id="input_select.vacuum_autoclean_state", option=state)


  def get_vacuum_auto_clean_state(self):
    return self.get_state("input_select.vacuum_autoclean_state")
