from base import Base
from datetime import timedelta


class AlarmManager(Base):

  def initialize(self):
    super().initialize()
    self.handles = {}
    for person_name in self.persons.get_all_person_names(with_alarm=True):
      self.handles[person_name] = None
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
    if self.get_delta_ts(self.sleeping_zone_motion_ts) < 60 and self.is_entity_on("binary_sensor.bedroom_door"):
      self.motion_occured()


  def motion_occured(self):
    person_name = self.get_person_name_alarm_ringing()
    if not person_name:
      return
    other_alarms_turned_on = False
    for other_person_name in self.persons.get_all_person_names_except_provided(person_name, with_alarm=True):
      self.turn_off_entity("input_boolean.alarm_ringing")
      if self.is_entity_on(f"input_boolean.alarm_{other_person_name}"):
        other_alarms_turned_on = True
    if other_alarms_turned_on:
      self.log(f"Motion occured when {person_name.capitalize()}'s alarm was ringing. "
               "Cancelling it because different alarm is turned on")
      self.fire_event("custom_event", custom_event_data=f"cancel_alarm_{person_name}")
    else:
      self.log(f"Motion occured when {person_name.capitalize()}'s alarm was ringing. "
               "Finishing it because no other alarms are turned on")
      self.fire_event("custom_event", custom_event_data=f"finish_alarm_{person_name}")
    self.run_in(self.turn_off_alarm, 1, person_name=person_name)


  def on_alarm_off(self, entity, attribute, old, new, kwargs):
    person_name = self.persons.get_person_name_from_entity_name(entity)
    self.log(f"{person_name.capitalize()}'s alarm turned off")
    if self.is_entity_on(f"input_boolean.alarm_{person_name}_ringing"):
      self.log(f"{person_name.capitalize()}'s alarm is ringing and will be cancelled because alarm was turned off")
      self.turn_off_entity("input_boolean.alarm_ringing")
      self.fire_event("custom_event", custom_event_data=f"cancel_alarm_{person_name}")
    self.cancel_handle(self.handles[person_name])
    self.allow_snooze_if_alarms_off()


  def on_alarm_on(self, entity, attribute, old, new, kwargs):
    if self.get_sleeping_scene() != "night":
      self.set_sleeping_scene("night")
    person_name = self.persons.get_person_name_from_entity_name(entity)
    self.log(f"{person_name.capitalize()}'s alarm turned on")
    self.set_alarm_on_time(person_name)


  def on_alarm_time_update(self, entity, attribute, old, new, kwargs):
    person_name = self.persons.get_person_name_from_entity_name(entity)
    self.log(f"New time was set for {person_name.capitalize()}'s alarm")
    self.update_alarm_time(person_name)


  def update_alarm_time(self, person_name):
    if self.is_entity_on(f"input_boolean.alarm_{person_name}"):
      if self.is_entity_on(f"input_boolean.alarm_{person_name}_ringing"):
        self.log(f"{person_name.capitalize()}'s alarm is ringing and will be cancelled because new alarm time was set")
        self.turn_off_entity("input_boolean.alarm_ringing")
        self.fire_event("custom_event", custom_event_data=f"cancel_alarm_{person_name}")
      self.set_alarm_on_time(person_name)


  def ring_alarm(self, kwargs):
    person_name = kwargs["person_name"]
    if not self.get_person_name_alarm_ringing() and self.get_sleeping_scene() == "night":
      self.log(f"{person_name.capitalize()}'s alarm is ringing")
      self.turn_on_entity("input_boolean.alarm_ringing")
      self.fire_event("custom_event", custom_event_data=f"start_alarm_{person_name}")
    elif self.get_sleeping_scene() != "night":
      self.log(f"{person_name.capitalize()}'s alarm is not ringing because night scene is not turned on")
      self.turn_off_entity(f"input_boolean.alarm_{person_name}")
    else:
      self.log(f"{person_name.capitalize()}'s alarm is not ringing because another alarm is ringing now")
      self.turn_off_entity(f"input_boolean.alarm_{person_name}")


  def snooze_alarm(self, event_name, data, kwargs):
    person_name = self.get_person_name_alarm_ringing()
    if person_name:
      self.log("Alarm snoozed")
      alarm_time = (self.get_now() + timedelta(minutes=10)).strftime("%H:%M:00")
      self.set_time(f"input_datetime.alarm_{person_name}", alarm_time)


  def turn_off_alarm(self, kwargs):
    person_name = kwargs["person_name"]
    self.turn_off_entity(f"input_boolean.alarm_{person_name}")


  def get_person_name_alarm_ringing(self):
    ringing = None
    for person_name in self.persons.get_all_person_names(with_alarm=True):
      if self.is_entity_on(f"input_boolean.alarm_{person_name}_ringing"):
        ringing = person_name
    return ringing


  def set_alarm_on_time(self, person_name):
    self.log(f"Setting {person_name.capitalize()}'s alarm")
    current_time = self.get_now()
    alarm_time = self.parse_datetime(self.get_state(f"input_datetime.alarm_{person_name}"), aware=True)
    alarm_time = alarm_time - timedelta(minutes=5)
    if (current_time - alarm_time).seconds <= 300:
      self.log("Alarm time is too soon, starting it immediately")
      alarm_time = current_time + timedelta(seconds=5)
    alarm_time = alarm_time.time()
    self.cancel_handle(self.handles[person_name])
    self.log(f"Setting alarm on {alarm_time}")
    self.handles[person_name] = self.run_once(self.ring_alarm, alarm_time, person_name=person_name)


  def time_to_minutes(self, input_time):
    return input_time.hour * 60 + input_time.minute


  def on_night_scene(self, entity, attribute, old, new, kwargs):
    if self.is_entity_on("binary_sensor.bedroom_yandex_station_active"):
      return
    alarms = []
    text = "Спокойной ночи! "
    for person_name in self.persons.get_all_person_names(with_alarm=True):
      if self.is_entity_on(f"input_boolean.alarm_{person_name}"):
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
      if self.is_entity_on(f"input_boolean.alarm_{person_name}"):
        all_alarms_off = False
    if all_alarms_off:
      self.turn_on_entity("input_boolean.alarm_snooze_allowed")
