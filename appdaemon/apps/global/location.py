from base import Base


class Location(Base):

  def initialize(self):
    super().initialize()
    self.init_storage("location", "lock_unlocked_ts", 0)
    self.restart_ts = self.get_now_ts()
    for person in self.get_persons(with_phone=True):
      person_name = person["name"]
      person_phone = person["phone"]
      self.listen_state(self.on_tracker_change, f"device_tracker.wifi_{person_phone}")
      self.listen_state(self.on_tracker_change, f"device_tracker.ha_{person_phone}")
      self.listen_state(self.on_tracker_change, f"device_tracker.bt_{person_phone}")
      self.listen_state(self.on_tracker_change, f"proximity.ha_{person_name}_home")
      self.listen_state(self.on_location_change, f"input_select.{person_name}_location")
      self.update_person_location(person)
    self.listen_state(self.on_lock_unlock, "lock.entrance_lock", new="unlocked")
    service_data = {"entity_id": "lock.entrance_lock", "service": "unlock"}
    self.listen_event(self.on_lock_unlock_service_call, "call_service", domain="lock", service_data=service_data)
    self.set_nearest_person_location()


  def on_lock_unlock(self, entity, attribute, old, new, kwargs):
    self.update_unlocked_ts()


  def on_lock_unlock_service_call(self, event_name, data, kwargs):
    self.update_unlocked_ts()


  def update_unlocked_ts(self):
    self.write_storage("lock_unlocked_ts", self.get_now_ts())
    persons = self.get_persons(with_location=True)
    for person in persons:
      self.update_person_location(person)


  def on_tracker_change(self, entity, attribute, old, new, kwargs):
    person = self.get_persons(entity=entity)[0]
    self.update_person_location(person)


  def update_person_location(self, person):
    location = self.get_person_location(person)
    self.set_person_location(person, location)


  def get_person_location(self, person):
    person_name = person["name"]
    person_phone = person["phone"]
    if not person_phone:
      return
    wifi_home = self.get_state(f"device_tracker.wifi_{person_phone}") == "home"
    bt_home = self.get_state(f"device_tracker.bt_{person_phone}") == "home"
    ha_home = self.get_state(f"device_tracker.ha_{person_phone}") == "home"
    proximity = self.get_float_state(f"proximity.ha_{person_name}_home")
    location = self.get_state(f"input_select.{person_name}_location")
    lock_unlocked_ts = self.read_storage("lock_unlocked_ts")

    if (
      not wifi_home
      and not bt_home
      and not ha_home
      and (proximity is None or proximity > 500)
    ):
      return "not_home"
    elif (
      not wifi_home
      and not bt_home
      and not ha_home
      and proximity is not None
      and proximity <= 500
    ):
      return "district"
    elif (
      not wifi_home
      and not bt_home
      and ha_home
    ):
      return "yard"
    elif (
      location in ["not_home", "district", "yard", "downstairs"]
      and (wifi_home or bt_home)
      and self.get_delta_ts(lock_unlocked_ts) > 300
      and self.get_delta_ts(self.restart_ts) > 120
    ):
      return "downstairs"
    else:
      return "home"


  def set_person_location(self, person, location):
    person_name = person["name"]
    self.select_option(f"{person_name}_location", location)


  def on_location_change(self, entity, attribute, old, new, kwargs):
    person_name = self.get_person_names(entity=entity)[0]
    self.log(f"New location for {person_name}: {new}. Was: {old}")
    self.set_nearest_person_location()


  def set_nearest_person_location(self):
    nearest_location = "not_home"
    for location in ["not_home", "district", "yard", "downstairs", "home"]:
      for entity in self.get_person_locations():
        if self.get_state(entity) == location:
          nearest_location = location
    self.select_option("nearest_person_location", nearest_location)
