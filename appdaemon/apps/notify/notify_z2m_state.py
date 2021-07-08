from base import Base
import mqttapi as mqtt
import json

Z2M_INSTANCES = [
  {"short_name": "zigbee2mqtt", "url_name": "45df7312_zigbee2mqtt"},
  {"short_name": "zigbee2mqtt_entrance", "url_name": "1fd3ccdf_zigbee2mqtt_entrance"},
  {"short_name": "zigbee2mqtt_switches", "url_name": "1fd3ccdf_zigbee2mqtt_switches"},
  {"short_name": "zigbee2mqtt_bedroom", "url_name": "1fd3ccdf_zigbee2mqtt_bedroom"}
]

ZIGBEE_PI_RESTART_COMMANDS = ["restart_rpi_living_room", "restart_rpi_entrance", "restart_rpi_bedroom"]


class NotifyZ2mState(Base, mqtt.Mqtt):

  def initialize(self):
    super().initialize()
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
      self.on_z2m_on(full_name, url)
    elif new == "off":
      self.on_z2m_off(full_name, url)


  def on_mqtt_change(self, event_name, data, kwargs):
    short_name = kwargs["short_name"]
    url_name = kwargs["url_name"]
    payload = json.loads(data["payload"])
    category = f"{short_name}_state"
    url = f"/{url_name}"
    if "type" not in payload:
      return
    if payload["type"] == "device_connected":
      self.on_device_connected(payload, category, url)
    elif payload["type"] == "pairing" and payload["message"] == "interview_started":
      self.on_device_pairing_started(payload, category, url)
    elif payload["type"] == "pairing" and "interview_successful":
      self.on_device_pairing_finished(payload, category, url)
    elif payload["type"] == "device_removed":
      self.on_device_removed(payload, category, url)
    elif payload["type"] == "zigbee_publish_error" and "MEM_ERROR" in payload["message"]:
      self.on_mem_error(payload, category, url)
    if "error" in payload["type"]:
      self.fire_event("zigbee_log", text=payload)


  def on_z2m_on(self, full_name, url):
    message = f"📡 {full_name} was successfully restarted"
    self.send_push("admin", message, "z2m_state", sound="Ladder.caf", url=url)


  def on_z2m_off(self, full_name, url):
    message = f"📡 {full_name} is down"
    self.send_push("admin", message, "z2m_state", sound="Ladder.caf", url=url)


  def on_device_connected(self, payload, category, url):
    friendly_name = payload["message"]["friendly_name"]
    message = f"📡 New Zigbee device found: {friendly_name}"
    self.send_push("admin", message, category, sound="Ladder.caf", url=url)


  def on_device_pairing_started(self, payload, category, url):
    friendly_name = payload["meta"]["friendly_name"]
    message = f"📡 Pairing new Zigbee device: {friendly_name}"
    self.send_push("admin", message, category, sound="Ladder.caf", url=url)


  def on_device_pairing_finished(self, payload, category, url):
    friendly_name = payload["meta"]["friendly_name"]
    description = ""
    if "description" in payload["meta"]:
      description = payload["meta"]["description"]
      description = f" ({description})"
    message = f"📡 Successfully paired new Zigbee device: {friendly_name}{description}"
    self.send_push("admin", message, category, sound="Ladder.caf", url=url)


  def on_device_removed(self, payload, category, url):
    friendly_name = payload["meta"]["friendly_name"]
    message = f"📡 Zigbee device left the network: {friendly_name}"
    self.send_push("admin", message, category, sound="Ladder.caf", url=url)


  def on_mem_error(self, payload, category, url):
    actions = [{"action": "PI_RESTART", "title": "📌 Restart Zigbee Pis", "destructive": True}]
    message = "👎 Memory error on Zigbee stick. Do you want to restart Zigbee Pis?"
    self.send_push("admin", message, category, sound="Ladder.caf", actions=actions, url=url)


  def on_pi_restart(self, event_name, data, kwargs):
    for restart_command in ZIGBEE_PI_RESTART_COMMANDS:
      self.call_service(f"shell_command/{restart_command}")
