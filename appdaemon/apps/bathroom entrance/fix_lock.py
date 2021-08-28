from base import Base


class FixLock(Base):

  def initialize(self):
    super().initialize()
    self.init_storage("notify_lock", "change_ts", None)
    self.init_storage("notify_lock", "is_locked", False)
    self.expected_state = None
    self.handle = None
    service_data = {"entity_id": "lock.entrance_lock"}
    self.listen_event(self.on_lock_service, "call_service", domain="lock", service_data=service_data)
    self.listen_state(self.on_lock_change, "lock.entrance_lock")
    self.listen_state(self.on_door_open, "binary_sensor.entrance_door", new="on", old="off")


  def on_lock_change(self, entity, attribute, old, new, kwargs):
    if new == "unlocked":
      self.write_storage("is_locked", False)
      self.log("Lock was unlocked")
      if old == "unknown":
        return
      self.write_storage("change_ts", self.get_now_ts())
      if self.expected_state == "unlocked":
        self.expected_state = None
    elif new == "locked":
      self.write_storage("is_locked", True)
      self.log("Lock was locked")
      if old == "unknown":
        return
      self.write_storage("change_ts", self.get_now_ts())
      if self.expected_state == "locked":
        self.expected_state = None


  def on_lock_service(self, event_name, data, kwargs):
    self.cancel_handle(self.handle)
    change_ts = self.read_storage("change_ts")
    is_locked = self.read_storage("is_locked")
    service = data["service"]
    self.log(f"{service} service was requested")
    if change_ts is None or self.get_delta_ts(change_ts) < 5:
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
    if self.get_state("lock.entrance_lock") == "locked" and self.entity_is_on("binary_sensor.entrance_door"):
      self.log("Entrance locked but door is opened")
      message = "🔓 Lock stuck in the locked state. Trying to fix it now"
      self.send_push("admin", message, "lock_repair", sound="Noir.caf", url="/lovelace/bathroom_entrance")
      self.configure_lock()


  def check_lock_new_state(self, kwargs):
    if self.expected_state is not None:
      return
    expected_state = kwargs["expected"]
    current_state = self.get_state("lock.entrance_lock")
    if current_state != expected_state:
      self.log(f"Expected state is {expected_state}, but current state is {current_state}")
      message = f"🔓 Lock stuck in the {current_state} state. Trying to fix it now"
      self.send_push("admin", message, "lock_repair", sound="Noir.caf", url="/lovelace/bathroom_entrance")
      self.configure_lock()


  def configure_lock(self):
    self.log("Configuring the lock")
    topic = "zigbee2mqtt_entrance/bridge/request/device/configure"
    self.call_service("mqtt/publish", topic=topic, payload="Entrance Lock")
