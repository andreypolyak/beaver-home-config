from base import Base

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


class PersonInside(Base):

  def initialize(self):
    super().initialize()
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
    door = room["door"]
    if self.is_entity_off(f"binary_sensor.{door}"):
      self.turn_on_entity(f"input_boolean.person_inside_{room_name}")
    elif self.is_entity_on(f"binary_sensor.{door}"):
      self.turn_off_entity(f"input_boolean.person_inside_{room_name}")


  def on_door_open(self, entity, attribute, old, new, kwargs):
    room_name = kwargs["room_name"]
    self.turn_off_entity(f"input_boolean.person_inside_{room_name}")
