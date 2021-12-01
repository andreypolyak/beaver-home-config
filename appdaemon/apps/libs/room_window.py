from base import Base


class RoomWindow(Base):

  def room_init(self):
    super().initialize()
    self.init_storage("room_window", f"{self.room}_handle_ts", 0)
    self.handle = None
    self.listen_state(self.on_scene_change, f"input_select.{self.zone}_scene")
    self.listen_state(self.on_room_change, self.co2_sensor, ignore_debounce=False)
    self.listen_state(self.on_room_change, self.temperature_sensor, ignore_debounce=False)
    self.listen_state(self.on_room_change, f"timer.window_{self.room}_freeze", ignore_debounce=False)
    self.listen_state(self.on_room_change, f"input_boolean.auto_window_{self.room}", new="on", ignore_debounce=True)
    self.listen_state(self.on_light_off, f"light.ha_template_room_{self.room}", new="off", old="on")
    for action_sensor in self.action_sensors:
      self.listen_state(self.on_action_event, action_sensor)
    self.listen_event(self.on_lovelace_change, event=f"{self.room}_window")
    self.listen_state(self.on_manual_control, f"binary_sensor.{self.room}_window_manual_control", new="on", old="off")


  def on_manual_control(self, entity, attribute, old, new, kwargs):
    self.timer_start(f"window_{self.room}_freeze", 1200)


  def on_lovelace_change(self, event_name, data, kwargs):
    position = data["position"]
    if position == "toggle":
      current_position = self.get_int_state(f"cover.{self.room}_window", attribute="current_position")
      if current_position is None:
        return
      if current_position < 10:
        position = 100
      else:
        position = 0
    else:
      position = int(position)
    self.set_position(position, "lovelace")
    self.timer_start(f"window_{self.room}_freeze", 3600)


  def on_scene_change(self, entity, attribute, old, new, kwargs):
    self.turn_on_entity(f"input_boolean.auto_window_{self.room}")


  def on_light_off(self, entity, attribute, old, new, kwargs):
    self.debounce({"ignore_debounce": True})
    self.timer_cancel(f"window_{self.room}_freeze")


  def on_action_event(self, entity, attribute, old, new, kwargs):
    self.debounce({"ignore_debounce": True})


  def on_room_change(self, entity, attribute, old, new, kwargs):
    ignore_debounce = kwargs["ignore_debounce"]
    self.debounce({"ignore_debounce": ignore_debounce})


  def debounce(self, kwargs):
    ignore_debounce = kwargs["ignore_debounce"]
    self.cancel_handle(self.handle)
    handle_ts = self.read_storage(f"{self.room}_handle_ts")
    freeze_timer_is_active = self.timer_is_active(f"window_{self.room}_freeze")
    if (
      (ignore_debounce or self.get_delta_ts(handle_ts) > 60)
      and not freeze_timer_is_active
      and self.entity_is_on(f"input_boolean.auto_window_{self.room}")
    ):
      self.write_storage(f"{self.room}_handle_ts", self.get_now_ts())
      self.process()
    else:
      self.handle = self.run_in(self.debounce, 60, ignore_debounce=False)


  def process(self):
    (position, reason) = self.calculate_position()
    if position is None:
      return
    position = self.normalize_windows_position(position)
    if self.change_required(position) and self.get_state(f"cover.{self.room}_window") != "unavailable":
      self.set_cover_position(f"{self.room}_window", position)
      self.set_position(position, reason)


  def change_required(self, position):
    current_position = self.get_int_state(f"cover.{self.room}_window", attribute="current_position")
    if current_position is None or abs(current_position - position) >= 5:
      return True
    return False


  def set_position(self, position, reason):
    self.set_cover_position(f"{self.room}_window", position)
    self.log(f"new window position is {position} because of: {reason}")


  def normalize_windows_position(self, position):
    if position < 0:
      position = 0
    elif position > 100:
      position = 100
    position = int(round(position, -1))
    return position


  @property
  def person_sitting_near(self):
    for sensor in self.occupancy_sensors:
      if self.entity_is_on(sensor):
        return True
    return False
