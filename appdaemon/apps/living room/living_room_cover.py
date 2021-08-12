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
    entity = "cover.living_room_cover"
    self.listen_state(self.on_cover_running_change, entity, attribute="running", immediate=True)
    self.listen_state(self.on_cover_position_change, entity, attribute="current_position", immediate=True)
    self.listen_event(self.on_close_living_room_cover, "close_living_room_cover")
    self.run_every(self.get_cover_state, "now", 30)


  def get_cover_state(self, kwargs):
    self.call_service("mqtt/publish", topic="zigbee2mqtt/Living Room Cover/get", payload='{"state": ""}')


  def on_cover_running_change(self, entity, attribute, old, new, kwargs):
    if new is True:
      self.turn_on_active()
      return
    self.turn_off_active()


  def on_cover_position_change(self, entity, attribute, old, new, kwargs):
    if new not in [0, 100]:
      self.turn_on_active()
      return
    self.turn_off_active()


  def turn_on_active(self):
    self.turn_on_entity("input_boolean.living_room_cover_active")
    self.cancel_handle(self.check_handle)
    self.cancel_handle(self.turn_off_handle)
    self.check_handle = self.run_every(self.get_cover_state, "now", 1)


  def turn_off_active(self):
    self.turn_off_entity("input_boolean.living_room_cover_active")
    self.cancel_handle(self.turn_off_handle)
    self.turn_off_handle = self.run_in(self.turn_off_check, 15)


  def turn_off_check(self, kwargs):
    self.cancel_handle(self.check_handle)
    self.cancel_handle(self.turn_off_handle)


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
    if self.is_cover_closed():
      self.write_storage("was_closed", True)
    else:
      self.write_storage("was_closed", False)
    self.open_living_room_cover()


  def on_balcony_door_close(self, entity, attribute, old, new, kwargs):
    if self.get_living_scene() in ["away", "night", "light_cinema", "dark_cinema", "party"]:
      self.log("Balcony door closed. Closing cover because of the current living scene")
      self.close_living_room_cover()
    elif self.read_storage("was_closed"):
      self.log("Balcony door closed. Closing cover because it was closed before the door was open")
      self.close_living_room_cover()


  def close_living_room_cover(self):
    if self.is_entity_off("binary_sensor.living_room_balcony_door"):
      self.log("Close cover")
      self.close_cover("living_room_cover")
    else:
      self.log("Cover will not close because balcony door is open")


  def open_living_room_cover(self):
    self.log("Open cover")
    self.open_cover("living_room_cover")


  def is_cover_closed(self):
    if self.is_entity_on("input_boolean.living_room_cover_active"):
      self.log("Cover not closed because it's active")
      return False
    if self.get_state("cover.living_room_cover") == "open":
      self.log("Cover not closed because it's open")
      return False
    self.log("Cover is not closed")
    return True
