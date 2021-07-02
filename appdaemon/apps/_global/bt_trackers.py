import appdaemon.plugins.hass.hassapi as hass

ROOMS = ["entrance", "kitchen"]


class BtTrackers(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    for person in self.persons.get_all_persons(with_phone=True):
      person_phone = person["phone"]
      for room in ROOMS:
        entity = f"sensor.bt_{room}_{person_phone}_confidence"
        self.listen_state(self.on_room_confidence_change, entity, immediate=True)
      entity = f"sensor.bt_{person_phone}_confidence"
      self.listen_state(self.on_confidence_change, entity, immediate=True)


  def on_room_confidence_change(self, entity, attribute, old, new, kwargs):
    try:
      confidence = float(new)
    except ValueError:
      return
    room = self.get_room_from_entity(entity)
    person = self.persons.get_person_from_entity_name(entity)
    person_phone = person["phone"]
    state = "home"
    if confidence <= 10:
      state = "not_home"
    dev_id = f"bt_{room}_{person_phone}"
    self.call_service("device_tracker/see", dev_id=dev_id, location_name=state, source_type="bluetooth")


  def on_confidence_change(self, entity, attribute, old, new, kwargs):
    try:
      confidence = float(new)
    except ValueError:
      return
    person = self.persons.get_person_from_entity_name(entity)
    person_phone = person["phone"]
    state = "home"
    if confidence <= 10:
      state = "not_home"
    dev_id = f"bt_{person_phone}"
    self.call_service("device_tracker/see", dev_id=dev_id, location_name=state, source_type="bluetooth")


  def get_room_from_entity(self, entity):
    for room in ROOMS:
      if room in entity:
        return room
