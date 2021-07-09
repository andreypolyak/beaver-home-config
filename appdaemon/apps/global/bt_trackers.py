from base import Base

ROOMS = ["entrance", "kitchen"]


class BtTrackers(Base):

  def initialize(self):
    super().initialize()
    for person in self.get_all_persons(with_phone=True):
      person_phone = person["phone"]
      for room in ROOMS:
        self.listen_state(self.on_room_confidence_change, f"sensor.bt_{room}_{person_phone}_confidence", immediate=True)
      self.listen_state(self.on_confidence_change, f"sensor.bt_{person_phone}_confidence", immediate=True)


  def on_room_confidence_change(self, entity, attribute, old, new, kwargs):
    confidence = self.get_float_state(new)
    if confidence is None:
      return
    room = self.get_room_from_entity(entity)
    person = self.get_person_from_entity_name(entity)
    person_phone = person["phone"]
    state = "home"
    if confidence <= 10:
      state = "not_home"
    dev_id = f"bt_{room}_{person_phone}"
    self.call_service("device_tracker/see", dev_id=dev_id, location_name=state, source_type="bluetooth")


  def on_confidence_change(self, entity, attribute, old, new, kwargs):
    confidence = self.get_float_state(new)
    if confidence is None:
      return
    person = self.get_person_from_entity_name(entity)
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
