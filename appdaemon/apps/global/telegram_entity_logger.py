from base import Base
import html

MODES = ["entities", "entities_with_attr"]


class TelegramEntityLogger(Base):

  def initialize(self):
    super().initialize()
    self.handles = {}
    for mode in MODES:
      self.init_storage("telegram_entity_logger", mode, [])
      self.handles[mode] = []
    self.listen_event(self.on_entities_change, "entity_registry_updated")
    self.listen_event(self.on_entities_change, "call_service", domain="input_select", service="reload")
    self.listen_event(self.on_logged_entity_add, "custom_event", custom_event_data="logged_entity_add")
    self.listen_event(self.on_logged_entity_remove, "custom_event", custom_event_data="logged_entity_remove")
    self.update_entities_lists({})


  def on_logged_entity_add(self, event_name, data, kwargs):
    mode = data["custom_event_data2"]
    added_entity = self.get_state("input_select.all_entities")
    logged_entities = self.read_storage(mode)
    logged_entities.insert(0, added_entity)
    self.write_storage(mode, logged_entities)
    self.update_entities_lists({})


  def on_logged_entity_remove(self, event_name, data, kwargs):
    mode = data["custom_event_data2"]
    removed_entity = self.get_state(f"input_select.logged_{mode}")
    if removed_entity != "":
      logged_entities = self.read_storage(mode)
      logged_entities.remove(removed_entity)
      self.write_storage(mode, logged_entities)
      self.update_entities_lists({})


  def on_entities_change(self, event_name, data, kwargs):
    self.run_in(self.update_entities_lists, 5)


  def on_state_change(self, entity, attribute, old, new, kwargs):
    mode = kwargs["mode"]
    if mode == "entities_with_attr":
      text = f"New state: {str(new)}"
    else:
      text = f"{entity}: {old}→{new}"
    if self.is_entity_on("input_boolean.log_entities"):
      self.send_to_bot(text)


  def update_entities_lists(self, kwargs):
    self.log("Updating entities list")
    all_entities = list(self.get_state().keys())
    not_logged_entities = all_entities.copy()
    total_logged_entities = 0
    for mode in MODES:
      logged_entities = self.read_storage(mode)
      for entity in logged_entities:
        if entity not in all_entities:
          logged_entities.remove(entity)
        if entity in logged_entities:
          not_logged_entities.remove(entity)
      total_logged_entities += len(logged_entities)
      if len(logged_entities) == 0:
        logged_entities = [""]
      self.set_options(f"logged_{mode}", options=logged_entities)

      for handle in self.handles[mode]:
        if handle:
          self.cancel_listen_state(handle)
      self.handles[mode] = []
      for entity in logged_entities:
        if entity != "":
          if mode == "entities_with_attr":
            handle = self.listen_state(self.on_state_change, entity, attribute="all", mode=mode)
          else:
            handle = self.listen_state(self.on_state_change, entity, mode=mode)
          self.handles[mode].append(handle)

    self.set_value("input_number.logged_entities", total_logged_entities)
    if len(not_logged_entities) == 0:
      not_logged_entities = [""]
    else:
      not_logged_entities = sorted(not_logged_entities)
    self.set_options("all_entities", options=not_logged_entities)


  def send_to_bot(self, text):
    message = html.escape(text[:3500])
    chat_id = self.args["chat_id"]
    try:
      self.call_service("telegram_bot/send_message", message=message, target=chat_id, disable_notification=True)
    except:
      pass
