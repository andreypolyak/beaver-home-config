import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime, date, timedelta


class AlarmManager(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    self.alarm_handlers = {}
    for person_name in self.persons.get_all_person_names(with_alarm=True):
      self.alarm_handlers[person_name] = None
      self.listen_state(self.on_alarm_time_update, f"input_datetime.alarm_{person_name}")
      self.listen_state(self.on_alarm_on, f"input_boolean.alarm_{person_name}", new="on")
      self.listen_state(self.on_alarm_off, f"input_boolean.alarm_{person_name}", new="off")
      self.update_alarm_time(person_name)

    self.sleeping_zone_motion_ts = 0
    binary_sensors = self.get_state("binary_sensor")
    for binary_sensor in binary_sensors:
      if not binary_sensor.endswith("_motion"):
        continue
      if "bedroom_floor" in binary_sensor or "bedroom_table" in binary_sensor:
        self.listen_state(self.on_sleeping_zone_motion, binary_sensor, new="on", old="off")
      elif "bedroom_door" in binary_sensor:
        self.listen_state(self.on_bedroom_door_open, binary_sensor, new="on", old="off")
      elif "kitchen" in binary_sensor or "living_room" in binary_sensor:
        self.listen_state(self.on_living_zone_motion, binary_sensor, new="on", old="off")

    self.listen_event(self.snooze_alarm, event="custom_event", custom_event_data="snooze_alarm")
    self.listen_state(self.on_night_scene, "input_select.sleeping_scene", new="night")
    self.allow_snooze_if_alarms_off()


  def on_sleeping_zone_motion(self, entity, attribute, old, new, kwargs):
    self.sleeping_zone_motion_ts = self.get_now_ts()


  def on_bedroom_door_open(self, entity, attribute, old, new, kwargs):
    self.motion_occured()


  def on_living_zone_motion(self, entity, attribute, old, new, kwargs):
    if (self.get_now_ts() - self.sleeping_zone_motion_ts) < 60 and self.get_state("binary_sensor.bedroom_door") == "on":
      self.motion_occured()


  def motion_occured(self):
    person_name = self.get_person_name_alarm_ringing()
    if not person_name:
      return
    other_alarms_turned_on = False
    for other_person_name in self.persons.get_all_person_names_except_provided(person_name, with_alarm=True):
      self.call_service("input_boolean/turn_off", entity_id="input_boolean.alarm_ringing")
      if self.get_state(f"input_boolean.alarm_{other_person_name}") == "on":
        other_alarms_turned_on = True
    if other_alarms_turned_on:
      self.log(f"Motion occured when {person_name.capitalize()}'s alarm was ringing."
               "Cancelling it because different alarm is turned on")
      self.fire_event("custom_event", custom_event_data=f"cancel_alarm_{person_name}")
    else:
      self.log(f"Motion occured when {person_name.capitalize()}'s alarm was ringing."
               "Finishing it because no other alarms are turned on")
      self.fire_event("custom_event", custom_event_data=f"finish_alarm_{person_name}")
    self.run_in(self.turn_off_alarm, 1, person_name=person_name)


  def on_alarm_off(self, entity, attribute, old, new, kwargs):
    person_name = self.persons.get_person_name_from_entity_name(entity)
    self.log(person_name.capitalize() + "'s alarm turned off")
    if self.is_alarm_ringing(person_name):
      self.log(person_name.capitalize() + "'s alarm is ringing and will be cancelled because alarm was turned off")
      self.call_service("input_boolean/turn_off", entity_id="input_boolean.alarm_ringing")
      self.fire_event("custom_event", custom_event_data=f"cancel_alarm_{person_name}")
    self.cancel_alarm_handler(person_name)
    self.allow_snooze_if_alarms_off()


  def on_alarm_on(self, entity, attribute, old, new, kwargs):
    if self.get_state("input_select.sleeping_scene") != "night":
      self.call_service("input_select/select_option", entity_id="input_select.sleeping_scene", option="night")
    person_name = self.persons.get_person_name_from_entity_name(entity)
    self.log(person_name.capitalize() + "'s alarm turned on")
    self.set_alarm_on_time(person_name)


  def on_alarm_time_update(self, entity, attribute, old, new, kwargs):
    person_name = self.persons.get_person_name_from_entity_name(entity)
    self.log(f"New time was set for {person_name.capitalize()}'s alarm")
    self.update_alarm_time(person_name)


  def update_alarm_time(self, person_name):
    if self.get_state(f"input_boolean.alarm_{person_name}") == "on":
      if self.is_alarm_ringing(person_name):
        self.log(person_name.capitalize() + "'s alarm is ringing and will be cancelled because new alarm time was set")
        self.call_service("input_boolean/turn_off", entity_id="input_boolean.alarm_ringing")
        self.fire_event("custom_event", custom_event_data=f"cancel_alarm_{person_name}")
      self.set_alarm_on_time(person_name)


  def ring_alarm(self, kwargs):
    person_name = kwargs["person_name"]
    is_night_scene = self.get_state("input_select.sleeping_scene") == "night"
    if not self.get_person_name_alarm_ringing() and is_night_scene:
      self.log(person_name.capitalize() + "'s alarm is ringing")
      self.call_service("input_boolean/turn_on", entity_id="input_boolean.alarm_ringing")
      self.fire_event("custom_event", custom_event_data=f"start_alarm_{person_name}")
    elif not is_night_scene:
      self.log(person_name.capitalize() + "'s alarm is not ringing because night scene is not turned on")
      self.call_service("input_boolean/turn_off", entity_id=f"input_boolean.alarm_{person_name}")
    else:
      self.log(person_name.capitalize() + "'s alarm is not ringing because another alarm is ringing now")
      self.call_service("input_boolean/turn_off", entity_id=f"input_boolean.alarm_{person_name}")


  def snooze_alarm(self, event_name, data, kwargs):
    person_name = self.get_person_name_alarm_ringing()
    if person_name:
      self.log("Alarm snoozed")
      alarm_time = (datetime.now() + timedelta(minutes=10)).strftime("%H:%M:00")
      self.call_service("input_datetime/set_datetime", entity_id=f"input_datetime.alarm_{person_name}", time=alarm_time)


  def turn_off_alarm(self, kwargs):
    person_name = kwargs["person_name"]
    self.call_service("input_boolean/turn_off", entity_id=f"input_boolean.alarm_{person_name}")


  def get_person_name_alarm_ringing(self):
    ringing = None
    for person_name in self.persons.get_all_person_names(with_alarm=True):
      if self.is_alarm_ringing(person_name):
        ringing = person_name
    return ringing


  def cancel_alarm_handler(self, person_name):
    alarm_handler = self.alarm_handlers[person_name]
    if self.timer_running(alarm_handler):
      self.cancel_timer(alarm_handler)


  def set_alarm_on_time(self, person_name):
    self.log(f"Setting {person_name.capitalize()}'s alarm")
    current_time = datetime.now()
    current_alarm_time = self.parse_time(self.get_state(f"input_datetime.alarm_{person_name}"))
    alarm_time_start = (datetime.combine(date.today(), current_alarm_time) - timedelta(minutes=5)).time()
    current_time_alarm_time_start_diff = self.time_to_minutes(current_time) - self.time_to_minutes(alarm_time_start)
    if (0 <= current_time_alarm_time_start_diff <= 5) or (-1440 <= current_time_alarm_time_start_diff <= -1435):
      self.log("Alarm time is too soon, starting it immediately")
      alarm_time_start = (current_time + timedelta(seconds=5)).time()
    self.cancel_alarm_handler(person_name)
    self.alarm_handlers[person_name] = self.run_once(self.ring_alarm, alarm_time_start, person_name=person_name)


  def time_to_minutes(self, input_time):
    return input_time.hour * 60 + input_time.minute


  def is_alarm_ringing(self, person_name):
    entity = f"input_boolean.alarm_{person_name}_ringing"
    return self.get_state(entity) == "on"


  def on_night_scene(self, entity, attribute, old, new, kwargs):
    if self.get_state("binary_sensor.bedroom_yandex_station_active") == "on":
      return
    alarms = []
    text = "Спокойной ночи! "
    for person_name in self.persons.get_all_person_names(with_alarm=True):
      entity = f"input_boolean.alarm_{person_name}"
      if self.get_state(entity) == "on":
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
    for person_name in self.persons.get_all_person_names(with_alarm=True):
      entity = f"input_boolean.alarm_{person_name}"
      if self.get_state(entity) == "on":
        all_alarms_off = False
    if all_alarms_off:
      self.call_service("input_boolean/turn_on", entity_id="input_boolean.alarm_snooze_allowed")
