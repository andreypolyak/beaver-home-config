import appdaemon.plugins.hass.hassapi as hass


class Lock(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    self.notifications = self.get_app("notifications")
    self.lock_handle = None
    self.unlocked_ts = 0
    self.unlocked_by = None
    self.listen_state(self.on_door_close, "binary_sensor.entrance_door", new="off", old="on")
    self.listen_state(self.on_door_open, "binary_sensor.entrance_door", new="on", old="off")
    self.listen_state(self.on_lock_unlock, "lock.entrance_lock", new="unlocked", old="locked")
    self.listen_state(self.on_lock_change, "lock.entrance_lock", attribute="all")
    self.listen_event(self.on_ios_unlock, event="ios.action_fired", actionName="LOCK_UNLOCK")
    self.listen_event(self.on_ios_unlock, event="mobile_app_notification_action", action="LOCK_UNLOCK")
    self.listen_event(self.on_ios_lock, event="mobile_app_notification_action", action="LOCK_LOCK")
    for entity in self.persons.get_all_person_location_entities():
      self.listen_state(self.on_person_location_change, entity)


  def on_door_close(self, entity, attribute, old, new, kwargs):
    self.log("Door was closed")
    self.cancel_lock_handle()
    self.lock_handle = self.run_in(self.lock_door, 5)


  def on_door_open(self, entity, attribute, old, new, kwargs):
    self.log("Door was opened")
    self.cancel_lock_handle()


  def on_lock_unlock(self, entity, attribute, old, new, kwargs):
    self.log("Lock was unlocked")
    self.cancel_lock_handle()
    self.lock_handle = self.run_in(self.lock_door, 60)
    if (self.get_now_ts() - self.unlocked_ts) < 15 and self.unlocked_by:
      actions = [{"action": "LOCK_LOCK", "title": "🔒 Lock the door", "destructive": True}]
      self.notifications.send(self.unlocked_by, "🔓 Lock was unlocked", "lock", actions=actions)
      self.unlocked_ts = 0
      self.unlocked_by = None


  def on_lock_change(self, entity, attribute, old, new, kwargs):
    self.cancel_lock_handle()
    if self.get_state("lock.entrance_lock", attribute="lock_state") == "not_fully_locked":
      text = "Внимание! Дверь не закрыта до конца!"
      self.fire_event("yandex_speak_text", text=text, room="living_room", volume_level=1.0)
      actions = [
        {"action": "LOCK_UNLOCK", "title": "🔓 Unlock the door", "destructive": True},
        {"action": "LOCK_LOCK", "title": "🔒 Lock the door", "destructive": True}
      ]
      self.notifications.send("home_or_all", "🔓 Lock not fully closed!", "lock", is_critical=True, actions=actions)


  def on_ios_lock(self, event_name, data, kwargs):
    self.lock_door({})


  def on_ios_unlock(self, event_name, data, kwargs):
    self.unlock_door()
    if "action_data" in data:
      self.unlocked_by = data["action_data"]["person_name"]
    elif "sourceDeviceID" in data:
      self.unlocked_by = self.persons.get_person_name_from_entity_name(data["sourceDeviceID"])
    self.unlocked_ts = self.get_now_ts()


  def on_person_location_change(self, entity, attribute, old, new, kwargs):
    person_name = self.persons.get_person_name_from_entity_name(entity)
    actions = [{"action": "LOCK_UNLOCK", "title": "🔓 Unlock the door", "destructive": True}]
    if new == "yard" and old in ["not_home", "district"]:
      self.notifications.send(person_name, "🔐 Do you want to unlock the door?", "lock_district",
                              min_delta=600, ios_category="lock", actions=actions)
    elif new == "downstairs" and old in ["not_home", "district", "yard"]:
      self.notifications.send(person_name, "🔐 To unlock the door please double tap door bell",
                              "lock_downstairs", min_delta=600, ios_category="lock", actions=actions)


  def lock_door(self, kwargs):
    if self.get_state("lock.entrance_lock") == "unlocked" and self.get_state("binary_sensor.entrance_door") == "off":
      self.log("Locking the door")
      self.call_service("lock/lock", entity_id="lock.entrance_lock")


  def unlock_door(self):
    if self.get_state("lock.entrance_lock") == "locked" and self.get_state("binary_sensor.entrance_door") == "off":
      self.log("Unlocking the door")
      self.call_service("lock/unlock", entity_id="lock.entrance_lock")


  def cancel_lock_handle(self):
    if self.timer_running(self.lock_handle):
      self.cancel_timer(self.lock_handle)
