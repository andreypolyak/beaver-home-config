from base import Base


class Vacuum(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_nearest_person_location_change, "input_select.nearest_person_location")
    self.listen_state(self.on_vacuum_docked, "vacuum.rockrobo", new="docked")
    self.listen_state(self.on_vacuum_error, "vacuum.rockrobo", new="error")
    self.listen_state(self.on_vacuum_idle, "vacuum.rockrobo", new="idle")
    self.listen_state(self.on_vacuum_returning, "vacuum.rockrobo", new="returning")
    self.listen_state(self.on_vacuum_change, "vacuum.rockrobo")
    self.listen_state(self.on_manual_start, "script.vacuum_clean_all", new="on")
    self.listen_event(self.on_timer_finished, "timer.finished", entity_id="timer.vacuum_no_clean")


  def on_timer_finished(self, event_name, data, kwargs):
    self.turn_on_entity("input_boolean.vacuum_auto_clean")


  def on_nearest_person_location_change(self, entity, attribute, old, new, kwargs):
    autoclean_state = self.get_vacuum_auto_clean_state()
    if autoclean_state == "done_charging" and new in ["downstairs", "home"]:
      self.go_to_bin()
    timestamp = self.get_int_state("input_datetime.vacuum_last_cleaned", attribute="timestamp")
    day = self.get_int_state("input_datetime.vacuum_last_cleaned", attribute="day")

    if (
        new == "not_home"
        and self.get_living_scene() == "away"
        and self.get_state("vacuum.rockrobo") == "docked"
        and self.get_delta_ts(timestamp) > 216000
        and day != int(self.datetime().strftime("%d"))
        and self.get_vacuum_auto_clean_state() == "idle"
    ):
      if self.is_entity_off("input_boolean.vacuum_auto_clean"):
        self.timer_start("vacuum_no_clean", 3600)
        self.log("Vacuum auto clean is turned off")
        return
      if self.is_timer_active("vacuum_no_clean"):
        self.log("Vacuum no clean timer is active")
        return
      self.log("Starting automatical vacuum cleaning")
      self.turn_on_entity("script.vacuum_clean_all")
      self.start_vacuum()


  def start_vacuum(self):
    self.select_option("vacuum_room_cleaning", "all")
    self.set_vacuum_auto_clean_state("cleaning")


  def on_manual_start(self, entity, attribute, old, new, kwargs):
    self.log("Manual vacuum cleaning started")
    self.start_vacuum()


  def on_vacuum_returning(self, entity, attribute, old, new, kwargs):
    anyone_near_home = self.get_nearest_person_location() in ["home", "downstairs", "yard"]
    if self.get_vacuum_auto_clean_state() == "cleaning" and anyone_near_home:
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
    anyone_near_home = self.get_nearest_person_location() in ["home", "downstairs", "yard"]
    if self.get_vacuum_auto_clean_state() == "cleaning":
      self.log("Vacuum cleaning finished")
      self.set_vacuum_last_cleaned_ts()
      self.set_vacuum_auto_clean_state("done_charging")
      if anyone_near_home:
        self.go_to_bin()
    else:
      self.set_vacuum_auto_clean_state("idle")


  def on_vacuum_change(self, entity, attribute, old, new, kwargs):
    if new != "cleaning" and old == "cleaning":
      self.select_option("vacuum_room_cleaning", "none")


  def go_to_bin(self):
    self.log("Vacuum is moving to bin")
    self.turn_on_entity("script.vacuum_go_to_bin")
    self.set_vacuum_auto_clean_state("done_waiting")


  def set_vacuum_last_cleaned_ts(self):
    self.set_current_datetime("input_datetime.vacuum_last_cleaned")


  def set_vacuum_auto_clean_state(self, state):
    self.select_option("vacuum_autoclean_state", state)


  def get_vacuum_auto_clean_state(self):
    return self.get_state("input_select.vacuum_autoclean_state")
