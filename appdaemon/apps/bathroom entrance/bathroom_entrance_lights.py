from room_lights import RoomLights


class BathroomEntranceLights(RoomLights):

  def initialize(self):
    self.zone = "living"
    self.room = "bathroom_entrance"
    self.color_mode = "rgb"
    self.delay = 240
    self.max_delay = 600
    self.min_delay = 30
    self.sensors = [
      ("binary_sensor.bathroom_shower_motion", "motion_sensor"),
      ("binary_sensor.entrance_center_motion", "motion_sensor"),
      ("binary_sensor.bathroom_toilet_motion", "motion_sensor"),
      ("binary_sensor.entrance_door", "entrance_door_sensor"),
      ("binary_sensor.bathroom_door", "bathroom_door_sensor"),
      ("binary_sensor.bathroom_toilet_occupancy", "occupancy_sensor")
    ]
    self.switches = [
      ("sensor.living_room_switch", "switch")
    ]
    self.groups = {
      "group_bathroom_entrance_color": ["group_bathroom_top", "group_entrance_top", "group_entrance_mirror"]
    }
    self.lights = {
      "group_bathroom_top": ["color", "brightness", "transition"],
      "group_entrance_top": ["color", "brightness", "transition"],
      "group_entrance_mirror": ["color", "brightness", "transition"],
      "bathroom_mirror": []
    }
    self.presets = {
      "BRIGHT": {
        "group_bathroom_top": {"state": True, "brightness": 254},
        "group_entrance_top": {"state": True, "brightness": 254},
        "group_entrance_mirror": {"state": True, "brightness": 254},
        "bathroom_mirror": {"state": True}
      },
      "NIGHT": {
        "group_bathroom_top": {"state": True, "brightness": 3},
        "group_entrance_top": {"state": False},
        "group_entrance_mirror": {"state": True, "brightness": 3},
        "bathroom_mirror": {"state": False}
      },
      "DARK": {
        "group_bathroom_top": {"state": True, "brightness": 254},
        "group_entrance_top": {"state": True, "brightness": 3},
        "group_entrance_mirror": {"state": True, "brightness": 3},
        "bathroom_mirror": {"state": False}
      },
      "NIGHT_ENTRANCE_BRIGHT_BATHROOM": {
        "group_bathroom_top": {"state": True, "brightness": 254},
        "group_entrance_top": {"state": False},
        "group_entrance_mirror": {"state": True, "brightness": 3},
        "bathroom_mirror": {"state": True}
      },
      "DARK_ENTRANCE_BRIGHT_BATHROOM": {
        "group_bathroom_top": {"state": True, "brightness": 254},
        "group_entrance_top": {"state": True, "brightness": 3},
        "group_entrance_mirror": {"state": True, "brightness": 3},
        "bathroom_mirror": {"state": True}
      },
      "OFF": {
        "group_bathroom_top": {"state": False},
        "group_entrance_top": {"state": False},
        "group_entrance_mirror": {"state": False},
        "bathroom_mirror": {"state": False}
      },
    }
    self.room_init()


  def on_day(self, scene, mode, new=None, old=None):
    if mode == "new_scene":
      if old == "away":
        self.set_preset("BRIGHT")
      else:
        self.set_preset_if_on("BRIGHT")
    elif mode in ["motion_sensor", "occupancy_sensor", "entrance_door_sensor"] and new == "on" and not self.lock_lights:
      self.set_preset_or_restore("BRIGHT")
    elif mode in ["bathroom_door_sensor"] and new in ["on", "off"] and not self.lock_lights:
      self.set_preset_or_restore("BRIGHT")
    elif mode == "virtual_switch":
      self.toggle_preset("BRIGHT", new)
    else:
      return False


  def on_night(self, scene, mode, new=None, old=None):
    if mode == "new_scene":
      if self.bathroom_door_open and old == "away":
        self.set_preset("NIGHT")
      elif not self.bathroom_door_open and old == "away":
        self.set_preset("NIGHT_ENTRANCE_BRIGHT_BATHROOM")
      elif self.bathroom_door_open:
        self.set_preset("OFF")
      elif not self.bathroom_door_open:
        self.set_preset_if_on("NIGHT", min_delay=True)
    elif mode in ["motion_sensor", "occupancy_sensor", "entrance_door_sensor"] and new == "on" and not self.lock_lights:
      if self.entity_is_on("binary_sensor.night_scene_enough"):
        self.set_preset("BRIGHT")
        self.set_living_scene("day")
      elif self.bathroom_door_open:
        self.set_preset_or_restore("NIGHT", min_delay=True)
      else:
        self.set_preset_or_restore("NIGHT_ENTRANCE_BRIGHT_BATHROOM")
    elif mode == "bathroom_door_sensor" and new == "off" and not self.lock_lights:
      self.set_preset_if_on("NIGHT_ENTRANCE_BRIGHT_BATHROOM")
    elif mode == "bathroom_door_sensor" and new == "on" and not self.lock_lights:
      self.set_preset_if_on("NIGHT", min_delay=True)
    elif mode == "virtual_switch":
      if self.bathroom_door_open:
        self.toggle_preset("NIGHT", new)
      else:
        self.toggle_preset("NIGHT_ENTRANCE_BRIGHT_BATHROOM", new)
    else:
      return False


  def on_dumb(self, scene, mode, new=None, old=None):
    if mode in ["switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT", new)
    elif mode == "switch" and "brightness" in new:
      self.toggle_brightness(new)
    else:
      return False


  def on_party(self, scene, mode, new=None, old=None):
    if mode == "new_scene":
      if old == "away":
        self.set_preset("DARK_ENTRANCE_BRIGHT_BATHROOM", min_delay=True)
      else:
        self.set_preset_if_on("DARK_ENTRANCE_BRIGHT_BATHROOM", min_delay=True)
    elif mode in ["motion_sensor", "occupancy_sensor", "entrance_door_sensor"] and new == "on" and not self.lock_lights:
      self.set_preset_or_restore("DARK_ENTRANCE_BRIGHT_BATHROOM", min_delay=True)
    elif mode == "bathroom_door_sensor" and new in ["on", "off"] and not self.lock_lights:
      self.set_preset_or_restore("DARK_ENTRANCE_BRIGHT_BATHROOM", min_delay=True)
    elif mode == "virtual_switch":
      self.toggle_preset("DARK_ENTRANCE_BRIGHT_BATHROOM", new, min_delay=True)
    else:
      return False


  def on_light_cinema(self, scene, mode, new=None, old=None):
    if mode == "new_scene":
      if old == "away":
        self.set_preset("BRIGHT")
      else:
        self.set_preset_if_on("BRIGHT")
    elif mode in ["motion_sensor", "occupancy_sensor", "entrance_door_sensor"] and new == "on" and not self.lock_lights:
      self.set_preset_or_restore("BRIGHT")
    elif mode == "bathroom_door_sensor" and new in ["on", "off"] and not self.lock_lights:
      self.set_preset_or_restore("BRIGHT")
    elif mode == "virtual_switch":
      self.toggle_preset("BRIGHT", new)
    else:
      return False


  def on_dark_cinema(self, scene, mode, new=None, old=None):
    if mode == "new_scene":
      if self.bathroom_door_open and old == "away":
        self.set_preset("DARK", min_delay=True)
      elif not self.bathroom_door_open and old == "away":
        self.set_preset("DARK_ENTRANCE_BRIGHT_BATHROOM")
      elif self.bathroom_door_open:
        self.set_preset_if_on("DARK", min_delay=True)
      elif not self.bathroom_door_open:
        self.set_preset_if_on("DARK_ENTRANCE_BRIGHT_BATHROOM")
    elif mode in ["motion_sensor", "occupancy_sensor", "entrance_door_sensor"] and new == "on" and not self.lock_lights:
      if self.bathroom_door_open:
        self.set_preset_or_restore("DARK", min_delay=True)
      else:
        self.set_preset_or_restore("DARK_ENTRANCE_BRIGHT_BATHROOM")
    elif mode == "bathroom_door_sensor" and new == "off" and not self.lock_lights:
      self.set_preset_if_on("DARK_ENTRANCE_BRIGHT_BATHROOM")
    elif mode == "bathroom_door_sensor" and new == "on" and not self.lock_lights:
      self.set_preset_if_on("DARK", min_delay=True)
    elif mode == "virtual_switch":
      if self.bathroom_door_open:
        self.toggle_preset("DARK", new)
      else:
        self.toggle_preset("DARK_ENTRANCE_BRIGHT_BATHROOM", new)
    else:
      return False


  def on_away(self, scene, mode, new=None, old=None):
    if mode == "virtual_switch":
      self.toggle_on_away()
    else:
      return False


  @property
  def reason_to_keep_light(self):
    if self.living_scene == "dumb":
      return "dumb_scene"
    if self.person_inside:
      return "person_inside"
    if self.lock_lights:
      return "lock_lights_on"
    humidity = self.get_float_state("sensor.bathroom_humidity")
    if not self.bathroom_door_open and humidity is not None and humidity > 60:
      return "humidity"
    if self.entity_is_on("binary_sensor.bathroom_toilet_occupancy"):
      return "toilet_occupied"
    return None


  @property
  def bathroom_door_open(self):
    return self.entity_is_on("binary_sensor.bathroom_door")
