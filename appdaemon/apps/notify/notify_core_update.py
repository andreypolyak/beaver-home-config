from base import Base


class NotifyCoreUpdate(Base):

  def initialize(self):
    super().initialize()
    self.init_storage("notify_core_update", "notified_version", None)
    self.listen_state(self.on_core_update, "sensor.ha_info", attribute="all", immediate=True)


  def on_core_update(self, entity, attribute, old, new, kwargs):
    updates_info = self.get_state("sensor.ha_info", attribute="all")
    notified_version = self.read_storage("notified_version")
    try:
      new_version = updates_info["attributes"]["newest_version"]
      old_version = updates_info["attributes"]["current_version"]
    except KeyError:
      return
    if new_version == old_version or notified_version == new_version:
      return
    message = self.build_message(new_version, old_version)
    self.send_push("admin", message, "core_update", url="/hassio/dashboard")
    self.write_storage("notified_version", new_version)


  def build_message(self, new_version, old_version):
    message = f"💡 New HA Core version available: {new_version} (current version: {old_version})"
    return message
