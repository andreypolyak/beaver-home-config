from base import Base


class LivingRoomCover(Base):

  def initialize(self):
    super().initialize()
    self.prev_position = None
    self.was_closed = False
    self.listen_state(self.on_scene_change, "input_select.living_scene")
    self.listen_state(self.on_balcony_door_open, "binary_sensor.living_room_balcony_door", new="on", old="off")
    self.listen_state(self.on_balcony_door_close, "binary_sensor.living_room_balcony_door", new="off", old="on")
    self.listen_state(self.on_cover_running_change, "cover.living_room_cover", attribute="running", immediate=True)
    self.listen_state(self.on_cover_switch_change, "sensor.living_room_cover_switch")
    self.listen_event(self.on_close_living_room_cover, "close_living_room_cover")
    self.run_every(self.get_cover_state, "now", 60)


  def get_cover_state(self, kwargs):
    self.call_service("mqtt/publish", topic="zigbee2mqtt/Living Room Cover/get", payload='{"state": ""}')


  def on_cover_switch_change(self, entity, attribute, old, new, kwargs):
    if new not in ["open", "close"]:
      return
    if new == "close" and self.is_cover_closed():
      return
    if new == "open" and not self.is_cover_closed():
      return
    self.log(f"Cover got command from the switch: {new}. Setting it active")
    self.turn_on_entity("input_boolean.living_room_cover_active")
    self.run_in(self.update_position, 8)


  def update_position(self, kwargs):
    position = self.get_state("cover.living_room_cover", attribute="current_position")
    if position != self.prev_position or position not in [0, 100]:
      self.log(f"Cover changed position ({position}). Getting fresh update")
      self.get_cover_state({})
      self.turn_on_entity("input_boolean.living_room_cover_active")
      self.prev_position = position
      self.run_in(self.update_position, 4)
    else:
      self.log("Cover didn't change position. Setting it inactive")
      self.turn_off_entity("input_boolean.living_room_cover_active")


  def on_cover_running_change(self, entity, attribute, old, new, kwargs):
    if new is True:
      self.turn_on_entity("input_boolean.living_room_cover_active")
      self.run_in(self.update_position, 8)


  def on_close_living_room_cover(self, event_name, data, kwargs):
    self.close_living_room_cover()


  def on_scene_change(self, entity, attribute, old, new, kwargs):
    if new in ["away", "night", "light_cinema", "dark_cinema", "party"]:
      self.close_living_room_cover()
    elif new == "day":
      self.was_closed = False
      self.open_living_room_cover()
    elif old == "away":
      self.was_closed = False
      self.open_living_room_cover()


  def on_balcony_door_open(self, entity, attribute, old, new, kwargs):
    if self.is_cover_closed():
      self.log("Balcony door is open but cover is closed. Saving that cover was closed")
      self.was_closed = True
      self.open_living_room_cover()
    else:
      self.log("Balcony door is open and cover is open. Saving that cover was not closed")
      self.was_closed = False


  def on_balcony_door_close(self, entity, attribute, old, new, kwargs):
    if self.get_living_scene() in ["away", "night", "light_cinema", "dark_cinema", "party"]:
      self.log("Balcony door closed. Closing cover because of the current living scene")
      self.close_living_room_cover()
    elif self.was_closed:
      self.log("Balcony door closed. Closing cover beacuse it was closed before the door was open")
      self.close_living_room_cover()


  def close_living_room_cover(self):
    if self.is_cover_closed():
      self.log("Cover will not close because it's aready closed")
      return
    if self.is_entity_off("binary_sensor.living_room_balcony_door"):
      self.log("Close cover")
      self.close_cover("living_room_cover")
    else:
      self.log("Cover will not close because balcony door is open")


  def open_living_room_cover(self):
    if self.is_cover_closed():
      self.log("Open cover")
      self.open_cover("living_room_cover")
    else:
      self.log("Cover will not open because it's aready open")


  def is_cover_closed(self):
    if self.is_entity_on("input_boolean.living_room_cover_active"):
      return False
    if self.get_state("cover.living_room_cover") == "open":
      return False
    return True
