import appdaemon.plugins.hass.hassapi as hass


class NotifyAddonUpdate(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    self.storage = self.get_app("persistent_storage")
    self.storage.init("notify_addon_update.notified_updates", {})
    self.listen_state(self.on_addon_update, "sensor.supervisor_info", attribute="all")
    self.check_updates()


  def on_addon_update(self, entity, attribute, old, new, kwargs):
    self.check_updates()


  def check_updates(self):
    updates_info = self.get_state("sensor.supervisor_info", attribute="all")
    updates = updates_info["attributes"]["addons"]
    for update in updates:
      app_id = update["slug"]
      app_name = update["name"]
      app_version = update["version_latest"]
      notified_version = self.storage.read("notify_addon_update.notified_updates", attribute=app_id)
      if notified_version == app_version:
        continue
      self.storage.write("notify_addon_update.notified_updates", app_version, attribute=app_id)
      other_updates_int = len(updates) - 1
      message = self.build_message(app_name, app_version, other_updates_int)
      self.persons.send_notification("admin", message, "addon_update", url=f"/hassio/addon/{app_id}/info")


  def build_message(self, app_name, app_version, other_updates_int):
    other_updates_str = ""
    if other_updates_int == 1:
      other_updates_str = f". {other_updates_int} other update is also available"
    elif other_updates_int > 1:
      other_updates_str = f". {other_updates_int} other updates are also available"
    message = f"💡 Update for {app_name} ({app_version}) is available in Supervisor{other_updates_str}"
    return message
