import appdaemon.plugins.hass.hassapi as hass
import html

APPDAEMON_BLACKLIST = [
  "not found in namespace persistent_storage",
  " has now completed",
  "initialize() skipped",
  "Invalid callback handle"
]

HA_BLACKLIST = [
  "evaluating 't._leaflet_pos'",
  "Error getting new camera image from",
  "telegram",
  "swipe-navigation",
  "socket.send() raised exception.",
  "components/stream",
  "components/generic/camera",
  "image_processing",
  "Could not find data in region",
  "Disconnected: Did not receive auth message within 10 seconds",
  "Update of switch.living_room_christmas_tree is taking over 10 seconds",
  "Repository is archived",
  "PS4 could not be reached",
  "GitHub Ratelimit error",
  "mset?motor_speed",
  "using 'value_template' for 'position_topic'",
  "Authentication required for Account. (421)",
  "Updating androidtv media_player took longer than the scheduled update interval",
  "Client unable to keep up with pending messages.",
  "BrokenPipeError",
  "ConnectionResetError",
  "Template variable warning: 'dict object' has no attribute",
  "Flood control exceeded.",
  "Erroneous JSON",
  "Template variable error: 'value_json' is undefined",
  "Error parsing value: 'value_json' is undefined",
  "Can't connect to ESPHome API",
  "GitHub returned 502 for",
  "MosenergosbytException",
  "Update of sensor.mes_",
  "Connection reset by peer",
  "Broken pipe",
  "/ingress/validate_session return code 401",
  "Failed to to call /ingress/validate_session - ",
  "Timeout while waiting for API response!",
  "Disconnected from Broadlink",
  "Connected to Broadlink",
  "Error fetching Broadlink",
  "We found a custom integration",
  "GitHub returned 404 for https://api.github.com/repos",
  ":0:0 Script error.",
  "Timeout call http://192.168.1.78:8080/start",
  "Cannot connect to host quasar.yandex.ru",
  "TypeError: forward_push_notification()",
  "Error sending notification to https://mobile-apps.home-assistant.io/api/sendPushNotification: "
]


class NotifyLogs(hass.Hass):

  def initialize(self):
    self.listen_log(self.on_appdaemon_log, "WARNING")
    self.listen_event(self.on_ha_log, "system_log_event")
    self.listen_event(self.on_telegram_log, "telegram_log")
    self.listen_event(self.on_zigbee_log, "zigbee_log")


  def on_telegram_log(self, event_name, data, kwargs):
    if "text" in data:
      self.send_to_bot(data["text"])


  def on_appdaemon_log(self, app_name, ts, level, log_type, message, kwargs):
    is_banned = False
    for item in APPDAEMON_BLACKLIST:
      if item in message:
        is_banned = True
    if not is_banned and self.get_state("input_boolean.log_ad") == "on":
      ts_formatted = ts.strftime("%Y-%m-%D %H:%M:%S.%f")
      message = f"{ts_formatted} {level} {app_name} {message[:1000]}"
      self.send_to_bot(message)


  def on_ha_log(self, event_name, data, kwargs):
    message = str(data)
    is_banned = False
    for item in HA_BLACKLIST:
      if item in message:
        is_banned = True
    if not is_banned and self.get_state("input_boolean.log_ha") == "on":
      self.send_to_bot(message)


  def on_zigbee_log(self, event_name, data, kwargs):
    message = data["text"]
    if "error" in message and self.get_state("input_boolean.log_z2m") == "on":
      self.send_to_bot(message)


  def send_to_bot(self, text):
    message = html.escape(text[:3500])
    chat_id = self.args["chat_id"]
    self.call_service("telegram_bot/send_message", message=message, target=chat_id, disable_notification=True)
