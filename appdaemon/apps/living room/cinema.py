from base import Base


class Cinema(Base):

  def initialize(self):
    super().initialize()
    default = {
      "dark_cinema_turned_on_ts": 0,
      "dark_cinema_turned_off_ts": 0,
      "auto_scene_change_ts": 0,
      "media_played_ever_in_session": False,
      "auto_cinema_session_disabled": False
    }
    self.init_storage("cinema", "data", default)
    self.listen_event(self.on_dark_cinema_action, event="mobile_app_notification_action", action="DARK_CINEMA_TURN_ON")
    self.listen_state(self.on_tv_turned_on, "binary_sensor.living_room_tv", new="on", old="off")
    self.listen_state(self.on_tv_turned_off, "binary_sensor.living_room_tv", new="off", old="on")
    self.listen_state(self.on_cinema_session_turned_off, "input_boolean.cinema_session", new="off", old="on")
    self.listen_state(self.on_apple_tv_change, "media_player.living_room_apple_tv", attribute="all")
    self.listen_state(self.on_living_scene_change, "input_select.living_scene")

    for binary_sensor in self.get_state("binary_sensor"):
      if (
        binary_sensor.endswith("_motion")
        and ("kitchen" in binary_sensor or "bathroom" in binary_sensor or "entrance" in binary_sensor)
        and "camera" not in binary_sensor
      ):
        self.listen_state(self.on_motion, binary_sensor, new="on", old="off")


  def on_living_scene_change(self, entity, attribute, old, new, kwargs):
    auto_scene_change_ts = self.read_storage("data", attribute="auto_scene_change_ts")
    if new != "dark_cinema":
      if self.get_delta_ts(auto_scene_change_ts) > 1:
        self.turn_off_entity("input_boolean.cinema_session")
      self.write_storage("data", self.get_now_ts(), attribute="dark_cinema_turned_off_ts")
    if new in ["night", "away"]:
      self.turn_on_entity("script.tv_turn_off")
    elif new == "dark_cinema":
      self.write_storage("data", self.get_now_ts(), attribute="dark_cinema_turned_on_ts")
      self.turn_on_entity("input_boolean.cinema_session")
      self.turn_on_tv()
    elif new == "light_cinema":
      self.turn_on_tv()
    elif new == "day":
      self.turn_off_entity("input_boolean.cinema_session")


  def on_motion(self, entity, attribute, old, new, kwargs):
    dark_cinema_turned_on_ts = self.read_storage("data", attribute="dark_cinema_turned_on_ts")
    media_played_ever_in_session = self.read_storage("data", attribute="media_played_ever_in_session")
    universal_tv_source = self.get_state("input_select.current_universal_tv_source")
    if (
      self.get_state("media_player.living_room_apple_tv") == "paused"
      and self.living_scene == "dark_cinema"
      and self.get_delta_ts(dark_cinema_turned_on_ts) > 5
      and media_played_ever_in_session
      and universal_tv_source == "apple_tv"
    ):
      self.log(f"Turning light cinema scene because motion occured on {entity}")
      self.turn_on_scene("light_cinema")


  def on_apple_tv_change(self, entity, attribute, old, new, kwargs):
    apple_tv = self.get_state("media_player.living_room_apple_tv", attribute="all")
    dark_cinema_turned_on_ts = self.read_storage("data", attribute="dark_cinema_turned_on_ts")
    dark_cinema_turned_off_ts = self.read_storage("data", attribute="dark_cinema_turned_off_ts")
    auto_cinema_session_disabled = self.read_storage("data", attribute="auto_cinema_session_disabled")
    universal_tv_source = self.get_state("input_select.current_universal_tv_source")

    if (
      apple_tv["state"] == "playing"
      and self.living_scene != "dark_cinema"
      and self.entity_is_on("input_boolean.cinema_session")
      and self.get_delta_ts(dark_cinema_turned_off_ts) < 1800
    ):
      self.log("Apple TV is now playing, turn on dark cinema scene")
      self.turn_on_scene("dark_cinema")
    elif (
      apple_tv["state"] == "playing"
      and self.living_scene != "dark_cinema"
      and self.entity_is_on("input_boolean.cinema_session")
      and self.get_delta_ts(dark_cinema_turned_off_ts) >= 1800
    ):
      self.log("Cinema session expired")
      self.turn_off_entity("input_boolean.cinema_session")
    elif (
      apple_tv["state"] not in ["playing", "paused"]
      and self.living_scene == "dark_cinema"
      and self.get_delta_ts(dark_cinema_turned_on_ts) > 5
      and universal_tv_source == "apple_tv"
    ):
      self.log("Stopped watching, turn on light cinema scene")
      self.turn_on_scene("light_cinema")
    elif (
      apple_tv["state"] == "playing"
      and "app_id" in apple_tv["attributes"] and "cncrt" in apple_tv["attributes"]["app_id"]
      and "media_duration" in apple_tv["attributes"] and float(apple_tv["attributes"]["media_duration"]) > 3600
      and self.living_scene == "light_cinema"
      and not auto_cinema_session_disabled
    ):
      self.log("Movie is being watched, turn on dark cinema scene")
      self.turn_on_scene("dark_cinema")
    if apple_tv["state"] == "playing" and "media_duration" in apple_tv["attributes"]:
      self.write_storage("data", True, attribute="media_played_ever_in_session")


  def on_dark_cinema_action(self, event_name, data, kwargs):
    self.turn_on_scene("dark_cinema")


  def on_tv_turned_on(self, entity, attribute, old, new, kwargs):
    if self.living_scene in ["dark_cinema", "party"]:
      return
    self.turn_on_scene("light_cinema")
    actions = [{"action": "DARK_CINEMA_TURN_ON", "title": "🌑 Turn on dark cinema scene", "destructive": True}]
    message = "🎦 Do you want to turn on dark cinema scene?"
    self.send_push("home_or_none", message, "cinema", actions=actions)


  def on_tv_turned_off(self, entity, attribute, old, new, kwargs):
    dark_cinema_turned_on_ts = self.read_storage("data", attribute="dark_cinema_turned_on_ts")
    self.turn_off_entity("input_boolean.cinema_session")
    self.write_storage("data", False, attribute="media_played_ever_in_session")
    self.write_storage("data", False, attribute="auto_cinema_session_disabled")
    if (
      self.living_scene in ["light_cinema", "dark_cinema"]
      and self.get_delta_ts(dark_cinema_turned_on_ts) > 5
    ):
      self.turn_on_scene("day")


  def on_cinema_session_turned_off(self, entity, attribute, old, new, kwargs):
    if self.entity_is_on("binary_sensor.living_room_tv"):
      self.write_storage("data", True, attribute="auto_cinema_session_disabled")


  def turn_on_scene(self, scene):
    self.write_storage("data", self.get_now_ts(), attribute="auto_scene_change_ts")
    self.set_living_scene(scene)


  def turn_on_tv(self):
    if self.entity_is_off("binary_sensor.living_room_tv"):
      self.call_service("script/tv_turn_on")
