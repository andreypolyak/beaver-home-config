import appdaemon.plugins.hass.hassapi as hass


class NotifyRestart(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    self.persons.send_notification("admin", "🤖 AppDaemon was successfully restarted", "appdaemon_restart",
                                   url="/hassio/addon/a0d7b954_appdaemon/logs")
    self.call_service("input_boolean/turn_on", entity_id="input_boolean.appdaemon_running")
    self.listen_event(self.on_notification, event="state_changed",
                      entity_id="persistent_notification.homeassistant_check_config")


  def on_notification(self, event_name, data, kwargs):
    if data["new_state"]["state"] == "notifying":
      self.persons.send_notification("admin", "😞 Incorrect config, can't restart Home Assistant",
                                     "ha_config_error", url="/config/logs")
      self.call_service("persistent_notification/dismiss", notification_id="homeassistant_check_config")
