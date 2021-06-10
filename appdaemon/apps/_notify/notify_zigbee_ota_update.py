import appdaemon.plugins.hass.hassapi as hass


class NotifyZigbeeOtaUpdate(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    self.storage = self.get_app("persistent_storage")
    self.storage.init("notify_zigbee_updates.entities", {})
    self.run_every(self.check_entities, "now", 600)


  def check_entities(self, kwargs):
    binary_sensors = self.get_state("binary_sensor")
    entity_update_states = self.storage.read("notify_zigbee_updates.entities", attribute="all")
    old_entities = []
    new_entities = []
    for entity in binary_sensors:
      if not entity.endswith("_update_available"):
        continue
      if self.get_state(entity) != "on":
        entity_update_states[entity] = False
        continue
      if entity not in entity_update_states or entity_update_states[entity] is False:
        new_entities.append(entity)
      else:
        old_entities.append(entity)
      entity_update_states[entity] = True
    num_updates = len(new_entities + old_entities)
    self.call_service("input_number/set_value", entity_id="input_number.zigbee_ota_updates", value=num_updates)
    if len(new_entities) > 0:
      message = self.build_message(new_entities + old_entities)
      self.persons.send_notification("admin", message, "zigbee_update", url="/hassio/ingress/45df7312_zigbee2mqtt")
    self.storage.write("notify_zigbee_updates.entities", entity_update_states, attribute="all")


  def build_message(self, entities):
    (entities_list, entities_len) = self.build_entity_list_text(entities)
    if entities_len == 1:
      message = f"💡 OTA update was found for: {entities_list}"
    else:
      message = f"💡 {entities_len} OTA updates were found for: {entities_list}"
    return message


  def build_entity_list_text(self, entities):
    if len(entities) > 3:
      entities_list = ", ".join(entities[:3]) + " and other"
    else:
      entities_list = ", ".join(entities)
    entities_len = len(entities)
    entities_list = entities_list.replace("_update_available", "").replace("binary_sensor.", "").replace("_", " ")
    entities_list = entities_list.title()
    return (entities_list, entities_len)
