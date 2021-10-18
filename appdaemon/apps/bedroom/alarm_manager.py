from base import Base
from datetime import timedelta

SNOOZE_MINUTES = 15


class AlarmManager(Base):

  def initialize(self):
    super().initialize()
    self.handles = {}
    for person_name in self.get_person_names(with_alarm=True):
      self.handles[person_name] = None
      self.listen_state(self.on_alarm_time_update, f"input_datetime.alarm_{person_name}")
      self.listen_state(self.on_alarm_on, f"input_boolean.alarm_{person_name}", new="on")
      self.listen_state(self.on_alarm_off, f"input_boolean.alarm_{person_name}", new="off")
      self.update_alarm_time(person_name)
    self.listen_state(self.on_night_scene, "input_select.sleeping_scene", new="night")
    self.listen_state(self.on_day_scene, "input_select.sleeping_scene", new="day", old="night")
    self.listen_event(self.on_finish_alarm, event="mobile_app_notification_action", action="FINISH_ALARM")
    self.listen_event(self.on_finish_alarm, event="custom_event", custom_event_data="finish_alarm")
    self.listen_event(self.on_snooze_alarm, event="custom_event", custom_event_data="snooze_alarm")
    self.listen_event(self.on_snooze_alarm, event="mobile_app_notification_action", action="SNOOZE_ALARM")
    self.run_daily(self.on_evening, "23:00:00")
    for action in ["ALARM_0730", "ALARM_0800", "ALARM_0830", "ALARM_0845", "ALARM_0900", "ALARM_0930"]:
      self.listen_event(self.on_set_alarm_time, event="mobile_app_notification_action", action=action)
    self.allow_snooze_if_alarms_off()


  def on_day_scene(self, entity, attribute, old, new, kwargs):
    self.finish_alarm()


  def finish_alarm(self):
    person_name = self.ringing_alarm_person_name
    if not person_name:
      return
    self.turn_off_entity("input_boolean.alarm_ringing")
    if self.alarms_turned_on_count > 1:
      self.log(f"Activity occured when {person_name.capitalize()}'s alarm was ringing. "
               "Cancelling it because different alarm is turned on")
      self.fire_event("custom_event", custom_event_data=f"cancel_alarm_{person_name}")
    else:
      self.log(f"Activity occured when {person_name.capitalize()}'s alarm was ringing. "
               "Finishing it because no other alarms are turned on")
      self.fire_event("custom_event", custom_event_data=f"finish_alarm_{person_name}")
    self.run_in(self.turn_off_alarm, 1, person_name=person_name)


  def on_alarm_off(self, entity, attribute, old, new, kwargs):
    person_name = self.get_person_names(entity=entity)[0]
    self.log(f"{person_name.capitalize()}'s alarm turned off")
    if self.entity_is_on(f"input_boolean.alarm_{person_name}_ringing"):
      self.log(f"{person_name.capitalize()}'s alarm is ringing and will be cancelled because alarm was turned off")
      self.turn_off_entity("input_boolean.alarm_ringing")
      self.fire_event("custom_event", custom_event_data=f"cancel_alarm_{person_name}")
    self.cancel_handle(self.handles[person_name])
    self.allow_snooze_if_alarms_off()


  def on_alarm_on(self, entity, attribute, old, new, kwargs):
    person_name = self.get_person_names(entity=entity)[0]
    self.log(f"{person_name.capitalize()}'s alarm turned on")
    self.set_alarm_on_time(person_name)


  def on_alarm_time_update(self, entity, attribute, old, new, kwargs):
    person_name = self.get_person_names(entity=entity)[0]
    self.log(f"New time was set for {person_name.capitalize()}'s alarm")
    self.update_alarm_time(person_name)


  def update_alarm_time(self, person_name):
    if self.entity_is_on(f"input_boolean.alarm_{person_name}"):
      if self.entity_is_on(f"input_boolean.alarm_{person_name}_ringing"):
        self.log(f"{person_name.capitalize()}'s alarm is ringing and will be cancelled because new alarm time was set")
        self.turn_off_entity("input_boolean.alarm_ringing")
        self.fire_event("custom_event", custom_event_data=f"cancel_alarm_{person_name}")
      self.set_alarm_on_time(person_name)


  def ring_alarm(self, kwargs):
    person_name = kwargs["person_name"]
    if not self.ringing_alarm_person_name and self.sleeping_scene == "night":
      self.log(f"{person_name.capitalize()}'s alarm is ringing")
      self.turn_on_entity("input_boolean.alarm_ringing")
      self.fire_event("custom_event", custom_event_data=f"start_alarm_{person_name}")
      self.send_ringing_notification(person_name)
    elif self.sleeping_scene != "night":
      self.log(f"{person_name.capitalize()}'s alarm is not ringing because night scene is not turned on")
      self.turn_off_entity(f"input_boolean.alarm_{person_name}")
    else:
      self.log(f"{person_name.capitalize()}'s alarm is not ringing because another alarm is ringing now")
      self.turn_off_entity(f"input_boolean.alarm_{person_name}")


  def send_ringing_notification(self, person_name):
    actions = []
    if self.alarms_turned_on_count > 1:
      actions.append({"action": "FINISH_ALARM", "title": "🌙 Cancel alarm and turn on night mode"})
    else:
      actions.append({"action": "FINISH_ALARM", "title": "☀️ Turn off alarm and turn on day mode"})
    if self.entity_is_on("input_boolean.alarm_snooze_allowed"):
      actions.append({"action": "SNOOZE_ALARM", "title": "😴 Snooze alarm"})
    message = "⏰ Alarm! It's time to wake up"
    self.send_push("home_or_none", message, "alarm", url="/lovelace/bedroom", actions=actions)


  def on_evening(self, kwargs):
    self.send_alarm_setup_notifications()


  def send_alarm_setup_notifications(self):
    for person_name in self.get_person_names(with_alarm=True):
      if self.entity_is_on(f"input_boolean.alarm_{person_name}"):
        continue
      if self.get_state(f"input_select.{person_name}_location") not in ["home", "downstairs"]:
        continue
      actions = [
        {"action": "ALARM_0730", "title": "🕢 07:30"},
        {"action": "ALARM_0800", "title": "🕗 08:00"},
        {"action": "ALARM_0830", "title": "🕣 08:30"},
        {"action": "ALARM_0845", "title": "💩 08:45"},
        {"action": "ALARM_0900", "title": "🕘 09:00"},
        {"action": "ALARM_0930", "title": "🕤 09:30"}
      ]
      message = "⏰ Do you want to turn on alarm?"
      self.send_push(person_name, message, "alarm", url="/lovelace/bedroom", actions=actions)


  def on_set_alarm_time(self, event_name, data, kwargs):
    alarm_time = data["action"][6:8] + ":" + data["action"][-2:] + ":00"
    person_name = data["action_data"]["person_name"]
    self.set_time(f"input_datetime.alarm_{person_name}", alarm_time)
    self.turn_on_entity(f"input_boolean.alarm_{person_name}")


  def on_snooze_alarm(self, event_name, data, kwargs):
    person_name = self.ringing_alarm_person_name
    if person_name:
      self.log("Alarm snoozed")
      alarm_time = self.parse_datetime(self.get_state(f"input_datetime.alarm_{person_name}"), aware=True)
      new_alarm_time = (alarm_time + timedelta(minutes=SNOOZE_MINUTES)).strftime("%H:%M:00")
      self.set_time(f"input_datetime.alarm_{person_name}", new_alarm_time)


  def on_finish_alarm(self, event_name, data, kwargs):
    self.finish_alarm()


  def turn_off_alarm(self, kwargs):
    person_name = kwargs["person_name"]
    self.turn_off_entity(f"input_boolean.alarm_{person_name}")


  def set_alarm_on_time(self, person_name):
    self.log(f"Setting {person_name.capitalize()}'s alarm")
    current_time = self.get_now()
    alarm_time = self.parse_datetime(self.get_state(f"input_datetime.alarm_{person_name}"), aware=True)
    alarm_time = alarm_time - timedelta(minutes=5)
    if (current_time - alarm_time).seconds <= 300:
      self.log("Alarm time is too soon, starting it immediately")
      alarm_time = current_time + timedelta(seconds=10)
    alarm_time = alarm_time.time().replace(microsecond=0)
    self.cancel_handle(self.handles[person_name])
    self.log(f"Setting alarm on {alarm_time}")
    self.handles[person_name] = self.run_once(self.ring_alarm, alarm_time, person_name=person_name)


  def time_to_minutes(self, input_time):
    return input_time.hour * 60 + input_time.minute


  def on_night_scene(self, entity, attribute, old, new, kwargs):
    self.send_alarm_setup_notifications()
    if self.entity_is_on("binary_sensor.bedroom_yandex_station_active"):
      return
    alarms = []
    text = "Спокойной ночи! "
    for person_name in self.get_person_names(with_alarm=True):
      if self.entity_is_on(f"input_boolean.alarm_{person_name}"):
        alarms.append(self.get_state(f"input_datetime.alarm_{person_name}")[:-3])
    if len(alarms) == 0:
      text += "Будильник не установлен!"
    elif len(alarms) == 1:
      text += f"Будильник установлен на {alarms[0]}!"
    else:
      text += f"Будильник установлен на {alarms[0]} и на {alarms[1]}!"
    self.fire_event("yandex_speak_text", text=text, room="bedroom")


  def allow_snooze_if_alarms_off(self):
    all_alarms_off = True
    for person_name in self.get_person_names(with_alarm=True):
      if self.entity_is_on(f"input_boolean.alarm_{person_name}"):
        all_alarms_off = False
    if all_alarms_off:
      self.turn_on_entity("input_boolean.alarm_snooze_allowed")


  @property
  def ringing_alarm_person_name(self):
    ringing = None
    for person_name in self.get_person_names(with_alarm=True):
      if self.entity_is_on(f"input_boolean.alarm_{person_name}_ringing"):
        ringing = person_name
    return ringing


  @property
  def alarms_turned_on_count(self):
    count = 0
    for person_name in self.get_person_names(with_alarm=True):
      if self.entity_is_on(f"input_boolean.alarm_{person_name}"):
        count += 1
    return count
