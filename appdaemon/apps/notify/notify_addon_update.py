from base import Base


class NotifyAddonUpdate(Base):

  def initialize(self):
    super().initialize()
    self.init_storage("notify_addon_update", "notified_updates", {})
    self.listen_state(self.on_addon_update, "sensor.supervisor_info", attribute="all", immediate=True)


  def on_addon_update(self, entity, attribute, old, new, kwargs):
    updates_info = self.get_state("sensor.supervisor_info", attribute="all")
    try:
      updates = updates_info["attributes"]["addons"]
    except KeyError:
      return
    for update in updates:
      app_id = update["slug"]
      app_name = update["name"]
      app_version = update["version_latest"]
      notified_version = self.read_storage("notified_updates", attribute=app_id)
      if notified_version == app_version:
        continue
      self.write_storage("notified_updates", app_version, attribute=app_id)
      other_updates_int = len(updates) - 1
      message = self.build_message(app_name, app_version, other_updates_int)
      self.send_push("admin", message, "addon_update", url=f"/hassio/addon/{app_id}/info")


  def build_message(self, app_name, app_version, other_updates_int):
    other_updates_str = ""
    if other_updates_int == 1:
      other_updates_str = f". {other_updates_int} other update is also available"
    elif other_updates_int > 1:
      other_updates_str = f". {other_updates_int} other updates are also available"
    message = f"💡 Update for {app_name} ({app_version}) is available in Supervisor{other_updates_str}"
    return message
