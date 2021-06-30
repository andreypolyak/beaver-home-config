import appdaemon.plugins.hass.hassapi as hass


class NotifyOsUpdate(hass.Hass):

  def initialize(self):
    self.notifications = self.get_app("notifications")
    self.storage = self.get_app("persistent_storage")
    self.storage.init("notify_os_update.notified_version", None)
    self.listen_state(self.on_core_update, "sensor.os_info", attribute="all", immediate=True)


  def on_core_update(self, entity, attribute, old, new, kwargs):
    updates_info = self.get_state("sensor.os_info", attribute="all")
    notified_version = self.storage.read("notify_os_update.notified_version")
    try:
      new_version = updates_info["attributes"]["newest_version"]
      old_version = updates_info["attributes"]["current_version"]
    except KeyError:
      return
    if new_version == old_version or notified_version == new_version:
      return
    message = self.build_message(new_version, old_version)
    self.notifications.send("admin", message, "os_update", url="/hassio/dashboard")
    self.storage.write("notify_os_update.notified_version", new_version)


  def build_message(self, new_version, old_version):
    message = f"💡 New HA OS version available: {new_version} (current version: {old_version})"
    return message
