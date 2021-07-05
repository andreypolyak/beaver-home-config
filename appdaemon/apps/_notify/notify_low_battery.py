import appdaemon.plugins.hass.hassapi as hass

BLACKLIST = [
  "apple",
  "iphone",
  "macbook",
  "ipad",
  "playstation",
  "sonos"
]


class NotifyLowBattery(hass.Hass):

  def initialize(self):
    self.notifications = self.get_app("notifications")
    self.storage = self.get_app("persistent_storage")
    self.storage.init("notify_low_battery.entities", {})
    self.run_every(self.check_entities, "now+120", 600)


  def check_entities(self, kwargs):
    url = "/lovelace/settings_batteries"
    sensors = self.get_state("sensor")
    entity_low_battery_states = self.storage.read("notify_low_battery.entities", attribute="all")
    old_entities = []
    new_entities = []
    for entity in sensors:
      if not entity.endswith("_battery"):
        continue
      if any(i in entity for i in BLACKLIST):
        continue
      try:
        if float(self.get_state(entity)) > 10:
          entity_low_battery_states[entity] = False
          continue
      except (ValueError, TypeError):
        continue
      if entity not in entity_low_battery_states or entity_low_battery_states[entity] is False:
        new_entities.append(entity)
      else:
        old_entities.append(entity)
      entity_low_battery_states[entity] = True
    num_devices = len(new_entities + old_entities)
    self.call_service("input_number/set_value", entity_id="input_number.low_battery_devices", value=num_devices)
    if len(new_entities) > 0:
      message = self.build_message(new_entities + old_entities)
      self.notifications.send("admin", message, "low_battery", sound="Aurora.caf", url=url)
    elif len(old_entities) > 0:
      message = self.build_message(new_entities + old_entities)
      self.notifications.send("admin", message, "low_battery", sound="Aurora.caf", min_delta=86400, url=url)
    self.storage.write("notify_low_battery.entities", entity_low_battery_states, attribute="all")


  def build_message(self, entities):
    (entities_list, entities_len) = self.build_entity_list_text(entities)
    if entities_len == 1:
      message = f"🔋 New low battery device was found: {entities_list}"
    else:
      message = f"🔋 {entities_len} new low battery devices were found: {entities_list}"
    return message


  def build_entity_list_text(self, entities):
    if len(entities) > 3:
      entities_list = ", ".join(entities[:3]) + " and other"
    else:
      entities_list = ", ".join(entities)
    entities_len = len(entities)
    entities_list = entities_list.replace("_battery", "").replace("sensor.", "").replace("_", " ").title()
    return (entities_list, entities_len)
