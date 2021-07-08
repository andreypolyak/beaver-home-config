from base import Base


class NotifyRestart(Base):

  def initialize(self):
    super().initialize()
    self.turn_on_entity("input_boolean.ad_running")
    message = "🤖 AppDaemon was successfully restarted"
    self.send_push("admin", message, "appdaemon_restart", url="/hassio/addon/a0d7b954_appdaemon/logs")
    entity = "persistent_notification.homeassistant_check_config"
    self.listen_event(self.on_notification, event="state_changed", entity_id=entity)


  def on_notification(self, event_name, data, kwargs):
    if data["new_state"]["state"] == "notifying":
      message = "😞 Incorrect config, can't restart Home Assistant"
      self.send_push("admin", message, "ha_config_error", url="/config/logs")
      self.call_service("persistent_notification/dismiss", notification_id="homeassistant_check_config")
