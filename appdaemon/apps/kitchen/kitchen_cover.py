from base import Base


class KitchenCover(Base):

  def initialize(self):
    super().initialize()
    self.handle = None
    self.listen_state(self.on_living_scene_change, "input_select.living_scene")
    self.listen_event(self.on_close_cover, "close_kitchen_cover")
    self.listen_event(self.on_partly_open_cover, "partly_open_kitchen_cover")
    for binary_sensor in self.get_state("binary_sensor"):
      if binary_sensor.endswith("_motion") and ("kitchen" in binary_sensor or "living_room" in binary_sensor):
        self.listen_state(self.on_motion, binary_sensor, new="on", old="off")
    self.listen_state(self.on_cinema_session_off, "input_boolean.cinema_session", new="off")
    self.listen_state(self.on_cover_change, "cover.kitchen_cover", attribute="position")


  def on_cover_change(self, entity, attribute, old, new, kwargs):
    self.make_cover_active()


  def make_cover_active(self):
    self.cancel_handle(self.handle)
    self.turn_on_entity("input_boolean.kitchen_cover_active")
    self.handle = self.run_in(self.turn_off_cover_active, 10)


  def turn_off_cover_active(self, kwargs):
    self.turn_off_entity("input_boolean.kitchen_cover_active")


  def on_cinema_session_off(self, entity, attribute, old, new, kwargs):
    if self.living_scene not in ["night", "away", "party"]:
      self.open_cover()


  def on_motion(self, entity, attribute, old, new, kwargs):
    if self.living_scene == "night" and self.cover_position == 0:
      self.partly_open_cover()


  def on_living_scene_change(self, entity, attribute, old, new, kwargs):
    if new == "dumb":
      return
    elif new == "away":
      self.partly_open_cover()
    elif new == "party":
      self.close_cover()
    elif new in ["dark_cinema", "night"]:
      self.partly_open_cover()
    elif old in ["party", "night"]:
      self.open_cover()
    elif old == "away":
      self.open_cover()


  def on_close_cover(self, event_name, data, kwargs):
    self.close_cover()


  def on_partly_open_cover(self, event_name, data, kwargs):
    self.partly_open_cover()


  def close_cover(self):
    if self.cover_position != 0:
      self.make_cover_active()
      self.set_cover_position("kitchen_cover", 0)


  def open_cover(self):
    if self.cover_position != 100:
      self.make_cover_active()
      self.set_cover_position("kitchen_cover", 100)


  def partly_open_cover(self):
    if self.cover_position != 15:
      self.make_cover_active()
      self.set_cover_position("kitchen_cover", 15)


  @property
  def cover_position(self):
    return self.get_state("cover.kitchen_cover", attribute="position")
