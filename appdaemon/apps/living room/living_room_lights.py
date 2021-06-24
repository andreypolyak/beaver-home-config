from room_lights import RoomLights


class LivingRoomLights(RoomLights):

  def initialize(self):
    self.zone = "living"
    self.room = "living_room"
    self.delay = 1200
    self.max_delay = 1800
    self.min_delay = 30
    self.sensors = [
      ("binary_sensor.living_room_front_motion", "motion_sensor"),
      ("binary_sensor.living_room_back_motion", "back_motion_sensor"),
      ("binary_sensor.living_room_middle_motion", "motion_sensor"),
      ("binary_sensor.entrance_door", "door_sensor"),
      ("binary_sensor.bedroom_door", "door_sensor")
    ]
    self.switches = [
      ("sensor.living_room_switch", "switch")
    ]
    self.turn_off_lights = [
      "group_living_room",
      "living_room_sofa_led_rgb"
    ]
    self.lights = {
      "group_living_room": [
        "group_living_room_top",
        "group_living_room_speakers",
        "living_room_sofa"
      ],
      "living_room_sofa_led_rgb": []
    }
    self.presets = {
      "BRIGHT": {
        "group_living_room": {"state": "on", "attributes": {"brightness": 254}},
        "living_room_sofa_led_rgb": {"state": "on", "attributes": {"brightness": 254}}
      },
      "DARK": {
        "group_living_room_dark_on": {"state": "on", "attributes": {"brightness": 3}},
        "group_living_room_dark_off": {"state": "off"},
        "living_room_sofa_led_rgb": {"state": "on", "attributes": {"brightness": 3}}
      },
      "CINEMA": {
        "group_living_room_light_cinema_on": {"state": "on", "attributes": {"brightness": 254}},
        "group_living_room_light_cinema_off": {"state": "off"},
        "living_room_sofa_led_rgb": {"state": "on", "attributes": {"brightness": 254}}
      },
      "OFF": {
        "group_living_room": {"state": "off"},
        "living_room_sofa_led_rgb": {"state": "off"}
      }
    }
    self.room_init()


  def on_day(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      if old == "away":
        self.turn_preset("BRIGHT", mode, state)
      else:
        self.turn_preset_if_on("BRIGHT", mode, state)
    elif mode in ["motion_sensor", "door_sensor"] and new == "on" and self.is_auto_lights():
      self.turn_preset_or_restore("BRIGHT", mode, state)
    elif mode == "back_motion_sensor" and new == "on" and not self.is_cover_active() and self.is_auto_lights():
      self.turn_preset_or_restore("BRIGHT", mode, state)
    elif mode in ["switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.light_toggle("BRIGHT", new, mode, state)
    elif mode == "switch" and "brightness" in new:
      self.toggle_brightness(new, state)
    else:
      return False


  def on_night(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      if old == "away":
        self.turn_preset("DARK", mode, state)
      else:
        self.turn_off_all(state)
    elif mode in ["motion_sensor", "door_sensor"] and new == "on" and self.is_auto_lights():
      if self.get_state("binary_sensor.night_scene_in_living_zone_turned_on_long_enough") == "on":
        self.turn_preset("BRIGHT", mode, state)
        self.turn_on_scene("day")
      else:
        self.turn_preset_or_restore("DARK", mode, state, min_delay=True)
    elif mode == "back_motion_sensor" and new == "on" and not self.is_cover_active() and self.is_auto_lights():
      if self.get_state("binary_sensor.night_scene_in_living_zone_turned_on_long_enough") == "on":
        self.turn_preset("BRIGHT", mode, state)
        self.turn_on_scene("day")
      else:
        self.turn_preset_or_restore("DARK", mode, state, min_delay=True)
    elif mode in ["switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.night_scene_light_toggle("BRIGHT", new, mode, state)
    elif mode == "switch" and "brightness" in new:
      self.overwrite_scene(new, "day", "BRIGHT", state)
    else:
      return False


  def on_dumb(self, scene, mode, state, new=None, old=None, entity=None):
    if mode in ["switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.light_toggle("BRIGHT", new, mode, state)
    elif mode == "switch" and "brightness" in new:
      self.toggle_brightness(new, state)
    else:
      return False


  def on_party(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.turn_preset("OFF", mode, state, min_delay=True)
    elif mode == "old_scene":
      self.run_in(self.restore_lights, 1)
    elif mode in ["switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.turn_on_scene("day")
    elif mode == "switch" and "brightness" in new:
      self.overwrite_scene(new, "day", "BRIGHT", state)
    else:
      return False


  def on_light_cinema(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.turn_preset("CINEMA", mode, state, min_delay=True)
    elif mode in ["switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.turn_on_scene("dark_cinema")
    elif mode == "switch" and "brightness" in new:
      self.overwrite_scene(new, "day", "BRIGHT", state)
    else:
      return False


  def on_dark_cinema(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.turn_preset("OFF", mode, state, min_delay=True)
    elif mode in ["switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.turn_on_scene("light_cinema")
    elif mode == "switch" and "brightness" in new:
      self.overwrite_scene(new, "day", "BRIGHT", state)
    else:
      return False


  def on_away(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "virtual_switch":
      self.turn_off_all(state)
    else:
      return False


  def should_turn_off_by_timer(self):
    do_not_turn_off_scenes = ["dumb", "light_cinema", "dark_cinema", "party"]
    for scene in do_not_turn_off_scenes:
      if self.get_state(f"input_select.{self.zone}_scene") == scene:
        return f"{scene}_scene"
    if self.is_person_inside():
      return "person_inside"
    if not self.is_auto_lights():
      return "auto_lights_off"
    return None


  def restore_lights(self, kwargs):
    state = self.get_lights_state()
    mode = "restore"
    current_scene = self.get_state("input_select.living_scene")
    if current_scene in ["day", "dumb"]:
      self.turn_preset("BRIGHT", mode, state)
    elif current_scene in ["night", "party"]:
      self.turn_preset("DARK", mode, state, min_delay=True)
    elif current_scene in ["light_cinema"]:
      self.turn_preset("CINEMA", mode, state)
    elif current_scene in ["away", "dark_cinema"]:
      self.turn_preset("OFF", mode, state)
