import appdaemon.plugins.hass.hassapi as hass


class BedroomCover(hass.Hass):

  def initialize(self):
    self.closed_ts = 0
    self.listen_state(self.on_sleeping_scene_change, "input_select.sleeping_scene")
    self.listen_state(self.on_living_scene_change, "input_select.living_scene")
    # self.listen_event(self.on_timer_finished, "timer.finished", entity_id="timer.ventilation_bedroom_cover")
    self.listen_event(self.on_close_cover, "close_bedroom_cover")
    self.listen_state(self.on_cinema_session_off, "input_boolean.cinema_session", new="off")
    self.listen_state(self.on_cover_change, "cover.bedroom_cover", attribute="current_position")
    self.handle = None


  def on_cover_change(self, entity, attribute, old, new, kwargs):
    if self.timer_running(self.handle):
      self.cancel_timer(self.handle)
    self.call_service("input_boolean/turn_on", entity_id="input_boolean.bedroom_cover_active")
    self.handle = self.run_in(self.turn_off_cover_active, 10)


  # def on_close_cover(self, event_name, data, kwargs):
  #   self.close_cover()


  def turn_off_cover_active(self, kwargs):
    self.call_service("input_boolean/turn_off", entity_id="input_boolean.bedroom_cover_active")


  def on_cinema_session_off(self, entity, attribute, old, new, kwargs):
    living_scene = self.get_state("input_select.living_scene")
    sleeping_scene = self.get_state("input_select.sleeping_scene")
    cover_position = self.get_state("cover.bedroom_cover", attribute="current_position")
    if (
      living_scene not in ["night", "away", "party"]
      and sleeping_scene not in ["night", "away"]
      and cover_position != "100"
    ):
      self.open_cover()


  def on_sleeping_scene_change(self, entity, attribute, old, new, kwargs):
    if new == "night":
      self.close_cover()
    elif old == "night":
      self.open_cover()


  def on_living_scene_change(self, entity, attribute, old, new, kwargs):
    sleeping_scene = self.get_state("input_select.sleeping_scene")
    cover_position = self.get_state("cover.bedroom_cover", attribute="current_position")
    if new == "party":
      self.close_cover()
    elif new == "dark_cinema":
      self.partly_open_cover()
    elif old == "party" and sleeping_scene == "day" and cover_position != "100":
      self.open_cover()


  def on_close_cover(self, event_name, data, kwargs):
    delta_ts = self.get_now_ts() - self.closed_ts
    if self.get_state("cover.bedroom_cover", attribute="current_position") != "0" and delta_ts > 30:
      self.close_cover()


  # def on_timer_finished(self, event_name, data, kwargs):
  #   self.partly_open_cover()


  def close_cover(self):
    self.closed_ts = self.get_now_ts()
    # self.call_service("timer/start", entity_id="timer.ventilation_bedroom_cover", duration=60*60)
    self.call_service("cover/set_cover_position", entity_id="cover.bedroom_cover", position=0)


  def open_cover(self):
    self.closed_ts = 0
    # self.call_service("timer/cancel", entity_id="timer.ventilation_bedroom_cover")
    self.call_service("cover/set_cover_position", entity_id="cover.bedroom_cover", position=100)


  def partly_open_cover(self):
    self.closed_ts = 0
    # self.call_service("timer/cancel", entity_id="timer.ventilation_bedroom_cover")
    self.call_service("cover/set_cover_position", entity_id="cover.bedroom_cover", position=15)
