from base import Base


class NotifyHacsUpdate(Base):

  def initialize(self):
    super().initialize()
    self.init_storage("notify_hacs_update", "notified_updates", {})
    self.listen_state(self.on_hacs_update, "sensor.hacs_updates", attribute="all", immediate=True)
    self.listen_event(self.on_install, "hacs/repository", action="install")


  def on_hacs_update(self, entity, attribute, old, new, kwargs):
    updates_info = self.get_state("sensor.hacs", attribute="all")
    try:
      updates = updates_info["attributes"]["repositories"]
    except KeyError:
      return
    for update in updates:
      app_id = update["name"]
      app_name = update["display_name"]
      app_version = update["available_version"]
      notified_version = self.read_storage("notified_updates", attribute=app_id)
      if notified_version == app_version:
        continue
      self.write_storage("notified_updates", app_version, attribute=app_id)
      other_updates_int = len(updates) - 1
      message = self.build_message(app_name, app_version, other_updates_int)
      self.send_push("admin", message, "hacs_update", url="/hacs")


  def build_message(self, app_name, app_version, other_updates_int):
    other_updates_str = ""
    if other_updates_int == 1:
      other_updates_str = f". {other_updates_int} other update is also available"
    elif other_updates_int > 1:
      other_updates_str = f". {other_updates_int} other updates are also available"
    message = f"💡 Update for {app_name} ({app_version}) is available in HACS{other_updates_str}"
    return message


  def on_install(self, event_name, data, kwargs):
    self.run_in(self.update_sensor, 5)
    self.run_in(self.update_sensor, 30)


  def update_sensor(self, kwargs):
    self.update_entity("sensor.hacs")
