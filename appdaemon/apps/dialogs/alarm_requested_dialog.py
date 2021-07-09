from yandex_dialog import YandexDialog


class AlarmRequestedDialog(YandexDialog):

  def initialize(self):
    self.dialog_name = "alarm_requested"
    self.dialog_init()
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
      self.set_time("input_datetime.alarm_andrey", alarm_time)
      self.turn_on_entity("input_boolean.alarm_andrey")
    else:
      text = "Не удалось разобрать время, установите будильник через приложение. Спокойной ночи!"
    self.finish_dialog(text)


  def get_alarms(self):
    alarms = []
    for person_name in self.get_all_person_names(with_alarm=True):
      if self.is_entity_on(f"input_boolean.alarm_{person_name}"):
        alarms.append(self.get_state(f"input_datetime.alarm_{person_name}")[:-3])
    return alarms
