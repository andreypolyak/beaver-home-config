import appdaemon.plugins.hass.hassapi as hass


class RoomWindow(hass.Hass):

  def room_init(self):
    self.storage = self.get_app("persistent_storage")
    self.persons = self.get_app("persons")
    self.handle = None
    self.storage.init(f"room_window.{self.room}_handle_ts", 0)
    self.set_max_speed({})
    self.listen_state(self.on_scene_change, f"input_select.{self.zone}_scene")
    self.listen_state(self.on_window_stopped, f"sensor.{self.room}_window", new="STOPPED")
    self.listen_state(self.on_room_change, self.co2_sensor, immediate=False)
    self.listen_state(self.on_room_change, self.temperature_sensor, immediate=False)
    self.listen_state(self.on_room_change, f"timer.window_{self.room}_no_change", immediate=False)
    self.listen_state(self.on_room_change, f"input_boolean.auto_window_{self.room}", new="on", immediate=True)
    self.listen_state(self.on_position_change, f"sensor.{self.room}_window_target_position")
    self.listen_state(self.on_light_off, f"light.ha_template_room_{self.room}", new="off", old="on")
    for action_sensor in self.action_sensors:
      self.listen_state(self.on_action_event, action_sensor)
    self.listen_event(self.on_lovelace_change, event="custom_event", custom_event_data=f"{self.room}_window")


  def on_window_stopped(self, entity, attribute, old, new, kwargs):
    self.run_in(self.set_max_speed, 5)


  def on_lovelace_change(self, event_name, data, kwargs):
    command = data["custom_event_data2"]
    if command == "toggle":
      try:
        current_position = int(float(self.get_state(f"cover.{self.room}_window", attribute="current_position")))
      except (TypeError, ValueError):
        return
      if current_position < 10:
        position = 100
      else:
        position = 0
    else:
      position = float(data["custom_event_data2"])
    reason = "lovelace"
    self.set_position({"position": position, "reason": reason})
    self.call_service("timer/start", entity_id=f"timer.window_{self.room}_no_change", duration=1200)


  def on_scene_change(self, entity, attribute, old, new, kwargs):
    self.call_service("input_boolean/turn_on", entity_id=f"input_boolean.auto_window_{self.room}")


  def on_light_off(self, entity, attribute, old, new, kwargs):
    self.debounce({"immediate": True})


  def on_action_event(self, entity, attribute, old, new, kwargs):
    self.debounce({"immediate": True})


  def on_room_change(self, entity, attribute, old, new, kwargs):
    immediate = kwargs["immediate"]
    self.debounce({"immediate": immediate})


  def debounce(self, kwargs):
    immediate = kwargs["immediate"]
    if self.timer_running(self.handle):
      self.cancel_timer(self.handle)
    handle_ts = self.storage.read(f"room_window.{self.room}_handle_ts")
    current_ts = self.get_now_ts()
    is_auto_on = self.get_state(f"input_boolean.auto_window_{self.room}") == "on"
    is_timer_no_change_on = self.get_state(f"timer.window_{self.room}_no_change") == "active"
    if (
      (immediate or (current_ts - handle_ts) > 60)
      and not is_timer_no_change_on
      and is_auto_on
    ):
      self.storage.write(f"room_window.{self.room}_handle_ts", current_ts)
      self.process()
    else:
      self.handle = self.run_in(self.debounce, 60, immediate=False)


  def process(self):
    (position, reason) = self.calculate_position()
    if position is None:
      return
    position = self.normalize_windows_position(position)
    if self.check_if_change_needed(position) and self.get_state(f"cover.{self.room}_window") != "unavailable":
      self.change_position(position, reason)


  def check_if_change_needed(self, position):
    try:
      current_position = int(float(self.get_state(f"cover.{self.room}_window", attribute="current_position")))
    except (ValueError, TypeError):
      return True
    if abs(current_position - position) < 5:
      return False
    return True


  def change_position(self, position, reason):
    self.set_min_speed()
    self.run_in(self.set_position, 3, position=position, reason=reason)


  def set_min_speed(self):
    self.call_service(f"rest_command/{self.room}_window_25")


  def set_position(self, kwargs):
    position = kwargs["position"]
    reason = kwargs["reason"]
    self.call_service("cover/set_cover_position", entity_id=f"cover.{self.room}_window", position=position)
    self.log(f"new window position is {position} because of: {reason}")


  def set_max_speed(self, kwargs):
    if self.get_state(f"sensor.{self.room}_window") == "STOPPED":
      self.call_service(f"rest_command/{self.room}_window_100")


  def normalize_windows_position(self, position):
    if position < 0:
      position = 0
    elif position > 100:
      position = 100
    position = int(round(position, -1))
    return position


  def on_position_change(self, entity, attribute, old, new, kwargs):
    try:
      target_position = self.get_state(f"sensor.{self.room}_window_target_position")
      set_position = self.get_state(f"sensor.{self.room}_window_set_position")
      if abs(float(target_position) - float(set_position)) > 2:
        self.call_service("timer/start", entity_id=f"timer.window_{self.room}_no_change", duration=1200)
    except (ValueError, TypeError):
      return


  def is_person_sitting_near(self):
    for sensor in self.occupancy_sensors:
      if self.get_state(sensor) == "on":
        return True
    return False
