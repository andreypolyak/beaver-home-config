from room_lights import RoomLights


class LivingRoomLights(RoomLights):

  def initialize(self):
    self.zone = "living"
    self.room = "living_room"
    self.color_mode = "rgb"
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
    self.groups = {
      "group_living_room": [
        "group_living_room_top",
        "group_living_room_speakers",
        "living_room_sofa",
        "living_room_sofa_led"
      ],
      "group_living_room_dark_on": ["living_room_sofa", "living_room_sofa_led"],
      "group_living_room_dark_off": ["group_living_room_top", "group_living_room_speakers"],
      "group_living_room_light_cinema_on": ["group_living_room_top", "living_room_sofa_led"],
      "group_living_room_light_cinema_off": ["group_living_room_speakers", "living_room_sofa"],
    }
    self.lights = {
      "group_living_room_top": ["color", "brightness", "transition"],
      "group_living_room_speakers": ["color", "brightness", "transition"],
      "living_room_sofa": ["color", "brightness", "transition"],
      "living_room_sofa_led": ["color", "brightness", "transition"]
    }
    self.presets = {
      "BRIGHT": {
        "group_living_room_top": {"state": True, "brightness": 254},
        "group_living_room_speakers": {"state": True, "brightness": 254},
        "living_room_sofa": {"state": True, "brightness": 254},
        "living_room_sofa_led": {"state": True, "brightness": 254}
      },
      "DARK": {
        "group_living_room_top": {"state": False},
        "group_living_room_speakers": {"state": False},
        "living_room_sofa": {"state": True, "brightness": 3},
        "living_room_sofa_led": {"state": True, "brightness": 3}
      },
      "CINEMA": {
        "group_living_room_top": {"state": True, "brightness": 254},
        "group_living_room_speakers": {"state": False},
        "living_room_sofa_led": {"state": True, "brightness": 254},
        "living_room_sofa": {"state": False}
      },
      "OFF": {
        "group_living_room_top": {"state": False},
        "group_living_room_speakers": {"state": False},
        "living_room_sofa": {"state": False},
        "living_room_sofa_led": {"state": False}
      }
    }
    self.room_init()


  def on_day(self, scene, mode, new=None, old=None, entity=None):
    if mode == "new_scene":
      if old == "away":
        self.set_preset("BRIGHT")
      else:
        self.set_preset_if_on("BRIGHT")
    elif mode in ["motion_sensor", "door_sensor"] and new == "on" and self.auto_lights:
      self.set_preset_or_restore("BRIGHT")
    elif mode == "back_motion_sensor" and new == "on" and not self.cover_active and self.auto_lights:
      self.set_preset_or_restore("BRIGHT")
    elif mode == "switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT", new, set_cooldown=True)
    elif mode == "virtual_switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT", new)
    elif mode == "switch" and "brightness" in new:
      self.toggle_brightness(new)
    else:
      return False


  def on_night(self, scene, mode, new=None, old=None, entity=None):
    if mode == "new_scene":
      if old == "away":
        self.set_preset("DARK")
      else:
        self.set_preset("OFF")
    elif mode in ["motion_sensor", "door_sensor"] and new == "on" and self.auto_lights:
      if self.is_entity_on("binary_sensor.night_scene_enough"):
        self.set_preset("BRIGHT")
        self.set_living_scene("day")
      else:
        self.set_preset_or_restore("DARK", min_delay=True)
    elif mode == "back_motion_sensor" and new == "on" and not self.cover_active and self.auto_lights:
      if self.is_entity_on("binary_sensor.night_scene_enough"):
        self.set_preset("BRIGHT")
        self.set_living_scene("day")
      else:
        self.set_preset_or_restore("DARK", min_delay=True)
    elif mode == "switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT", new, set_cooldown=True)
    elif mode == "virtual_switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT", new)
    elif mode == "switch" and "brightness" in new:
      self.toggle_brightness(new, set_day=True)
    else:
      return False


  def on_dumb(self, scene, mode, new=None, old=None, entity=None):
    if mode in ["switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT", new)
    elif mode == "switch" and "brightness" in new:
      self.toggle_brightness(new)
    else:
      return False


  def on_party(self, scene, mode, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.set_preset("OFF", min_delay=True)
    elif mode == "old_scene":
      self.run_in(self.restore_lights, 1)
    elif mode in ["switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.set_living_scene("day")
    elif mode == "switch" and "brightness" in new:
      self.toggle_brightness(new, set_day=True)
    else:
      return False


  def on_light_cinema(self, scene, mode, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.set_preset("CINEMA", min_delay=True)
    elif mode in ["switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.set_living_scene("dark_cinema")
    elif mode == "switch" and "brightness" in new:
      self.toggle_brightness(new, set_day=True)
    else:
      return False


  def on_dark_cinema(self, scene, mode, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.set_preset("OFF", min_delay=True)
    elif mode in ["switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.set_living_scene("light_cinema")
    elif mode == "switch" and "brightness" in new:
      self.toggle_brightness(new, set_day=True)
    else:
      return False


  def on_away(self, scene, mode, new=None, old=None, entity=None):
    if mode == "virtual_switch":
      self.set_preset("OFF")
    else:
      return False


  @property
  def reason_to_keep_light(self):
    living_scene = self.living_scene
    if living_scene in ["dumb", "light_cinema", "dark_cinema", "party"]:
      return f"{living_scene}_scene"
    if not self.auto_lights:
      return "auto_lights_off"
    return None


  def restore_lights(self, kwargs):
    living_scene = self.living_scene
    if living_scene in ["day", "dumb"]:
      self.set_preset("BRIGHT")
    elif living_scene in ["night", "party"]:
      self.set_preset("DARK", min_delay=True)
    elif living_scene in ["light_cinema"]:
      self.set_preset("CINEMA")
    elif living_scene in ["away", "dark_cinema"]:
      self.set_preset("OFF")
