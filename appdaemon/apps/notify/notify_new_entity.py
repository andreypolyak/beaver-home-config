from base import Base


class NotifyNewEntity(Base):

  def initialize(self):
    super().initialize()
    self.init_storage("notify_new_entity", "new_entities", {})
    self.init_storage("notify_new_entity", "all_entities", [])
    self.handle = None
    self.new_entities = []
    self.call_service("group/set", object_id="new_entities", entities=self.new_entities)
    self.listen_event(self.on_entity_registry_updated, "entity_registry_updated", action="create")
    self.run_every(self.update_group, "now", 3600)
    self.run_every(self.check_all_entities, "now", 120)


  def check_all_entities(self, kwargs):
    all_entities = list(self.get_state().keys())
    saved_all_entities = self.read_storage("all_entities")
    if len(saved_all_entities) > 0:
      for entity in all_entities:
        if entity in saved_all_entities:
          continue
        self.handle_new_entity(entity)
    self.write_storage("all_entities", all_entities)


  def on_entity_registry_updated(self, event_name, data, kwargs):
    entity = data["entity_id"]
    self.handle_new_entity(entity)


  def handle_new_entity(self, entity):
    new_entities = self.read_storage("new_entities", attribute="all")
    if entity in new_entities or "persistent_notification." in entity:
      return
    self.write_storage("new_entities", self.get_now_ts(), attribute=entity)
    self.update_group({})
    self.new_entities.append(entity)
    self.cancel_handle(self.handle)
    self.handle = self.run_in(self.send_notification, 2)


  def update_group(self, kwargs):
    entities = self.read_storage("new_entities", attribute="all")
    new_entities = []
    for entity, ts in entities.items():
      if self.get_delta_ts(ts) < 86400 and self.entity_exists(entity):
        new_entities.append(entity)
      # AppDaemon sometimes doesn't load state for newly created entities
      elif self.get_delta_ts(ts) < 600:
        new_entities.append(entity)
    self.call_service("group/set", object_id="new_entities", entities=new_entities)
    self.set_value("input_number.new_entities", len(new_entities))


  def send_notification(self, kwargs):
    if len(self.new_entities) > 0:
      message = self.build_message(self.new_entities)
      self.send_push("admin", message, "new", sound="Tweet.caf", url="/lovelace/settings_entities")
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
