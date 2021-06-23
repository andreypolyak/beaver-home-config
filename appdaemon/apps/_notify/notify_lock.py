import appdaemon.plugins.hass.hassapi as hass


class NotifyLock(hass.Hass):

  def initialize(self):
    self.notifications = self.get_app("notifications")
    self.storage = self.get_app("persistent_storage")
    default = {"change_ts": None, "is_locked": False}
    self.storage.init("notify_lock.data", default)
    self.expected_state = None
    self.handle = None
    service_data = {"entity_id": "lock.entrance_lock"}
    self.listen_event(self.on_lock_service, "call_service", domain="lock", service_data=service_data)
    self.listen_state(self.on_lock_change, "lock.entrance_lock")
    self.listen_state(self.on_door_open, "binary_sensor.entrance_door", new="on", old="off")


  def on_lock_change(self, entity, attribute, old, new, kwargs):
    if new == "unlocked":
      self.storage.write("notify_lock.data", False, attribute="is_locked")
      self.log("Lock was unlocked")
      if old == "unknown":
        return
      self.storage.write("notify_lock.data", self.get_now_ts(), attribute="change_ts")
      if self.expected_state == "unlocked":
        self.expected_state = None
    elif new == "locked":
      self.storage.write("notify_lock.data", True, attribute="is_locked")
      self.log("Lock was locked")
      if old == "unknown":
        return
      self.storage.write("notify_lock.data", self.get_now_ts(), attribute="change_ts")
      if self.expected_state == "locked":
        self.expected_state = None


  def on_lock_service(self, event_name, data, kwargs):
    if self.timer_running(self.handle):
      self.cancel_timer(self.handle)
    change_ts = self.storage.read("notify_lock.data", attribute="change_ts")
    is_locked = self.storage.read("notify_lock.data", attribute="is_locked")
    service = data["service"]
    self.log(f"{service} service was requested")
    if change_ts is None or (self.get_now_ts() - change_ts) < 5:
      return
    if service == "lock" and not is_locked:
      self.expected_state = "locked"
      self.handle = self.run_in(self.check_lock_new_state, 10, expected="locked")
    elif service == "unlock" and is_locked:
      self.expected_state = "unlocked"
      self.handle = self.run_in(self.check_lock_new_state, 10, expected="unlocked")


  def on_door_open(self, entity, attribute, old, new, kwargs):
    if self.get_state("lock.entrance_lock") == "locked":
      self.log("Door was opened")
      self.run_in(self.check_lock_after_door_open, 1)


  def check_lock_after_door_open(self, kwargs):
    if self.get_state("lock.entrance_lock") == "locked" and self.get_state("binary_sensor.entrance_door") == "on":
      self.log("Entrance locked but door is opened")
      message = "🔓 Lock stuck in the locked state. Trying to fix it now"
      self.notifications.send("admin", message, "lock_repair", sound="Noir.caf", url="/lovelace/bathroom_entrance")
      self.configure_lock()


  def check_lock_new_state(self, kwargs):
    if self.expected_state is not None:
      return
    expected_state = kwargs["expected"]
    current_state = self.get_state("lock.entrance_lock")
    if current_state != expected_state:
      self.log(f"Expected state is {expected_state}, but current state is {current_state}")
      message = f"🔓 Lock stuck in the {current_state} state. Trying to fix it now"
      self.notifications.send("admin", message, "lock_repair", sound="Noir.caf", url="/lovelace/bathroom_entrance")
      self.configure_lock()


  def configure_lock(self):
    self.log("Configuring the lock")
    topic = "zigbee2mqtt_entrance/bridge/request/device/configure"
    self.call_service("mqtt/publish", topic=topic, payload="Entrance Lock")
