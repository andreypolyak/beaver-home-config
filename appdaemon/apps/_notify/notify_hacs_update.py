import appdaemon.plugins.hass.hassapi as hass


class NotifyHacsUpdate(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    self.storage = self.get_app("persistent_storage")
    self.storage.init("notify_hacs_update.notified_updates", {})
    self.listen_state(self.on_hacs_update, "sensor.hacs_updates", attribute="all")
    self.check_updates()


  def on_hacs_update(self, entity, attribute, old, new, kwargs):
    self.check_updates()


  def check_updates(self):
    updates_info = self.get_state("sensor.hacs", attribute="all")
    updates = updates_info["attributes"]["repositories"]
    for update in updates:
      app_id = update["name"]
      app_name = update["display_name"]
      app_version = update["available_version"]
      notified_version = self.storage.read("notify_hacs_update.notified_updates", attribute=app_id)
      if notified_version == app_version:
        continue
      self.storage.write("notify_hacs_update.notified_updates", app_version, attribute=app_id)
      other_updates_int = len(updates) - 1
      message = self.build_message(app_name, app_version, other_updates_int)
      self.persons.send_notification("admin", message, "hacs_update", url="/hacs")


  def build_message(self, app_name, app_version, other_updates_int):
    other_updates_str = ""
    if other_updates_int == 1:
      other_updates_str = f". {other_updates_int} other update is also available"
    elif other_updates_int > 1:
      other_updates_str = f". {other_updates_int} other updates are also available"
    message = f"💡 Update for {app_name} ({app_version}) is available in HACS{other_updates_str}"
    return message
