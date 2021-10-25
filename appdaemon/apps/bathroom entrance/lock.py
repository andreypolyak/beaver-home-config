from base import Base


class Lock(Base):

  def initialize(self):
    super().initialize()
    self.handle = None
    self.unlocked_ts = 0
    self.unlocked_by = None
    self.listen_state(self.on_door_close, "binary_sensor.entrance_door", new="off", old="on")
    self.listen_state(self.on_door_open, "binary_sensor.entrance_door", new="on", old="off")
    self.listen_state(self.on_lock_unlock, "lock.entrance_lock", new="unlocked", old="locked")
    self.listen_state(self.on_lock_change, "lock.entrance_lock", attribute="all")
    self.listen_event(self.on_ios_unlock, event="ios.action_fired", actionName="LOCK_UNLOCK")
    self.listen_event(self.on_ios_unlock, event="mobile_app_notification_action", action="LOCK_UNLOCK")
    self.listen_event(self.on_ios_lock, event="mobile_app_notification_action", action="LOCK_LOCK")
    for entity in self.get_person_locations():
      self.listen_state(self.on_person_location_change, entity)


  def on_door_close(self, entity, attribute, old, new, kwargs):
    self.log("Door was closed")
    self.cancel_handle(self.handle)
    self.handle = self.run_in(self.lock_door, 5)


  def on_door_open(self, entity, attribute, old, new, kwargs):
    self.log("Door was opened")
    self.cancel_handle(self.handle)


  def on_lock_unlock(self, entity, attribute, old, new, kwargs):
    self.log("Lock was unlocked")
    self.cancel_handle(self.handle)
    self.handle = self.run_in(self.lock_door, 60)
    if self.get_delta_ts(self.unlocked_ts) < 15 and self.unlocked_by:
      actions = [{"action": "LOCK_LOCK", "title": "🔒 Lock the door", "destructive": True}]
      self.send_push(self.unlocked_by, "🔓 Lock was unlocked", "lock", sound="Calypso.caf", actions=actions)
      self.unlocked_ts = 0
      self.unlocked_by = None


  def on_lock_change(self, entity, attribute, old, new, kwargs):
    self.cancel_handle(self.handle)
    if self.get_state("lock.entrance_lock", attribute="lock_state") == "not_fully_locked":
      text = "Внимание! Дверь не закрыта до конца!"
      self.fire_event("yandex_speak_text", text=text, room="living_room", volume_level=0.9)
      actions = [
        {"action": "LOCK_UNLOCK", "title": "🔓 Unlock the door", "destructive": True},
        {"action": "LOCK_LOCK", "title": "🔒 Lock the door", "destructive": True}
      ]
      message = "🔓 Lock not fully closed!"
      self.send_push("home_or_all", message, "lock", critical=True, actions=actions)


  def on_ios_lock(self, event_name, data, kwargs):
    self.lock_door({})


  def on_ios_unlock(self, event_name, data, kwargs):
    self.unlock_door()
    if "action_data" in data:
      self.unlocked_by = data["action_data"]["person_name"]
    elif "sourceDeviceID" in data:
      self.unlocked_by = self.get_person_names(entity=data["sourceDeviceID"])[0]
    self.unlocked_ts = self.get_now_ts()


  def on_person_location_change(self, entity, attribute, old, new, kwargs):
    person_name = self.get_person_names(entity=entity)[0]
    actions = [{"action": "LOCK_UNLOCK", "title": "🔓 Unlock the door", "destructive": True}]
    kwargs = {
      "sound": "Calypso.caf",
      "min_delta": 600,
      "ios_category": "lock",
      "actions": actions
    }
    if new == "yard" and old in ["not_home", "district"]:
      message = "🔐 Do you want to unlock the door?"
      self.send_push(person_name, message, "lock_district", **kwargs)
    elif new == "downstairs" and old in ["not_home", "district", "yard"]:
      message = "🔐 To unlock the door please double tap door bell"
      self.send_push(person_name, message, "lock_downstairs", **kwargs)


  def lock_door(self, kwargs):
    if self.get_state("lock.entrance_lock") == "unlocked" and self.entity_is_off("binary_sensor.entrance_door"):
      self.log("Locking the door")
      self.call_service("lock/lock", entity_id="lock.entrance_lock")


  def unlock_door(self):
    if self.get_state("lock.entrance_lock") == "locked" and self.entity_is_off("binary_sensor.entrance_door"):
      self.log("Unlocking the door")
      self.call_service("lock/unlock", entity_id="lock.entrance_lock")
