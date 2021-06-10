import appdaemon.plugins.hass.hassapi as hass
import html

MODES = ["entities", "entities_with_attr"]


class TelegramEntityLogger(hass.Hass):

  def initialize(self):
    self.storage = self.get_app("persistent_storage")
    self.handles = {}
    for mode in MODES:
      self.storage.init(f"telegram_entity_logger.{mode}", [])
      self.handles[mode] = []
    self.listen_event(self.on_entities_change, "entity_registry_updated")
    self.listen_event(self.on_entities_change, "call_service", domain="input_select", service="reload")
    self.listen_event(self.on_logged_entity_add, "custom_event", custom_event_data="logged_entity_add")
    self.listen_event(self.on_logged_entity_remove, "custom_event", custom_event_data="logged_entity_remove")
    self.update_entities_lists({})


  def on_logged_entity_add(self, event_name, data, kwargs):
    mode = data["custom_event_data2"]
    added_entity = self.get_state("input_select.all_entities")
    logged_entities = self.get_logged_entities(mode)
    logged_entities.insert(0, added_entity)
    self.save_logged_entities(logged_entities, mode)
    self.update_entities_lists({})


  def on_logged_entity_remove(self, event_name, data, kwargs):
    mode = data["custom_event_data2"]
    removed_entity = self.get_state(f"input_select.logged_{mode}")
    if removed_entity != "":
      logged_entities = self.get_logged_entities(mode)
      logged_entities.remove(removed_entity)
      self.save_logged_entities(logged_entities, mode)
      self.update_entities_lists({})


  def on_entities_change(self, event_name, data, kwargs):
    self.run_in(self.update_entities_lists, 5)


  def on_state_change(self, entity, attribute, old, new, kwargs):
    mode = kwargs["mode"]
    if mode == "entities_with_attr":
      text = f"New state: {str(new)}"
    else:
      text = f"{entity}: {old}→{new}"
    if self.get_state("input_boolean.log_entities") == "on":
      self.send_to_bot(text)


  def get_logged_entities(self, mode):
    entities = self.storage.read(f"telegram_entity_logger.{mode}")
    return entities


  def save_logged_entities(self, entities, mode):
    self.storage.write(f"telegram_entity_logger.{mode}", entities)


  def update_entities_lists(self, kwargs):
    self.log("Updating entities list")
    all_entities = list(self.get_state().keys())
    not_logged_entities = all_entities.copy()
    total_logged_entities = 0
    for mode in MODES:
      logged_entities = self.get_logged_entities(mode)
      for entity in logged_entities:
        if entity not in all_entities:
          logged_entities.remove(entity)
        if entity in logged_entities:
          not_logged_entities.remove(entity)
      total_logged_entities += len(logged_entities)
      if len(logged_entities) == 0:
        logged_entities = [""]
      self.call_service("input_select/set_options", entity_id=f"input_select.logged_{mode}", options=logged_entities)

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

    self.call_service("input_number/set_value", entity_id="input_number.logged_entities", value=total_logged_entities)
    if len(not_logged_entities) == 0:
      not_logged_entities = [""]
    self.call_service("input_select/set_options", entity_id="input_select.all_entities",
                      options=sorted(not_logged_entities))


  def send_to_bot(self, text):
    message = html.escape(text[:3500])
    chat_id = self.args["chat_id"]
    self.call_service("telegram_bot/send_message", message=message, target=chat_id, disable_notification=True)
