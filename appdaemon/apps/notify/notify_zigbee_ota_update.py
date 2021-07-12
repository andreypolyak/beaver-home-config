from base import Base


class NotifyZigbeeOtaUpdate(Base):

  def initialize(self):
    super().initialize()
    self.init_storage("notify_zigbee_updates", "entities", {})
    self.run_every(self.check_entities, "now+120", 600)


  def check_entities(self, kwargs):
    entity_update_states = self.read_storage("entities", attribute="all")
    old_entities = []
    new_entities = []
    for entity in self.get_state("binary_sensor"):
      if not entity.endswith("_update_available"):
        continue
      if self.is_entity_off(entity):
        entity_update_states[entity] = False
        continue
      if entity not in entity_update_states or entity_update_states[entity] is False:
        new_entities.append(entity)
      else:
        old_entities.append(entity)
      entity_update_states[entity] = True
    num_updates = len(new_entities + old_entities)
    self.set_value("input_number.zigbee_ota_updates", num_updates)
    if len(new_entities) > 0:
      message = self.build_message(new_entities + old_entities)
      self.send_push("admin", message, "zigbee_update", url="/hassio/ingress/45df7312_zigbee2mqtt")
    self.write_storage("entities", entity_update_states, attribute="all")


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
