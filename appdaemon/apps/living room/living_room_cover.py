from base import Base


class LivingRoomCover(Base):

  def initialize(self):
    super().initialize()
    self.handle = self.run_in(self.stop_cover, 20)
    self.prev_position = None
    self.listen_state(self.on_scene_change, "input_select.living_scene")
    self.listen_state(self.on_balcony_door_open, "binary_sensor.living_room_balcony_door", new="on", old="off")
    self.listen_state(self.on_balcony_door_close, "binary_sensor.living_room_balcony_door", new="off", old="on")
    self.listen_state(self.on_cover_change, "cover.living_room_cover", attribute="running")
    self.listen_event(self.on_close_living_room_cover, "close_living_room_cover")
    self.listen_state(self.on_cover_switch_change, "sensor.living_room_cover_switch")
    self.was_closed = False


  def on_cover_switch_change(self, entity, attribute, old, new, kwargs):
    if new not in ["open", "close"]:
      return
    self.turn_on_entity("input_boolean.living_room_cover_active")
    self.run_in(self.update_position, 4)


  def update_position(self, kwargs):
    position = self.get_state("cover.living_room_cover", attribute="current_position")
    if position != self.prev_position:
      self.call_service("mqtt/publish", topic="zigbee2mqtt/Living Room Cover/get", payload='{"state": ""}')
      self.turn_on_entity("input_boolean.living_room_cover_active")
      self.prev_position = position
      self.run_in(self.update_position, 4)
    else:
      self.turn_off_entity("input_boolean.living_room_cover_active")


  def on_cover_change(self, entity, attribute, old, new, kwargs):
    self.cancel_handle(self.handle)
    self.log(f"Cover running changed: {new}")
    if new is False:
      self.turn_off_entity("input_boolean.living_room_cover_active")
    elif new is True:
      self.turn_on_entity("input_boolean.living_room_cover_active")
      self.handle = self.run_in(self.stop_cover, 20)


  def stop_cover(self, kwargs):
    if self.get_state("cover.living_room_cover", attribute="running") is True:
      self.stop_cover("living_room_cover")


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
      self.was_closed = True
      self.open_living_room_cover()
    else:
      self.was_closed = False


  def on_balcony_door_close(self, entity, attribute, old, new, kwargs):
    if self.get_living_scene() in ["away", "night", "light_cinema", "dark_cinema", "party"] or self.was_closed:
      self.close_living_room_cover()


  def close_living_room_cover(self):
    if self.is_entity_off("binary_sensor.living_room_balcony_door"):
      self.log("Close cover")
      self.close_cover("living_room_cover")
    else:
      self.log("Cover will not be closed because balcony door is open")


  def open_living_room_cover(self):
    if self.is_cover_closed():
      self.log("Open cover")
      self.open_cover("living_room_cover")
    else:
      self.log("Cover not openning because it's aready open")


  def is_cover_closed(self):
    cover = self.get_state("cover.living_room_cover", attribute="all")
    cover_state = cover["state"]
    if "running" in cover["attributes"]:
      is_running = cover["attributes"]["running"]
    else:
      is_running = False
    if cover_state == "closed" or (cover_state == "open" and is_running):
      return True
    return False
