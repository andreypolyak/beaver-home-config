import appdaemon.plugins.hass.hassapi as hass


class KitchenCover(hass.Hass):

  def initialize(self):
    self.closed_ts = 0
    self.listen_state(self.on_living_scene_change, "input_select.living_scene")
    self.listen_event(self.on_timer_finished, "timer.finished", entity_id="timer.ventilation_kitchen_cover")
    self.listen_event(self.on_close_cover, "close_kitchen_cover")
    self.listen_event(self.on_partly_open_cover, "partly_open_kitchen_cover")
    binary_sensors = self.get_state("binary_sensor")
    for binary_sensor in binary_sensors:
      if binary_sensor.endswith("_motion") and "bedroom" not in binary_sensor:
        self.listen_state(self.on_motion, binary_sensor, new="on", old="off")
    self.listen_state(self.on_cinema_session_off, "input_boolean.cinema_session", new="off")
    self.listen_state(self.on_cover_change, "cover.kitchen_cover", attribute="current_position")
    self.handle = None


  def on_cover_change(self, entity, attribute, old, new, kwargs):
    if self.timer_running(self.handle):
      self.cancel_timer(self.handle)
    self.call_service("input_boolean/turn_on", entity_id="input_boolean.kitchen_cover_active")
    self.handle = self.run_in(self.turn_off_cover_active, 10)


  def turn_off_cover_active(self, kwargs):
    self.call_service("input_boolean/turn_off", entity_id="input_boolean.kitchen_cover_active")


  def on_cinema_session_off(self, entity, attribute, old, new, kwargs):
    living_scene = self.get_state("input_select.living_scene")
    cover_position = self.get_state("cover.kitchen_cover", attribute="current_position")
    if living_scene not in ["night", "away", "party"] and cover_position != "100":
      self.open_cover()


  def on_motion(self, entity, attribute, old, new, kwargs):
    living_scene = self.get_state("input_select.living_scene")
    cover_position = self.get_state("cover.kitchen_cover", attribute="current_position")
    if living_scene == "night" and cover_position == "0":
      self.partly_open_cover()


  def on_living_scene_change(self, entity, attribute, old, new, kwargs):
    if new in ["party"]:
      self.close_cover()
    elif new in ["dark_cinema", "night"]:
      self.partly_open_cover()
    elif old in ["party", "night"]:
      self.open_cover()


  def on_close_cover(self, event_name, data, kwargs):
    delta_ts = self.get_now_ts() - self.closed_ts
    if self.get_state("cover.kitchen_cover", attribute="current_position") != "0" and delta_ts > 30:
      self.close_cover()


  def on_partly_open_cover(self, event_name, data, kwargs):
    self.partly_open_cover()


  def on_timer_finished(self, event_name, data, kwargs):
    self.partly_open_cover()


  def close_cover(self):
    self.closed_ts = self.get_now_ts()
    self.call_service("timer/start", entity_id="timer.ventilation_kitchen_cover", duration=3600)
    self.call_service("cover/set_cover_position", entity_id="cover.kitchen_cover", position=0)


  def open_cover(self):
    self.closed_ts = 0
    self.call_service("timer/cancel", entity_id="timer.ventilation_kitchen_cover")
    self.call_service("cover/set_cover_position", entity_id="cover.kitchen_cover", position=100)


  def partly_open_cover(self):
    self.closed_ts = 0
    self.call_service("timer/cancel", entity_id="timer.ventilation_kitchen_cover")
    self.call_service("cover/set_cover_position", entity_id="cover.kitchen_cover", position=30)
