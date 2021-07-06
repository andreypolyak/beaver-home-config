import appdaemon.plugins.hass.hassapi as hass
import mqttapi as mqtt
import json

Z2M_INSTANCES = [
  {"short_name": "zigbee2mqtt", "url_name": "45df7312_zigbee2mqtt"},
  {"short_name": "zigbee2mqtt_entrance", "url_name": "1fd3ccdf_zigbee2mqtt_entrance"},
  {"short_name": "zigbee2mqtt_switches", "url_name": "1fd3ccdf_zigbee2mqtt_switches"},
  {"short_name": "zigbee2mqtt_bedroom", "url_name": "1fd3ccdf_zigbee2mqtt_bedroom"}
]

ZIGBEE_PI_RESTART_COMMANDS = ["restart_rpi_living_room", "restart_rpi_entrance", "restart_rpi_bedroom"]


class NotifyZ2mState(hass.Hass, mqtt.Mqtt):

  def initialize(self):
    self.notifications = self.get_app("notifications")
    for z2m_instance in Z2M_INSTANCES:
      short_name = z2m_instance["short_name"]
      url_name = z2m_instance["url_name"]
      entity = f"binary_sensor.{short_name}_state"
      self.listen_state(self.on_z2m_change, entity, short_name=short_name, url_name=url_name)
      self.mqtt_subscribe(f"{short_name}/bridge/log", namespace="mqtt")
      topic = f"{short_name}/bridge/log"
      kwargs = {
        "topic": topic,
        "namespace": "mqtt",
        "short_name": short_name,
        "url_name": url_name
      }
      self.listen_event(self.on_mqtt_change, "MQTT_MESSAGE", **kwargs)
    self.listen_event(self.on_pi_restart, event="mobile_app_notification_action", action="PI_RESTART")


  def on_z2m_change(self, entity, attribute, old, new, kwargs):
    full_name = kwargs["short_name"].replace("_", " ").title()
    url_name = kwargs["url_name"]
    url = f"/hassio/addon/{url_name}/logs"
    if new == "on":
      message = f"📡 {full_name} was successfully restarted"
      self.notifications.send("admin", message, "z2m_state", sound="Ladder.caf", url=url)
    elif new == "off":
      message = f"📡 {full_name} is down"
      self.notifications.send("admin", message, "z2m_state", sound="Ladder.caf", url=url)


  def on_mqtt_change(self, event_name, data, kwargs):
    short_name = kwargs["short_name"]
    url_name = kwargs["url_name"]
    payload = json.loads(data["payload"])
    category = f"{short_name}_state"
    url = f"/{url_name}"
    if "type" not in payload:
      return
    if payload["type"] == "device_connected":
      friendly_name = payload["message"]["friendly_name"]
      message = f"📡 New Zigbee device found: {friendly_name}"
      self.notifications.send("admin", message, category, sound="Ladder.caf", url=url)
    elif payload["type"] == "pairing":
      friendly_name = payload["meta"]["friendly_name"]
      if payload["message"] == "interview_started":
        message = f"📡 Pairing new Zigbee device: {friendly_name}"
        self.notifications.send("admin", message, category, sound="Ladder.caf", url=url)
      elif payload["message"] == "interview_successful":
        if "description" in payload["meta"]:
          description = payload["meta"]["description"]
          description = f" ({description})"
        else:
          description = ""
        message = f"📡 Successfully paired new Zigbee device: {friendly_name}{description}"
        self.notifications.send("admin", message, category, sound="Ladder.caf", url=url)
    elif payload["type"] == "device_removed":
      friendly_name = payload["meta"]["friendly_name"]
      message = f"📡 Zigbee device left the network: {friendly_name}"
      self.notifications.send("admin", message, category, sound="Ladder.caf", url=url)
    elif payload["type"] == "zigbee_publish_error" and "MEM_ERROR" in payload["message"]:
      actions = [{"action": "PI_RESTART", "title": "📌 Restart Zigbee Pis", "destructive": True}]
      message = "👎 Memory error on Zigbee stick. Do you want to restart Zigbee Pis?"
      self.notifications.send("admin", message, "z2m_error", sound="Ladder.caf", actions=actions)
    if "error" in payload["type"]:
      self.fire_event("zigbee_log", text=payload)


  def on_pi_restart(self, event_name, data, kwargs):
    for restart_command in ZIGBEE_PI_RESTART_COMMANDS:
      self.call_service(f"shell_command/{restart_command}")
