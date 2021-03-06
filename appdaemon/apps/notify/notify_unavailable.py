from base import Base
import json


BLACKLIST = [
  "apple",
  "iphone",
  "macbook",
  "ipad",
  "playstation",
  "new_entities"
]


class NotifyUnavailable(Base):

  def initialize(self):
    super().initialize()
    self.new_unavailable_entities = []
    self.init_storage("notify_unavailable", "entities", {})
    self.entity_registry = None
    self.device_registry = None
    self.initial_run = True
    self.clear_entities()
    self.listen_state(self.on_unavailable_state, new="unavailable")
    self.run_every(self.process, "now+60", 5)


  def on_unavailable_state(self, entity, attribute, old, new, kwargs):
    if any(i in entity for i in BLACKLIST):
      return
    if not self.read_storage("entities", attribute=entity):
      data = {"ts": self.get_now_ts(), "notified": False}
      self.write_storage("entities", data, attribute=entity)


  def process(self, kwargs):
    self.clear_entities()
    self.get_registries()
    if self.initial_run:
      self.initial_process()
    else:
      self.saved_entities = self.read_storage("entities", attribute="all")
    self.process_saved_entities()
    if len(self.notify_entities) > 0:
      self.send_unavailable_notifications()
    if self.get_int_state("input_number.unavailable_entities") != self.unavailable_entities_len:
      self.set_value("input_number.unavailable_entities", self.unavailable_entities_len)
    if len(self.available_entities) > 0:
      self.send_available_notifications()
    self.write_storage("entities", self.saved_entities, attribute="all")


  def initial_process(self):
    self.initial_run = False
    self.saved_entities = {}
    all_entities = self.get_state()
    prev_entities = self.read_storage("entities", attribute="all")
    for entity in all_entities.keys():
      if any(i in entity for i in BLACKLIST):
        continue
      if entity in prev_entities:
        self.saved_entities[entity] = prev_entities[entity]
      else:
        self.saved_entities[entity] = {"ts": self.get_now_ts(), "notified": False}


  def process_saved_entities(self):
    del_entities = []
    for entity, entity_obj in self.saved_entities.items():
      if not self.entity_exists(entity) or self.get_state(entity, attribute="restored") is True:
        del_entities.append(entity)
        continue
      entity_state = self.get_state(entity)
      if entity_state == "unknown":
        del_entities.append(entity)
        continue
      if entity_state != "unavailable":
        self.available_entities.append(entity)
        continue
      if self.get_delta_ts(entity_obj["ts"]) < 480:
        continue
      if self.get_delta_ts(entity_obj["ts"]) >= 480 and self.get_delta_ts(entity_obj["ts"]) < 600:
        self.possible_notify_entities.append(entity)
        continue
      self.unavailable_entities_len += 1
      if entity_obj["notified"]:
        continue
      self.notify_entities.append(entity)
      self.saved_entities[entity]["notified"] = True
    for entity in del_entities:
      del self.saved_entities[entity]


  def send_unavailable_notifications(self):
    for entity in self.possible_notify_entities:
      self.notify_entities.append(entity)
      self.saved_entities[entity]["notified"] = True
    notify_objs = []
    for notify_entity in self.notify_entities:
      device_name = self.get_device_name(notify_entity)
      if device_name:
        notify_objs.append(device_name)
      else:
        notify_objs.append(notify_entity)
    notify_objs = list(set(notify_objs))
    if len(notify_objs) > 0:
      self.log(f"Send notification about unavailable entities: {notify_objs}")
      message = self.build_unavailable_message(notify_objs)
      self.send_push("admin", message, "unavailable_entity", sound="Noir.caf", url="/lovelace/settings_entities")


  def send_available_notifications(self):
    notify_objs = []
    for available_entity in self.available_entities:
      if available_entity in self.saved_entities and self.saved_entities[available_entity]["notified"]:
        if self.get_device_name(available_entity):
          notify_objs.append(self.get_device_name(available_entity))
        elif self.friendly_name(available_entity):
          notify_objs.append(self.friendly_name(available_entity))
        else:
          notify_objs.append(available_entity)
    notify_objs = list(set(notify_objs))
    if len(notify_objs) > 0:
      self.log(f"Send notification about available entities: {notify_objs}")
      message = self.build_available_message(notify_objs)
      self.send_push("admin", message, "available_entity", sound="Fanfare.caf", url="/lovelace/settings_entities")
    for entity in self.available_entities:
      del self.saved_entities[entity]


  def build_unavailable_message(self, entities):
    (entities_list, entities_len) = self.build_entity_list(entities)
    if entities_len == 1:
      message = f"???? New unavailable device: {entities_list}"
    else:
      message = f"???? {entities_len} new unavailable devices: {entities_list}"
    return message


  def build_available_message(self, entities):
    (entities_list, entities_len) = self.build_entity_list(entities)
    if entities_len == 1:
      message = f"???? Device is available now: {entities_list}"
    else:
      message = f"???? {entities_len} devices are available now: {entities_list}"
    return message


  def build_entity_list(self, entities):
    if len(entities) > 3:
      entities_list = ", ".join(entities[:3]) + " and other"
    else:
      entities_list = ", ".join(entities)
    entities_len = len(entities)
    return (entities_list, entities_len)


  def get_registries(self):
    with open("/config/.storage/core.entity_registry") as json_file:
      self.entity_registry = json.load(json_file)["data"]["entities"]
    with open("/config/.storage/core.device_registry") as json_file:
      self.device_registry = json.load(json_file)["data"]["devices"]


  def get_device_name(self, entity_id):
    device_name = None
    device_id = None
    for entity_obj in self.entity_registry:
      if entity_obj["entity_id"] == entity_id:
        if entity_obj["device_id"] is not None:
          device_id = entity_obj["device_id"]
        break
    if not device_id:
      return None
    for device_obj in self.device_registry:
      if device_obj["id"] == device_id:
        device_name = device_obj["name"]
        break
    return device_name


  def clear_entities(self):
    self.saved_entities = {}
    self.notify_entities = []
    self.possible_notify_entities = []
    self.available_entities = []
    self.unavailable_entities_len = 0
