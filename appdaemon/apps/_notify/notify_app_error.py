import appdaemon.plugins.hass.hassapi as hass


class NotifyAppError(hass.Hass):

  def initialize(self):
    self.notifications = self.get_app("notifications")
    self.listen_log(self.on_appdaemon_log, "WARNING")


  def on_appdaemon_log(self, app_name, ts, level, log_type, message, kwargs):
    if "Unable to find module" not in message:
      return
    app_name = message.replace("Unable to find module ", "").replace(" - initialize() skipped", "")
    notification_message = f"🧰 Unable to load {app_name} app"
    self.notifications.send("admin", notification_message, "app_error", url="/hassio/ingress/core_configurator")
