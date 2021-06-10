import appdaemon.plugins.hass.hassapi as hass


class NotifyNewEntity(hass.Hass):

  def initialize(self):
    self.storage = self.get_app("persistent_storage")
    self.persons = self.get_app("persons")
    self.storage.init("notify_new_entity.entities", {})
    self.handle = None
    self.new_entities = []
    self.call_service("group/set", object_id="new_entities", entities=self.new_entities)
    self.listen_event(self.on_entity_registry_updated, "entity_registry_updated", action="create")
    self.run_every(self.update_group, "now", 3600)


  def on_entity_registry_updated(self, event_name, data, kwargs):
    entity = data["entity_id"]
    self.storage.write("notify_new_entity.entities", self.get_now_ts(), attribute=entity)
    self.update_group({})
    self.new_entities.append(entity)
    if self.timer_running(self.handle):
      self.cancel_timer(self.handle)
    self.handle = self.run_in(self.send_notification, 2)


  def update_group(self, kwargs):
    entities = self.storage.read("notify_new_entity.entities", attribute="all")
    current_ts = self.get_now_ts()
    new_entities = []
    for entity, ts in entities.items():
      if (current_ts - ts) < (24 * 3600) and self.entity_exists(entity):
        new_entities.append(entity)
      # AppDaemon sometimes doesn't load state for newly created entities
      elif (current_ts - ts) < 600:
        new_entities.append(entity)
    self.call_service("group/set", object_id="new_entities", entities=new_entities)
    self.call_service("input_number/set_value", entity_id="input_number.new_entities", value=len(new_entities))


  def send_notification(self, kwargs):
    if len(self.new_entities) > 0:
      message = self.build_message(self.new_entities)
      self.persons.send_notification("admin", message, "new", sound="Tweet.caf", url="/lovelace/settings_entities")
    self.new_entities = []


  def build_message(self, entities):
    (entities_list, entities_len) = self.build_entity_list(entities)
    if entities_len == 1:
      message = f"🆕 New entity was found: {entities_list}"
    else:
      message = f"🆕 {entities_len} new entities were found: {entities_list}"
    return message


  def build_entity_list(self, entities):
    if len(entities) > 3:
      entities_list = ", ".join(entities[:3]) + " and other"
    else:
      entities_list = ", ".join(entities)
    entities_len = len(entities)
    return (entities_list, entities_len)
