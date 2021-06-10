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
      self.listen_state(self.on_change, f"device_tracker.bt_entrance_{person_phone}_tracker")
      self.listen_state(self.on_change, f"device_tracker.bt_kitchen_{person_phone}_tracker")
      self.listen_state(self.on_change, f"device_tracker.wifi_{person_phone}")
      self.listen_state(self.on_change, f"device_tracker.ha_{person_phone}")
      self.listen_state(self.on_change, f"proximity.ha_{person_name}_home")
      self.process(person)
    self.listen_state(self.on_lock_unlock, "lock.entrance_lock", new="unlocked")
    service_data = {"entity_id": "lock.entrance_lock", "service": "unlock"}
    self.listen_event(self.on_lock_unlock_service_call, "call_service", domain="lock", service_data=service_data)


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
    bt_home = self.get_state(f"device_tracker.bt_global_{person_phone}") == "home"
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
      not bt_home
      and not wifi_home
      and not ha_home
      and (proximity is None or proximity > 500)
    ):
      return "not_home"
    elif (
      not bt_home
      and not wifi_home
      and not ha_home
      and proximity is not None
      and proximity <= 500
    ):
      return "district"
    elif (
      location != "home"
      and not bt_home
      and not wifi_home
      and ha_home
    ):
      return "yard"
    elif (
      location in ["not_home", "district", "yard", "downstairs"]
      and (bt_home or wifi_home)
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
