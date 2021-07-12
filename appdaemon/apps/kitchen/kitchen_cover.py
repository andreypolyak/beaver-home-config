from base import Base


class KitchenCover(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_living_scene_change, "input_select.living_scene")
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
    self.cancel_handle(self.handle)
    self.turn_on_entity("input_boolean.kitchen_cover_active")
    self.handle = self.run_in(self.turn_off_cover_active, 10)


  def turn_off_cover_active(self, kwargs):
    self.turn_off_entity("input_boolean.kitchen_cover_active")


  def on_cinema_session_off(self, entity, attribute, old, new, kwargs):
    if self.get_living_scene() not in ["night", "away", "party"]:
      self.open_cover()


  def on_motion(self, entity, attribute, old, new, kwargs):
    if self.get_living_scene() == "night" and self.get_cover_position() == 0:
      self.partly_open_cover()


  def on_living_scene_change(self, entity, attribute, old, new, kwargs):
    if new == "away":
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
    if self.get_cover_position() != 0:
      self.set_cover_position("kitchen_cover", 0)
      return True
    return False


  def open_cover(self):
    if self.get_cover_position() != 100:
      self.set_cover_position("kitchen_cover", 100)
      return True
    return False


  def partly_open_cover(self):
    if self.get_cover_position() != 15:
      self.set_cover_position("kitchen_cover", 15)
      return True
    return False


  def get_cover_position(self):
    return self.get_state("cover.kitchen_cover", attribute="current_position")
