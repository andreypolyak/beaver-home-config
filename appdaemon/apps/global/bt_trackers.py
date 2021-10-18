from base import Base


class BtTrackers(Base):

  def initialize(self):
    super().initialize()
    for person in self.get_persons(with_phone=True):
      person_phone = person["phone"]
      for sensor in self.get_state("sensor"):
        room = sensor.replace(f"_{person_phone}_confidence", "").replace("sensor.bt_", "")
        if sensor == f"sensor.bt_{person_phone}_confidence":
          continue
        if not sensor.endswith(f"_{person_phone}_confidence") or not sensor.startswith("sensor.bt_"):
          continue
        self.log_var(room, sensor)
        self.listen_state(self.on_room_confidence_change, sensor, immediate=True, room=room)
      self.listen_state(self.on_confidence_change, f"sensor.bt_{person_phone}_confidence", immediate=True)


  def on_room_confidence_change(self, entity, attribute, old, new, kwargs):
    confidence = self.get_float_state(new)
    if confidence is None:
      return
    room = kwargs["room"]
    person = self.get_persons(entity=entity)[0]
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
    person = self.get_persons(entity=entity)[0]
    person_phone = person["phone"]
    state = "home"
    if confidence <= 10:
      state = "not_home"
    dev_id = f"bt_{person_phone}"
    self.call_service("device_tracker/see", dev_id=dev_id, location_name=state, source_type="bluetooth")
