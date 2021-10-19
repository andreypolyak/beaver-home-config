from room_lights import RoomLights


class KitchenLights(RoomLights):

  def initialize(self):
    self.zone = "living"
    self.room = "kitchen"
    self.color_mode = "rgb"
    self.delay = 240
    self.max_delay = 600
    self.min_delay = 30
    self.sensors = [
      ("binary_sensor.kitchen_center_motion", "motion_sensor"),
      ("binary_sensor.kitchen_back_motion", "add_motion_sensor"),
      ("binary_sensor.bedroom_door", "door_sensor"),
      ("binary_sensor.entrance_door", "door_sensor"),
      ("binary_sensor.kitchen_chair_1_occupancy", "chair_sensor"),
      ("binary_sensor.kitchen_chair_2_occupancy", "chair_sensor")
    ]
    self.switches = [
      ("sensor.kitchen_switch", "switch")
    ]
    self.groups = {
      "group_kitchen_color": ["group_kitchen_top", "kitchen_table"]
    }
    self.lights = {
      "group_kitchen_top": ["color", "brightness", "transition"],
      "kitchen_table": ["color", "brightness", "transition"],
      "kitchen_vent": []
    }
    self.presets = {
      "BRIGHT": {
        "group_kitchen_top": {"state": True, "brightness": 254},
        "kitchen_table": {"state": True, "brightness": 254},
        "kitchen_vent": {"state": True}
      },
      "BRIGHT_CINEMA": {
        "group_kitchen_top": {"state": True, "brightness": 254},
        "kitchen_table": {"state": False},
        "kitchen_vent": {"state": True}
      },
      "DARK": {
        "group_kitchen_top": {"state": True, "brightness": 3},
        "kitchen_table": {"state": False},
        "kitchen_vent": {"state": True}
      },
      "NIGHT": {
        "group_kitchen_top": {"state": False},
        "kitchen_table": {"state": True, "brightness": 3},
        "kitchen_vent": {"state": False}
      },
      "OFF": {
        "group_kitchen_top": {"state": False},
        "kitchen_table": {"state": False},
        "kitchen_vent": {"state": False}
      }
    }
    self.room_init()


  def on_day(self, scene, mode, new=None, old=None):
    if mode == "new_scene":
      self.set_preset_if_on("BRIGHT")
    elif mode in ["add_motion_sensor", "door_sensor", "chair_sensor"] and new == "on" and not self.lock_lights:
      self.set_preset_or_restore("BRIGHT")
    elif mode == "motion_sensor" and new == "on" and not self.cover_active and not self.lock_lights:
      self.set_preset_or_restore("BRIGHT")
    elif mode == "switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT", new, set_cooldown=True)
    elif mode == "virtual_switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT", new)
    elif mode == "switch" and "brightness" in new:
      self.toggle_brightness(new)
    else:
      return False


  def on_night(self, scene, mode, new=None, old=None):
    if mode == "new_scene":
      self.set_preset("OFF")
    elif mode in ["add_motion_sensor", "door_sensor", "chair_sensor"] and new == "on" and not self.lock_lights:
      if self.entity_is_on("binary_sensor.night_scene_enough"):
        self.set_preset("BRIGHT")
        self.set_living_scene("day")
      else:
        self.set_preset_or_restore("NIGHT", min_delay=True)
    elif mode == "motion_sensor" and new == "on" and not self.cover_active and not self.lock_lights:
      if self.entity_is_on("binary_sensor.night_scene_enough"):
        self.set_preset("BRIGHT")
        self.set_living_scene("day")
      else:
        self.set_preset_or_restore("NIGHT", min_delay=True)
    elif mode == "switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT", new, set_cooldown=True)
    elif mode == "virtual_switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT", new)
    elif mode == "switch" and "brightness" in new:
      self.toggle_brightness(new, set_day=True)
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
      self.set_preset_if_on("DARK", min_delay=True)
    elif mode in ["add_motion_sensor", "door_sensor", "chair_sensor"] and new == "on" and not self.lock_lights:
      self.set_preset_or_restore("DARK", min_delay=True)
    elif mode == "motion_sensor" and new == "on" and not self.cover_active and not self.lock_lights:
      self.set_preset_or_restore("DARK", min_delay=True)
    elif mode == "switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("DARK", new, min_delay=True, set_cooldown=True)
    elif mode == "virtual_switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("DARK", new, min_delay=True)
    elif mode == "switch" and "brightness" in new:
      self.toggle_brightness(new, set_day=True)
    else:
      return False


  def on_light_cinema(self, scene, mode, new=None, old=None):
    if mode == "new_scene":
      self.set_preset_if_on("BRIGHT_CINEMA")
    elif mode in ["add_motion_sensor", "door_sensor", "chair_sensor"] and new == "on" and not self.lock_lights:
      self.set_preset_or_restore("BRIGHT_CINEMA")
    elif mode == "motion_sensor" and new == "on" and not self.cover_active and not self.lock_lights:
      self.set_preset_or_restore("BRIGHT_CINEMA")
    elif mode == "switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT_CINEMA", new, min_delay=True, set_cooldown=True)
    elif mode == "virtual_switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT_CINEMA", new, min_delay=True)
    elif mode == "switch" and "brightness" in new:
      self.toggle_brightness(new)
    else:
      return False


  def on_dark_cinema(self, scene, mode, new=None, old=None):
    if mode == "new_scene":
      self.set_preset_if_on("DARK", min_delay=True)
    elif mode in ["add_motion_sensor", "door_sensor", "chair_sensor"] and new == "on" and not self.lock_lights:
      self.set_preset_or_restore("DARK", min_delay=True)
    elif mode == "motion_sensor" and new == "on" and not self.cover_active and not self.lock_lights:
      self.set_preset_or_restore("DARK", min_delay=True)
    elif mode == "switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("DARK", new, min_delay=True, set_cooldown=True)
    elif mode == "virtual_switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("DARK", new, min_delay=True)
    elif mode == "switch" and "brightness" in new:
      self.toggle_brightness(new, set_day=True)
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
    if self.lock_lights:
      return "lock_lights_on"
    if (
      self.entity_is_on("binary_sensor.kitchen_chair_1_occupancy")
      or self.entity_is_on("binary_sensor.kitchen_chair_2_occupancy")
    ):
      return "chair_occupied"
    return None
