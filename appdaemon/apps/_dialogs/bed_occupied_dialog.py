from yandex_dialog import YandexDialog
from datetime import date, datetime, time, timedelta


class BedOccupiedDialog(YandexDialog):

  def initialize(self):
    self.occupied_ts = 0
    self.dialog_name = "bed_occupied"
    self.dialog_init()
    self.persons = self.get_app("persons")
    self.dialog_allowed = True
    self.listen_state(self.on_bedroom_occupied, "binary_sensor.bedroom_bed_occupancy", new="on", old="off")
    binary_sensors = self.get_state("binary_sensor")
    for binary_sensor in binary_sensors:
      if binary_sensor.endswith("_motion") and ("bedroom_table" in binary_sensor or "bedroom_floor" in binary_sensor):
        self.listen_state(self.on_motion, binary_sensor, new="on", old="off")


  def on_motion(self, entity, attribute, old, new, kwargs):
    self.dialog_allowed = True


  def on_bedroom_occupied(self, entity, attribute, old, new, kwargs):
    sleeping_scene = self.get_state("input_select.sleeping_scene")
    if (
      sleeping_scene == "day"
      and self.dialog_allowed
      and (self.get_now_ts() - self.occupied_ts) > 120
      and self.now_is_between("20:00:00", "10:00:00")
    ):
      self.log("Bed was occupied")
      self.dialog_allowed = False
      self.occupied_ts = self.get_now_ts()
      self.call_service("media_player/volume_set", entity_id="media_player.bedroom_yandex_station", volume_level=0.3)
      self.start_dialog("night_mode", room="bedroom")


  def on_yandex_intent(self, event_name, data, kwargs):
    self.log(f"Intent: {data}, mode: {self.step}")
    if self.step == "night_mode":
      self.step_night_mode(data)
    elif self.step == "alarm_turn_on":
      self.step_alarm_question(data)
    elif self.step == "alarm_time":
      self.step_alarm_time(data)
    elif self.step == "alarm_finish":
      self.step_alarm_finish(data)
    else:
      self.cancel_dialog()


  def step_night_mode(self, data):
    text = "Вы хотите включить ночной режим?"
    self.continue_dialog(text, "alarm_turn_on")


  def step_alarm_question(self, data):
    nlu = data["data"]["nlu"]
    if "YANDEX.CONFIRM" not in nlu["intents"]:
      self.cancel_dialog()
      return
    self.call_service("input_select/select_option", entity_id="input_select.sleeping_scene", option="night")
    alarms = self.get_alarms()
    if len(alarms) == 0:
      text = "Включаю ночной режим! Вы хотите установить будильник?"
      self.continue_dialog(text, "alarm_time")
    elif len(alarms) == 1:
      text = f"Включаю ночной режим! Будильник установлен на {alarms[0]}! Спокойной ночи!"
      self.finish_dialog(text)
    else:
      text = f"Включаю ночной режим! Будильник установлен на {alarms[0]} и на {alarms[1]}! Спокойной ночи!"
      self.finish_dialog(text)


  def step_alarm_time(self, data):
    nlu = data["data"]["nlu"]
    parsed_time = self.parse_time(data)
    if parsed_time:
      str_parsed_time = parsed_time.strftime("%H:%M")
      text = f"Устанавливаю будильник на {str_parsed_time}. Спокойной ночи!"
      self.set_alarm(str_parsed_time)
      self.finish_dialog(text)
    elif "YANDEX.CONFIRM" in nlu["intents"]:
      text = "На какое время установить будильник?"
      self.continue_dialog(text, "alarm_finish")
    elif "YANDEX.REJECT" in nlu["intents"]:
      self.cancel_dialog()
    else:
      text = "Не удалось разобрать время, установите будильник через приложение. Спокойной ночи!"
      self.finish_dialog(text)


  def step_alarm_finish(self, data):
    parsed_time = self.parse_time(data)
    if parsed_time:
      str_parsed_time = parsed_time.strftime("%H:%M")
      text = f"Устанавливаю будильник на {str_parsed_time}. Спокойной ночи!"
      self.set_alarm(str_parsed_time)
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
    for person_name in self.persons.get_all_person_names():
      entity = f"input_boolean.alarm_{person_name}"
      if self.entity_exists(entity) and self.get_state(entity) == "on":
        alarms.append(self.get_state(f"input_datetime.alarm_{person_name}")[:-3])
    return alarms


  def set_alarm(self, str_parsed_time):
    alarm_time = f"{str_parsed_time}:00"
    self.call_service("input_datetime/set_datetime", entity_id="input_datetime.alarm_andrey", time=alarm_time)
    self.call_service("input_boolean/turn_on", entity_id="input_boolean.alarm_andrey")
