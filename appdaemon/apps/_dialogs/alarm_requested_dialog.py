from yandex_dialog import YandexDialog
from datetime import date, datetime, time, timedelta


class AlarmRequestedDialog(YandexDialog):

  def initialize(self):
    self.dialog_name = "alarm_requested"
    self.dialog_init()
    self.persons = self.get_app("persons")
    self.listen_event(self.on_alarm_dialog, "alarm_dialog")


  def on_alarm_dialog(self, event_name, data, kwargs):
    self.log("Alarm dialog was initiated")
    self.start_dialog("initial_alarm")


  def on_yandex_intent(self, event_name, data, kwargs):
    self.log(f"Intent: {data}, mode: {self.step}")
    if self.step == "initial_alarm":
      self.step_initial_alarm(data)
    elif self.step == "alarm_finish":
      self.step_alarm_finish(data)
    else:
      self.cancel_dialog()


  def step_initial_alarm(self, data):
    alarms = self.get_alarms()
    if len(alarms) == 0:
      text = "На какое время установить будильник?"
      self.continue_dialog(text, "alarm_finish")
    elif len(alarms) == 1:
      text = f"Будильник уже установлен на {alarms[0]}!"
      self.finish_dialog(text)
    else:
      text = f"Будильник уже установлен на {alarms[0]} и на {alarms[1]}!"
      self.finish_dialog(text)


  def step_alarm_finish(self, data):
    parsed_time = self.parse_time(data)
    if parsed_time:
      str_parsed_time = parsed_time.strftime("%H:%M")
      text = f"Устанавливаю будильник на {str_parsed_time}. Спокойной ночи!"
      alarm_time = f"{str_parsed_time}:00"
      self.call_service("input_datetime/set_datetime", entity_id="input_datetime.alarm_andrey", time=alarm_time)
      self.call_service("input_boolean/turn_on", entity_id="input_boolean.alarm_andrey")
    else:
      text = "Не удалось разобрать время, установите будильник через приложение. Спокойной ночи!"
    self.finish_dialog(text)


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


  def get_alarms(self):
    alarms = []
    for person_name in self.persons.get_all_person_names(with_alarm=True):
      if self.get_state(f"input_boolean.alarm_{person_name}") == "on":
        alarms.append(self.get_state(f"input_datetime.alarm_{person_name}")[:-3])
    return alarms
