from base import Base


class StorageRoom(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_storage_room_change, "binary_sensor.storage_room_door", immediate=True)


  def on_storage_room_change(self, entity, attribute, old, new, kwargs):
    entity = "light.group_storage_room"
    transition = self.get_float_state("input_number.transition")
    if new == "on":
      self.turn_on_entity(entity, brightness=254, transition=transition)
    elif new == "off":
      self.turn_off_entity(entity, transition=transition)
