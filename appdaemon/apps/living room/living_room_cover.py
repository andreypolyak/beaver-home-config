from base import Base


class LivingRoomCover(Base):

  def initialize(self):
    super().initialize()
    self.check_handle = None
    self.turn_off_handle = None
    self.init_storage("living_room_cover", "was_closed", False)
    self.listen_state(self.on_scene_change, "input_select.living_scene")
    self.listen_state(self.on_balcony_door_open, "binary_sensor.living_room_balcony_door", new="on", old="off")
    self.listen_state(self.on_balcony_door_close, "binary_sensor.living_room_balcony_door", new="off", old="on")
    self.listen_state(self.on_cover_change, "cover.living_room_template_cover", immediate=True)
    self.listen_event(self.on_close_living_room_cover, "close_living_room_cover")


  def on_cover_change(self, entity, attribute, old, new, kwargs):
    if new in ["opening", "closing"]:
      self.turn_on_entity("input_boolean.living_room_cover_active")
    else:
      self.turn_off_entity("input_boolean.living_room_cover_active")


  def on_close_living_room_cover(self, event_name, data, kwargs):
    self.close_living_room_cover()


  def on_scene_change(self, entity, attribute, old, new, kwargs):
    if new in ["away", "night", "light_cinema", "dark_cinema", "party"]:
      self.write_storage("was_closed", True)
      self.close_living_room_cover()
    elif new == "day":
      self.write_storage("was_closed", False)
      self.open_living_room_cover()


  def on_balcony_door_open(self, entity, attribute, old, new, kwargs):
    if self.get_state("cover.living_room_template_cover") in ["closed", "closing"]:
      self.write_storage("was_closed", True)
    else:
      self.write_storage("was_closed", False)
    self.open_living_room_cover()


  def on_balcony_door_close(self, entity, attribute, old, new, kwargs):
    if self.living_scene in ["away", "night", "light_cinema", "dark_cinema", "party"]:
      self.log("Balcony door closed. Closing cover because of the current living scene")
      self.close_living_room_cover()
    elif self.read_storage("was_closed"):
      self.log("Balcony door closed. Closing cover because it was closed before the door was open")
      self.close_living_room_cover()


  def close_living_room_cover(self):
    if self.entity_is_off("binary_sensor.living_room_balcony_door"):
      self.log("Close cover")
      self.close_cover("living_room_template_cover")
    else:
      self.log("Cover will not close because balcony door is open")


  def open_living_room_cover(self):
    self.log("Open cover")
    self.open_cover("living_room_template_cover")
