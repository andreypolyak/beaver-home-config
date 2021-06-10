import appdaemon.plugins.hass.hassapi as hass
import mqttapi as mqtt
import json

Z2M_INSTANCES = [
  {"short_name": "zigbee2mqtt", "url_name": "45df7312_zigbee2mqtt"},
  {"short_name": "zigbee2mqtt_entrance", "url_name": "7c299ebf_zigbee2mqtt_entrance"},
  {"short_name": "zigbee2mqtt_switches", "url_name": "7c299ebf_zigbee2mqtt_switches"},
  {"short_name": "zigbee2mqtt_bedroom", "url_name": "7c299ebf_zigbee2mqtt_bedroom"}
]

ZIGBEE_PI_RESTART_COMMANDS = ["restart_rpi_living_room", "restart_rpi_entrance", "restart_rpi_bedroom"]


class NotifyZ2mState(hass.Hass, mqtt.Mqtt):

  def initialize(self):
    self.persons = self.get_app("persons")
    for z2m_instance in Z2M_INSTANCES:
      short_name = z2m_instance["short_name"]
      url_name = z2m_instance["url_name"]
      entity = f"binary_sensor.{short_name}_state"
      self.listen_state(self.on_z2m_change, entity, short_name=short_name, url_name=url_name)
      self.mqtt_subscribe(f"{short_name}/bridge/log", namespace="mqtt")
      topic = f"{short_name}/bridge/log"
      self.listen_event(self.on_mqtt_change, "MQTT_MESSAGE", topic=topic, namespace="mqtt",
                        short_name=short_name, url_name=url_name)
    self.listen_event(self.on_pi_restart, event="mobile_app_notification_action", action="PI_RESTART")


  def on_z2m_change(self, entity, attribute, old, new, kwargs):
    full_name = kwargs["short_name"].replace("_", " ").title()
    url_name = kwargs["url_name"]
    url = f"/hassio/addon/{url_name}/logs"
    if new == "on":
      self.persons.send_notification("admin", f"📡 {full_name} was successfully restarted", "z2m_state", url=url)
    elif new == "off":
      self.persons.send_notification("admin", f"📡 {full_name} is down", "z2m_state", url=url)


  def on_mqtt_change(self, event_name, data, kwargs):
    short_name = kwargs["short_name"]
    url_name = kwargs["url_name"]
    message = json.loads(data["payload"])
    category = f"{short_name}_state"
    url = f"/{url_name}"
    if "type" not in message:
      return
    if message["type"] == "device_connected":
      friendly_name = message["message"]["friendly_name"]
      self.persons.send_notification("admin", f"📡 New Zigbee device found: {friendly_name}", category, url=url)
    elif message["type"] == "pairing":
      friendly_name = message["meta"]["friendly_name"]
      if message["message"] == "interview_started":
        self.persons.send_notification("admin", f"📡 Pairing new Zigbee device: {friendly_name}", category, url=url)
      elif message["message"] == "interview_successful":
        if "description" in message["meta"]:
          description = message["meta"]["description"]
          description = f" ({description})"
        else:
          description = ""
        text = f"📡 Successfully paired new Zigbee device: {friendly_name}{description}"
        self.persons.send_notification("admin", text, category, url=url)
    elif message["type"] == "device_removed":
      friendly_name = message["meta"]["friendly_name"]
      self.persons.send_notification("admin", f"📡 Zigbee device left the network: {friendly_name}", category, url=url)
    elif message["type"] == "zigbee_publish_error" and "MEM_ERROR" in message["message"]:
      actions = [{"action": "PI_RESTART", "title": "📌 Restart Zigbee Pis", "destructive": True}]
      self.persons.send_notification("admin", "👎 Memory error on Zigbee stick. Do you want to restart Zigbee Pis?",
                                     "z2m_error", sound="Aurora.caf", actions=actions)
    if "error" in message["type"]:
      self.fire_event("zigbee_log", text=message)


  def on_pi_restart(self, event_name, data, kwargs):
    for restart_command in ZIGBEE_PI_RESTART_COMMANDS:
      self.call_service(f"shell_command/{restart_command}")
