from base import Base
import mqttapi as mqtt
import json

Z2M_ROOMS = ["entrance", "living_room", "kitchen", "bedroom"]

Z2M_SLUG = "1fd3ccdf"


class NotifyZ2mState(Base, mqtt.Mqtt):

  def initialize(self):
    super().initialize()
    for room in Z2M_ROOMS:
      entity = f"binary_sensor.zigbee2mqtt_{room}_state"
      self.listen_state(self.on_z2m_change, entity, room=room)
      self.mqtt_subscribe(f"zigbee2mqtt_{room}/bridge/log", namespace="mqtt")
      kwargs = {
        "topic": f"zigbee2mqtt_{room}/bridge/log",
        "namespace": "mqtt",
        "room": room
      }
      self.listen_event(self.on_mqtt_change, "MQTT_MESSAGE", **kwargs)


  def on_z2m_change(self, entity, attribute, old, new, kwargs):
    room = kwargs["room"]
    url = f"/hassio/addon/{Z2M_SLUG}_zigbee2mqtt_{room}/logs"
    if new == "on":
      self.on_z2m_on(room, url)
    elif new == "off":
      self.on_z2m_off(room, url)


  def on_mqtt_change(self, event_name, data, kwargs):
    room = kwargs["room"]
    payload = json.loads(data["payload"])
    category = f"zigbee2mqtt_{room}_state"
    url = f"/{Z2M_SLUG}_zigbee2mqtt_{room}"
    if "type" not in payload:
      return
    if payload["type"] == "device_connected":
      self.on_device_connected(payload, category, url)
    elif payload["type"] == "pairing" and payload["message"] == "interview_started":
      self.on_device_pairing_started(payload, category, url)
    elif payload["type"] == "pairing" and payload["message"] == "interview_successful":
      self.on_device_pairing_finished(payload, category, url)
    elif payload["type"] == "device_removed":
      self.on_device_removed(payload, category, url)
    elif payload["type"] == "zigbee_publish_error" and "MEM_ERROR" in payload["message"]:
      self.on_mem_error(payload, category, url, room)
    if "error" in payload["type"]:
      self.fire_event("zigbee_log", text=payload)


  def on_z2m_on(self, room, url):
    name = f"{room} zigbee2mqtt".replace("_", " ").title()
    message = f"📡 {name} was successfully restarted"
    self.send_push("admin", message, "z2m_state", sound="Ladder.caf", url=url)


  def on_z2m_off(self, room, url):
    name = f"{room} zigbee2mqtt".replace("_", " ").title()
    message = f"📡 {name} is down"
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


  def on_mem_error(self, payload, category, url, room):
    message = "👎 Memory error on Zigbee stick. It will be restarted in a second"
    self.send_push("admin", message, category, sound="Ladder.caf", url=url)
    self.turn_on_entity(f"switch.{room}zigbee_gateway_zigbee_restart")
