from base import Base


class BedroomCover(Base):

  def initialize(self):
    super().initialize()
    self.handle = None
    self.listen_state(self.on_sleeping_scene_change, "input_select.sleeping_scene")
    self.listen_state(self.on_living_scene_change, "input_select.living_scene")
    self.listen_event(self.on_close_cover, "close_bedroom_cover")
    self.listen_state(self.on_cinema_session_off, "input_boolean.cinema_session", new="off")
    self.listen_state(self.on_cover_change, "cover.bedroom_cover", attribute="current_position")
    self.run_every(self.check_comfortable, "now", 60)


  def check_comfortable(self, kwargs):
    if self.sleeping_scene != "night":
      return
    if self.is_timer_active("cover_bedroom_freeze"):
      self.log("Freeze timer is active")
    elif self.uncomfortable:
      self.log("Uncomfortable condition during night")
      self.partly_open_cover()
    else:
      self.log("Comfortable condition during night")
      self.close_cover()


  def on_cover_change(self, entity, attribute, old, new, kwargs):
    self.cancel_handle(self.handle)
    self.turn_on_entity("input_boolean.bedroom_cover_active")
    self.handle = self.run_in(self.turn_off_cover_active, 10)


  def turn_off_cover_active(self, kwargs):
    self.turn_off_entity("input_boolean.bedroom_cover_active")


  def on_cinema_session_off(self, entity, attribute, old, new, kwargs):
    if (
      self.living_scene not in ["night", "away", "party"]
      and self.sleeping_scene not in ["night", "away"]
    ):
      self.open_cover()


  def on_sleeping_scene_change(self, entity, attribute, old, new, kwargs):
    if new == "night":
      if self.uncomfortable:
        self.partly_open_cover()
      else:
        self.close_cover()
      return
    self.timer_cancel("cover_bedroom_freeze")
    if new == "away":
      self.partly_open_cover()
    elif old == "night":
      self.open_cover()
    elif old == "away":
      self.open_cover()


  def on_living_scene_change(self, entity, attribute, old, new, kwargs):
    if new == "party":
      self.close_cover()
    elif new == "dark_cinema":
      self.partly_open_cover()
    elif old == "party" and self.sleeping_scene == "day":
      self.open_cover()


  def on_close_cover(self, event_name, data, kwargs):
    self.close_cover()


  def close_cover(self):
    self.set_timer_freeze()
    if self.cover_position != 0:
      self.set_cover_position("bedroom_cover", 0)


  def open_cover(self):
    if self.cover_position != 100:
      self.set_cover_position("bedroom_cover", 100)


  def partly_open_cover(self):
    self.set_timer_freeze()
    if self.cover_position != 15:
      self.set_cover_position("bedroom_cover", 15)


  @property
  def uncomfortable(self):
    co2 = self.get_float_state("sensor.bedroom_co2")
    temperature = self.get_float_state("sensor.bedroom_temperature")
    if co2 is None or temperature is None or (co2 < 800 and temperature < 25):
      return False
    return True


  @property
  def cover_position(self):
    return self.get_state("cover.bedroom_cover", attribute="current_position")


  def set_timer_freeze(self):
    if self.sleeping_scene == "night":
      self.timer_start("cover_bedroom_freeze", 1800)
