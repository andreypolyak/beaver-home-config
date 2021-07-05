import appdaemon.plugins.hass.hassapi as hass


class StorageRoom(hass.Hass):

  def initialize(self):
    self.listen_state(self.on_storage_room_change, "binary_sensor.storage_room_door", immediate=True)


  def on_storage_room_change(self, entity, attribute, old, new, kwargs):
    entity = "light.group_storage_room"
    transition = float(self.get_state("input_number.transition"))
    if new == "on":
      self.call_service("light/turn_on", entity_id=entity, brightness=254, transition=transition)
    elif new == "off":
      self.call_service("light/turn_off", entity_id=entity, transition=transition)
