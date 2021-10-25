from base import Base
from datetime import date, datetime, time, timedelta

ACTIVATION_COMMAND = "Скажи Афоне арбуз"


class YandexDialog(Base):

  def dialog_init(self):
    super().initialize()
    self.run_ts = 0
    self.step = None
    self.set_inactive_dialog()
    self.room = None
    self.listen_event(self.on_yandex_intent, self.dialog_name)
    self.listen_event(self.on_yandex_speaker_event, "yandex_speaker")


  def on_yandex_speaker_event(self, event_name, data, kwargs):
    if "value" in data and data["value"] == self.activation_phrase:
      room = data["entity_id"].replace("media_player.", "").replace("_yandex_station", "")
      self.start_dialog(room=room)


  def start_dialog(self, room=None):
    if self.get_delta_ts(self.run_ts) <= 5:
      return
    self.run_ts = self.get_now_ts()
    self.step = "initial"
    if room:
      self.select_option("last_active_yandex_station", room)
      self.room = room
    else:
      self.room = self.get_state("input_select.last_active_yandex_station")
    self.set_active_dialog()
    data = {
      "media_entity_id": f"media_player.{self.room}_yandex_station",
      "media_content_id": ACTIVATION_COMMAND,
      "media_content_type": "command"
    }
    self.call_service("script/turn_on", entity_id="script.yandex_play_media", variables=data)


  def continue_dialog(self, text, step):
    self.fire_event("yandex_intent_response", text=text, end_session=False)
    self.step = step


  def finish_dialog(self, text):
    self.fire_event("yandex_intent_response", text=text, end_session=True)
    self.set_inactive_dialog()
    self.step = None
    self.room = None


  def cancel_dialog(self):
    self.log("Cancelling dialog")
    self.fire_event("yandex_intent_response", text="", end_session=True)
    self.turn_off_entity(f"media_player.{self.room}_yandex_station")
    self.set_inactive_dialog()
    self.step = None
    self.room = None


  def set_active_dialog(self):
    self.set_value("input_text.active_dialog", self.dialog_name)


  def set_inactive_dialog(self):
    self.set_value("input_text.active_dialog", "")


  def parse_time(self, data):
    nlu = data["data"]["nlu"]
    entities = nlu["entities"]
    for entity in entities:
      if (
        entity["type"] == "YANDEX.DATETIME"
        and ("hour_is_relative" not in entity["value"] or entity["value"]["hour_is_relative"] is False)
        and ("minute_is_relative" not in entity["value"] or entity["value"]["minute_is_relative"] is False)
      ):
        if "minute" in entity["value"] and "hour" in entity["value"]:
          hour = entity["value"]["hour"]
          minute = entity["value"]["minute"]
          return datetime.combine(date.today(), time(hour, minute))
        elif "hour" in entity["value"]:
          hour = entity["value"]["hour"]
          return datetime.combine(date.today(), time(hour, 0))
    tokens = nlu["tokens"]
    delta = 0
    if len(tokens) > 0 and tokens[0] == "пол":
      delta = 30
    numbers = []
    for token in tokens:
      if token.isnumeric():
        numbers.append(int(token))
    if len(numbers) == 1 and numbers[0] >= 0 and numbers[0] <= 23:
      hour = numbers[0]
      return datetime.combine(date.today(), time(hour, 0)) - timedelta(minutes=delta)
    elif len(numbers) == 2 and numbers[0] >= 0 and numbers[0] <= 23 and numbers[1] >= 0 and numbers[1] <= 59:
      hour = numbers[0]
      minute = numbers[1]
      return datetime.combine(date.today(), time(hour, minute)) - timedelta(minutes=delta)
    elif len(numbers) == 3 and numbers[0] >= 0 and numbers[0] <= 23 and numbers[1] == 0 and numbers[2] == 0:
      return datetime.combine(date.today(), time(hour, 0)) - timedelta(minutes=delta)
    return None
