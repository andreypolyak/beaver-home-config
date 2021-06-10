import appdaemon.plugins.hass.hassapi as hass


class NotifyOsUpdate(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    self.storage = self.get_app("persistent_storage")
    self.storage.init("notify_os_update.notified_version", None)
    self.listen_state(self.on_core_update, "sensor.os_info", attribute="all")
    self.check_updates()


  def on_core_update(self, entity, attribute, old, new, kwargs):
    self.check_updates()


  def check_updates(self):
    updates_info = self.get_state("sensor.os_info", attribute="all")
    notified_version = self.storage.read("notify_os_update.notified_version")
    new_version = updates_info["attributes"]["newest_version"]
    old_version = updates_info["attributes"]["current_version"]
    if new_version == old_version or notified_version == new_version:
      return
    message = self.build_message(new_version, old_version)
    self.persons.send_notification("admin", message, "os_update", url="/hassio/dashboard")
    self.storage.write("notify_os_update.notified_version", new_version)


  def build_message(self, new_version, old_version):
    message = f"💡 New HA OS version available: {new_version} (current version: {old_version})"
    return message
