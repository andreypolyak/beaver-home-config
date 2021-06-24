import appdaemon.plugins.hass.hassapi as hass

ROOMS = {
  "bathroom_entrance": {
    "sensors": [
      "bathroom_toilet_motion",
      "bathroom_shower_motion"
    ],
    "door": "bathroom_door"
  },
  "bedroom": {
    "sensors": [
      "bedroom_bed_motion",
      "bedroom_table_motion",
      "bedroom_floor_motion",
      "bedroom_bed_occupancy",
      "bedroom_theo_bed_occupancy",
      "bedroom_chair_occupancy"
    ],
    "door": "bedroom_door"
  }
}


class PersonInside(hass.Hass):

  def initialize(self):
    self.listen_state(self.on_image_processing, "image_processing.doods_living_room_camera")
    self.handle = None
    for room_name, room in ROOMS.items():
      for sensor in room["sensors"]:
        sensor_entity = f"binary_sensor.{sensor}"
        self.listen_state(self.on_sensor_activity, sensor_entity, new="on", old="off", room_name=room_name)
      door = room["door"]
      door_entity = f"binary_sensor.{door}"
      self.listen_state(self.on_door_open, door_entity, new="on", old="off", room_name=room_name)


  def on_sensor_activity(self, entity, attribute, old, new, kwargs):
    room_name = kwargs["room_name"]
    room = ROOMS[room_name]
    person_inside_entity = f"input_boolean.person_inside_{room_name}"
    door = room["door"]
    door_entity = f"binary_sensor.{door}"
    if self.get_state(door_entity) == "off":
      self.call_service("input_boolean/turn_on", entity_id=person_inside_entity)
    elif self.get_state(door_entity) == "on":
      self.call_service("input_boolean/turn_off", entity_id=person_inside_entity)


  def on_door_open(self, entity, attribute, old, new, kwargs):
    room_name = kwargs["room_name"]
    person_inside_entity = f"input_boolean.person_inside_{room_name}"
    self.call_service("input_boolean/turn_off", entity_id=person_inside_entity)


  def on_image_processing(self, entity, attribute, old, new, kwargs):
    if new in ["unavailable", "unknown", "None"]:
      return
    if self.timer_running(self.handle):
      self.cancel_timer(self.handle)
    if int(new) == 0:
      self.handle = self.run_in(self.empty_living_room, 60)
    else:
      self.call_service("input_boolean/turn_on", entity_id="input_boolean.person_inside_living_room")


  def empty_living_room(self, kwargs):
    person_inside_entity = "input_boolean.person_inside_living_room"
    if self.get_state(person_inside_entity) == "on":
      self.call_service("input_boolean/turn_off", entity_id=person_inside_entity)
