from room_lights import RoomLights


class BathroomEntranceLights(RoomLights):

  def initialize(self):
    self.zone = "living"
    self.room = "bathroom_entrance"
    self.delay = 240
    self.max_delay = 600
    self.min_delay = 30
    self.sensors = [
      ("binary_sensor.bathroom_shower_motion", "motion_sensor"),
      ("binary_sensor.entrance_front_motion", "motion_sensor"),
      ("binary_sensor.entrance_back_motion", "motion_sensor"),
      ("binary_sensor.bathroom_toilet_motion", "motion_sensor"),
      ("binary_sensor.entrance_door", "entrance_door_sensor"),
      ("binary_sensor.bathroom_door", "bathroom_door_sensor")
    ]
    self.switches = [
      ("sensor.living_room_switch", "switch")
    ]
    self.turn_off_lights = [
      "group_bathroom_entrance_color",
      "bathroom_mirror"
    ]
    self.lights = {
      "group_bathroom_entrance_color": ["group_entrance_top", "group_bathroom_top", "group_entrance_mirror"],
      "bathroom_mirror": []
    }
    self.presets = {
      "BRIGHT": {
        "group_bathroom_entrance_color": {"state": "on", "attributes": {"brightness": 254}},
        "bathroom_mirror": {"state": "on"}
      },
      "NIGHT": {
        "group_entrance_mirror": {"state": "on", "attributes": {"brightness": 3}},
        "group_bathroom_top": {"state": "on", "attributes": {"brightness": 3}},
        "group_entrance_top": {"state": "off"},
        "bathroom_mirror": {"state": "off"}
      },
      "DARK": {
        "group_bathroom_entrance_color": {"state": "on", "attributes": {"brightness": 3}},
        "bathroom_mirror": {"state": "off"}
      },
      "NIGHT_ENTRANCE_BRIGHT_BATHROOM": {
        "group_bathroom_top": {"state": "on", "attributes": {"brightness": 254}},
        "bathroom_mirror": {"state": "on"},
        "group_entrance_mirror": {"state": "on", "attributes": {"brightness": 3}},
        "group_entrance_top": {"state": "off"}
      },
      "DARK_ENTRANCE_BRIGHT_BATHROOM": {
        "group_bathroom_top": {"state": "on", "attributes": {"brightness": 254}},
        "bathroom_mirror": {"state": "on"},
        "group_entrance_mirror": {"state": "on", "attributes": {"brightness": 3}},
        "group_entrance_top": {"state": "on", "attributes": {"brightness": 3}}
      }
    }
    self.room_init()


  def on_day(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      if old == "away":
        self.turn_preset("BRIGHT", mode, state)
      else:
        self.turn_preset_if_on("BRIGHT", mode, state)
    elif mode in ["motion_sensor", "entrance_door_sensor"] and new == "on" and self.is_auto_lights():
      self.turn_preset_or_restore("BRIGHT", mode, state)
    elif mode in ["bathroom_door_sensor"] and new in ["on", "off"] and self.is_auto_lights():
      self.turn_preset_or_restore("BRIGHT", mode, state)
    elif mode == "virtual_switch":
      self.light_toggle("BRIGHT", new, mode, state)
    else:
      return False


  def on_night(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      if self.is_door_open(state, "bathroom_door") and old == "away":
        self.turn_preset("NIGHT", mode, state)
      elif not self.is_door_open(state, "bathroom_door") and old == "away":
        self.turn_preset("NIGHT_ENTRANCE_BRIGHT_BATHROOM", mode, state)
      elif self.is_door_open(state, "bathroom_door"):
        self.turn_off_all(state)
      elif not self.is_door_open(state, "bathroom_door"):
        self.turn_preset_if_on("NIGHT", mode, state, min_delay=True)
    elif mode in ["motion_sensor", "entrance_door_sensor"] and new == "on" and self.is_auto_lights():
      if self.get_state("binary_sensor.night_scene_in_living_zone_enough") == "on":
        self.turn_preset("BRIGHT", mode, state)
        self.turn_on_scene("day")
      elif self.is_door_open(state, "bathroom_door"):
        self.turn_preset_or_restore("NIGHT", mode, state, min_delay=True)
      else:
        self.turn_preset_or_restore("NIGHT_ENTRANCE_BRIGHT_BATHROOM", mode, state)
    elif mode == "bathroom_door_sensor" and new == "off" and self.is_auto_lights():
      self.turn_preset_if_on("NIGHT_ENTRANCE_BRIGHT_BATHROOM", mode, state)
    elif mode == "bathroom_door_sensor" and new == "on" and self.is_auto_lights():
      self.turn_preset_if_on("NIGHT", mode, state, min_delay=True)
    elif mode == "virtual_switch":
      if self.is_door_open(state, "bathroom_door"):
        self.light_toggle("NIGHT", new, mode, state)
      else:
        self.light_toggle("NIGHT_ENTRANCE_BRIGHT_BATHROOM", new, mode, state)
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
      if old == "away":
        self.turn_preset("DARK_ENTRANCE_BRIGHT_BATHROOM", mode, state, min_delay=True)
      else:
        self.turn_preset_if_on("DARK_ENTRANCE_BRIGHT_BATHROOM", mode, state, min_delay=True)
    elif mode in ["motion_sensor", "entrance_door_sensor"] and new == "on" and self.is_auto_lights():
      self.turn_preset_or_restore("DARK_ENTRANCE_BRIGHT_BATHROOM", mode, state, min_delay=True)
    elif mode == "bathroom_door_sensor" and new in ["on", "off"] and self.is_auto_lights():
      self.turn_preset_or_restore("DARK_ENTRANCE_BRIGHT_BATHROOM", mode, state, min_delay=True)
    elif mode == "virtual_switch":
      self.light_toggle("DARK_ENTRANCE_BRIGHT_BATHROOM", new, mode, state, min_delay=True)
    else:
      return False


  def on_light_cinema(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      if old == "away":
        self.turn_preset("BRIGHT", mode, state)
      else:
        self.turn_preset_if_on("BRIGHT", mode, state)
    elif mode in ["motion_sensor", "entrance_door_sensor"] and new == "on" and self.is_auto_lights():
      self.turn_preset_or_restore("BRIGHT", mode, state)
    elif mode == "bathroom_door_sensor" and new in ["on", "off"] and self.is_auto_lights():
      self.turn_preset_or_restore("BRIGHT", mode, state)
    elif mode == "virtual_switch":
      self.light_toggle("BRIGHT", new, mode, state)
    else:
      return False


  def on_dark_cinema(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      if old == "away":
        self.turn_preset("DARK_ENTRANCE_BRIGHT_BATHROOM", mode, state, min_delay=True)
      else:
        self.turn_preset_if_on("DARK_ENTRANCE_BRIGHT_BATHROOM", mode, state, min_delay=True)
    elif mode in ["motion_sensor", "entrance_door_sensor"] and new == "on" and self.is_auto_lights():
      self.turn_preset_or_restore("DARK_ENTRANCE_BRIGHT_BATHROOM", mode, state, min_delay=True)
    elif mode == "bathroom_door_sensor" and new in ["on", "off"] and self.is_auto_lights():
      self.turn_preset_or_restore("DARK_ENTRANCE_BRIGHT_BATHROOM", mode, state, min_delay=True)
    elif mode == "virtual_switch":
      self.light_toggle("DARK_ENTRANCE_BRIGHT_BATHROOM", new, mode, state, min_delay=True)
    else:
      return False


  def on_away(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "virtual_switch":
      self.turn_off_all(state)
    else:
      return False


  def should_turn_off_by_timer(self):
    if self.get_state(f"input_select.{self.zone}_scene") == "dumb":
      return "dumb_scene"
    if self.is_person_inside():
      return "person_inside"
    if not self.is_auto_lights():
      return "auto_lights_off"
    try:
      humidity = float(self.get_state("sensor.bathroom_humidity"))
    except (TypeError, ValueError):
      humidity = 0
    if humidity > 60:
      return "humidity"
    return None
