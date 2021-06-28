import appdaemon.plugins.hass.hassapi as hass


class Location(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    self.storage = self.get_app("persistent_storage")
    self.storage.init("location.lock_unlocked_ts", 0)
    for person in self.persons.get_all_persons():
      person_name = person["name"]
      person_phone = person["phone"]
      if not person_phone:
        continue
      self.listen_state(self.on_change, f"device_tracker.wifi_{person_phone}")
      self.listen_state(self.on_change, f"device_tracker.ha_{person_phone}")
      self.listen_state(self.on_change, f"proximity.ha_{person_name}_home")
      self.listen_state(self.on_location_change, f"input_select.{person_name}_location")
      self.process(person)
    self.listen_state(self.on_lock_unlock, "lock.entrance_lock", new="unlocked")
    service_data = {"entity_id": "lock.entrance_lock", "service": "unlock"}
    self.listen_event(self.on_lock_unlock_service_call, "call_service", domain="lock", service_data=service_data)
    self.set_nearest_person_location()


  def on_lock_unlock(self, entity, attribute, old, new, kwargs):
    self.update_unlocked_ts()


  def on_lock_unlock_service_call(self, event_name, data, kwargs):
    self.update_unlocked_ts()


  def update_unlocked_ts(self):
    self.storage.write("location.lock_unlocked_ts", self.get_now_ts())
    persons = self.persons.get_all_persons()
    for person in persons:
      self.process(person)


  def on_change(self, entity, attribute, old, new, kwargs):
    person = self.persons.get_person_from_entity_name(entity)
    self.process(person)


  def process(self, person):
    location = self.get_person_location(person)
    self.set_person_location(person, location)


  def get_person_location(self, person):
    person_name = person["name"]
    person_phone = person["phone"]
    if not person_phone:
      return
    wifi_home = self.get_state(f"device_tracker.wifi_{person_phone}") == "home"
    ha_home = self.get_state(f"device_tracker.ha_{person_phone}") == "home"
    try:
      proximity = float(self.get_state(f"proximity.ha_{person_name}_home"))
    except ValueError:
      proximity = None
    location = self.get_state(f"input_select.{person_name}_location")
    lock_unlocked_ts = self.storage.read("location.lock_unlocked_ts")
    lock_unlocked_delta = self.get_now_ts() - lock_unlocked_ts

    if (
      not wifi_home
      and not ha_home
      and (proximity is None or proximity > 500)
    ):
      return "not_home"
    elif (
      not wifi_home
      and not ha_home
      and proximity is not None
      and proximity <= 500
    ):
      return "district"
    elif (
      location != "home"
      and not wifi_home
      and ha_home
    ):
      return "yard"
    elif (
      location in ["not_home", "district", "yard", "downstairs"]
      and wifi_home
      and lock_unlocked_delta > 300
    ):
      return "downstairs"
    else:
      return "home"


  def set_person_location(self, person, location):
    person_name = person["name"]
    entity = f"input_select.{person_name}_location"
    if self.entity_exists(entity):
      self.call_service("input_select/select_option", entity_id=entity, option=location)


  def on_location_change(self, entity, attribute, old, new, kwargs):
    self.set_nearest_person_location()


  def set_nearest_person_location(self):
    nearest_location = "not_home"
    for location in ["not_home", "district", "yard", "downstairs", "home"]:
      for entity in self.persons.get_all_person_location_entities():
        if self.get_state(entity) == location:
          nearest_location = location
    self.call_service("input_select/select_option", entity_id="input_select.nearest_person_location",
                      option=nearest_location)
