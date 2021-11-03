from base import Base
import html

APPDAEMON_BLACKLIST = [
  "not found in namespace storage",
  " has now completed",
  "initialize() skipped",
  "Invalid callback handle",
  "Found stale callback",
  "Attempt to call Home Assistant while disconnected: call_plugin_service"
]

HA_BLACKLIST = [
  "We found a custom integration ",  # [homeassistant.loader]
  " is taking over 10 seconds.",  # [homeassistant.setup]
  "The bridge Home Assistant Bridge has entity ",  # [homeassistant.components.homekit]
  "has no attribute ",  # [homeassistant.helpers.template] (zigbee2mqtt)
  "UnboundLocalError: local variable \\'controllers\\' referenced before assignment",  # [homeassistant] (sauresha)
  "Can't connect to ESPHome API",  # [homeassistant.components.esphome]
  "Error getting initial data for",  # [homeassistant.components.esphome]
  "Authentication required for Account. (421)",  # [pyicloud.base]
  "Error sending message: Flood control exceeded.",  # [homeassistant.components.telegram_bot]
  "Error sending message: Timed out.",  # [homeassistant.components.telegram_bot]
  "NewConnectionError('<telegram.vendor.ptb_urllib3.urllib3.connection.VerifiedHTTPSConnection",  # [telegram.vendor.ptb_urllib3.urllib3.connectionpool]  # noqa: 501
  "BrokenPipeError: [Errno 32] Broken pipe",  # [aiohttp.server]
  "ConnectionResetError: Cannot write to closing transport",  # [homeassistant]
  "InvalidStateError: The object is in an invalid state.",  # [frontend.js.latest.********]
  "Disconnected: Did not receive auth message within 10 seconds",  # [homeassistant.components.websocket_api.http.connection]  # noqa: 501
  "custom_components.hacs",  # [custom_components.hacs].
  "homeassistant.components.stream.worker",  # [homeassistant.components.stream.worker]
  "Failed to to call /ingress/validate_session -",  # [homeassistant.components.hassio]
  "/ingress/validate_session return code 401",  # [homeassistant.components.hassio.handler]
  "seconds. Please create a bug report at",  # [homeassistant.helpers.entity]
]


class NotifyLogs(Base):

  def initialize(self):
    super().initialize()
    self.listen_log(self.on_appdaemon_log, "WARNING")
    self.listen_event(self.on_ha_log, "system_log_event")
    self.listen_event(self.on_telegram_log, "telegram_log")
    self.listen_event(self.on_zigbee_log, "zigbee_log")


  def on_telegram_log(self, event_name, data, kwargs):
    if "text" in data:
      self.send_to_bot(data["text"])


  def on_appdaemon_log(self, app_name, ts, level, log_type, message, kwargs):
    blacklisted = False
    for item in APPDAEMON_BLACKLIST:
      if item in message:
        blacklisted = True
    if not blacklisted and self.entity_is_on("input_boolean.notify_appdaemon_logs"):
      ts_formatted = ts.strftime("%Y-%m-%D %H:%M:%S.%f")
      message = f"{ts_formatted} {level} {app_name} {message[:1000]}"
      self.send_to_bot(message)


  def on_ha_log(self, event_name, data, kwargs):
    message = str(data)
    blacklisted = False
    for item in HA_BLACKLIST:
      if item in message:
        blacklisted = True
    if not blacklisted and self.entity_is_on("input_boolean.notify_home_assistant_logs"):
      self.send_to_bot(message)


  def on_zigbee_log(self, event_name, data, kwargs):
    message = data["text"]
    if "error" in message and self.entity_is_on("input_boolean.notify_zigbee2mqtt_logs"):
      self.send_to_bot(message)


  def send_to_bot(self, text):
    message = html.escape(text[:3500])
    chat_id = self.args["chat_id"]
    try:
      self.log(f"Send logs to telegram: {message}")
      self.call_service("telegram_bot/send_message", message=message, target=chat_id, disable_notification=True)
    except:
      pass
