import appdaemon.plugins.hass.hassapi as hass


class BedroomCover(hass.Hass):

  def initialize(self):
    self.listen_state(self.on_sleeping_scene_change, "input_select.sleeping_scene")
    self.listen_state(self.on_living_scene_change, "input_select.living_scene")
    self.listen_event(self.on_close_cover, "close_bedroom_cover")
    self.listen_state(self.on_cinema_session_off, "input_boolean.cinema_session", new="off")
    self.listen_state(self.on_cover_change, "cover.bedroom_cover", attribute="current_position")
    self.handle = None
    self.run_every(self.check_comfortable, "now", 60)


  def check_comfortable(self, kwargs):
    if self.get_state("input_select.sleeping_scene") != "night":
      self.call_service("timer/cancel", entity_id=f"timer.cover_bedroom_no_change")
      return
    if self.get_state("timer.cover_bedroom_no_change") == "active":
      self.log("No change timer is active")
      return
    if self.is_uncomfortable():
      self.log("Uncomfortable condition during night")
      res = self.partly_open_cover()
    else:
      self.log("Comfortable condition during night")
      res = self.close_cover()
    if res:
      self.log("Cover position changed, turning on no change timer")
      self.call_service("timer/start", entity_id=f"timer.cover_bedroom_no_change", duration=1200)


  def on_cover_change(self, entity, attribute, old, new, kwargs):
    if self.timer_running(self.handle):
      self.cancel_timer(self.handle)
    self.call_service("input_boolean/turn_on", entity_id="input_boolean.bedroom_cover_active")
    self.handle = self.run_in(self.turn_off_cover_active, 10)


  def turn_off_cover_active(self, kwargs):
    self.call_service("input_boolean/turn_off", entity_id="input_boolean.bedroom_cover_active")


  def on_cinema_session_off(self, entity, attribute, old, new, kwargs):
    living_scene = self.get_state("input_select.living_scene")
    sleeping_scene = self.get_state("input_select.sleeping_scene")
    if (
      living_scene not in ["night", "away", "party"]
      and sleeping_scene not in ["night", "away"]
    ):
      self.open_cover()


  def on_sleeping_scene_change(self, entity, attribute, old, new, kwargs):
    if new == "away":
      self.partly_open_cover()
    elif new == "night":
      self.call_service("timer/start", entity_id=f"timer.cover_bedroom_no_change", duration=1200)
      if self.is_uncomfortable():
        self.partly_open_cover()
      else:
        self.close_cover()
    elif old == "night":
      self.open_cover()
    elif old == "away":
      self.open_cover()


  def on_living_scene_change(self, entity, attribute, old, new, kwargs):
    sleeping_scene = self.get_state("input_select.sleeping_scene")
    if new == "party":
      self.close_cover()
    elif new == "dark_cinema":
      self.partly_open_cover()
    elif old == "party" and sleeping_scene == "day":
      self.open_cover()


  def on_close_cover(self, event_name, data, kwargs):
    self.close_cover()


  def close_cover(self):
    if self.get_state("cover.bedroom_cover", attribute="current_position") != "0":
      self.call_service("cover/set_cover_position", entity_id="cover.bedroom_cover", position=0)
      return True
    return False


  def open_cover(self):
    if self.get_state("cover.bedroom_cover", attribute="current_position") != "100":
      self.call_service("cover/set_cover_position", entity_id="cover.bedroom_cover", position=100)
      return True
    return False


  def partly_open_cover(self):
    if self.get_state("cover.bedroom_cover", attribute="current_position") != "15":
      self.call_service("cover/set_cover_position", entity_id="cover.bedroom_cover", position=15)
      return True
    return False


  def is_uncomfortable(self):
    try:
      co2 = float(self.get_state("sensor.bedroom_co2"))
      temperature = float(self.get_state("sensor.bedroom_temperature"))
    except ValueError:
      return False
    if co2 > 800 or temperature > 25:
      return True
    return False
