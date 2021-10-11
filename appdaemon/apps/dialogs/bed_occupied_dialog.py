from yandex_dialog import YandexDialog


class BedOccupiedDialog(YandexDialog):

  def initialize(self):
    self.occupied_ts = 0
    self.dialog_name = "bed_occupied"
    self.dialog_init()
    self.dialog_allowed = True
    entity = "binary_sensor.bedroom_bed_top_occupancy"
    self.listen_state(self.on_bedroom_occupied, entity, new="on", old="off")
    for binary_sensor in self.get_state("binary_sensor"):
      if binary_sensor.endswith("_motion") and ("bedroom_table" in binary_sensor or "bedroom_floor" in binary_sensor):
        self.listen_state(self.on_motion, binary_sensor, new="on", old="off")


  def on_motion(self, entity, attribute, old, new, kwargs):
    self.dialog_allowed = True


  def on_bedroom_occupied(self, entity, attribute, old, new, kwargs):
    if (
      self.sleeping_scene == "day"
      and self.dialog_allowed
      and self.get_delta_ts(self.occupied_ts) > 120
      and self.now_is_between("20:00:00", "10:00:00")
      and self.get_state("sensor.bedroom_yandex_station_connection") == "ok"
    ):
      self.log("Bed was occupied")
      self.dialog_allowed = False
      self.occupied_ts = self.get_now_ts()
      self.volume_set("bedroom_yandex_station", 0.3)
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
    self.set_sleeping_scene("night")
    alarms = self.alarms
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


  @property
  def alarms(self):
    alarms = []
    for person_name in self.get_person_names(with_alarm=True):
      if self.entity_is_on(f"input_boolean.alarm_{person_name}"):
        alarms.append(self.get_state(f"input_datetime.alarm_{person_name}")[:-3])
    return alarms


  def set_alarm(self, str_parsed_time):
    alarm_time = f"{str_parsed_time}:00"
    self.set_time("input_datetime.alarm_andrey", alarm_time)
    self.turn_on_entity("input_boolean.alarm_andrey")
