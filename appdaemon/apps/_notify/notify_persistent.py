import appdaemon.plugins.hass.hassapi as hass
import re


class NotifyPersistent(hass.Hass):

  def initialize(self):
    self.notifications = self.get_app("notifications")
    notifications = self.get_state("persistent_notification")
    for notification in notifications:
      self.on_existing_notification(notification)
    self.listen_event(self.on_new_notification, "call_service", domain="persistent_notification", service="create")


  def on_new_notification(self, event_name, data, kwargs):
    title = data["service_data"]["title"]
    message = data["service_data"]["message"]
    notification_id = data["service_data"]["notification_id"]
    self.process_notification(title, message, notification_id)


  def on_existing_notification(self, notification):
    notification_state = self.get_state(notification, attribute="all")
    title = notification_state["attributes"]["title"]
    message = notification_state["attributes"]["message"]
    notification_id = notification.split(".")[1]
    self.process_notification(title, message, notification_id)


  def process_notification(self, title, message, notification_id):
    if notification_id in ["homeassistant_check_config", "homeassistant.check_config"]:
      return
    (message, url) = self.parse_message(message)
    text = f"📻 New notification: {title}. {message}"
    self.notifications.send("admin", text, "persistent", url=url)
    self.call_service("persistent_notification/dismiss", notification_id=notification_id)


  def parse_message(self, message):
    urls = re.findall(r"\[(.*?)\]\((.*?)\)", message)
    message = re.sub(r"\[(.*?)\]\((.*?)\)", r"\g<1>", message)
    url = None
    if len(urls) > 0:
      url = urls[0][1]
    return (message, url)
