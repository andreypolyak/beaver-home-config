from yandex_dialog import YandexDialog


class AlarmRequestedDialog(YandexDialog):

  def initialize(self):
    self.dialog_name = "alarm_requested"
    self.activation_phrase = "Будильник"
    self.dialog_init()
    self.listen_event(self.on_alarm_dialog, "alarm_dialog")


  def on_alarm_dialog(self, event_name, data, kwargs):
    self.log("Alarm dialog was initiated")
    self.start_dialog()


  def on_yandex_intent(self, event_name, data, kwargs):
    self.log(f"Intent: {data}, mode: {self.step}")
    if self.step == "initial":
      self.step_initial_alarm(data)
    elif self.step == "alarm_finish":
      self.step_alarm_finish(data)
    elif self.step == "night_mode":
      self.step_night_mode(data)
    else:
      self.cancel_dialog()


  def step_initial_alarm(self, data):
    alarms = self.alarms
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
      text = f"Устанавливаю будильник на {str_parsed_time}. Вы хотите включить ночной режим?"
      alarm_time = f"{str_parsed_time}:00"
      self.set_time("input_datetime.alarm_andrey", alarm_time)
      self.turn_on_entity("input_boolean.alarm_andrey")
    else:
      text = "Не удалось разобрать время, установите будильник через приложение."
    self.continue_dialog(text, "night_mode")


  def step_night_mode(self, data):
    nlu = data["data"]["nlu"]
    if "YANDEX.CONFIRM" not in nlu["intents"]:
      self.cancel_dialog()
      return
    self.set_sleeping_scene("night")
    text = "Включаю ночной режим! Спокойной ночи!"
    self.finish_dialog(text)


  @property
  def alarms(self):
    alarms = []
    for person_name in self.get_person_names(with_alarm=True):
      if self.entity_is_on(f"input_boolean.alarm_{person_name}"):
        alarms.append(self.get_state(f"input_datetime.alarm_{person_name}")[:-3])
    return alarms
