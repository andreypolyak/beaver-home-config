import appdaemon.plugins.hass.hassapi as hass


class StorageRoom(hass.Hass):

  def initialize(self):
    self.listen_state(self.on_storage_room_change, "binary_sensor.storage_room_door")


  def on_storage_room_change(self, entity, attribute, old, new, kwargs):
    if new == "on":
      self.call_service("light/turn_on", entity_id="light.group_storage_room", brightness=254,
                        transition=self.get_transition())
    elif new == "off":
      self.call_service("light/turn_off", entity_id="light.group_storage_room", transition=self.get_transition())


  def get_transition(self):
    return float(self.get_state("input_number.transition"))
