from room_lights import RoomLights


class BedroomLights(RoomLights):

  def initialize(self):
    self.zone = "sleeping"
    self.room = "bedroom"
    self.color_mode = "rgb"
    self.delay = 240
    self.max_delay = 600
    self.min_delay = 30
    self.sensors = [
      ("binary_sensor.bedroom_bed_motion", "motion_sensor"),
      ("binary_sensor.bedroom_table_motion", "table_motion_sensor"),
      ("binary_sensor.bedroom_floor_top_motion", "floor_motion_sensor"),
      ("binary_sensor.bedroom_floor_bottom_motion", "floor_motion_sensor"),
      ("binary_sensor.bedroom_door", "door_sensor"),
      ("binary_sensor.bedroom_chair_occupancy", "chair_sensor"),
      ("binary_sensor.bedroom_bed_occupancy", "bed_sensor"),
      ("binary_sensor.bedroom_theo_bed_occupancy", "bed_sensor")
    ]
    self.switches = [
      ("sensor.bedroom_theo_switch", "theo_switch"),
      ("sensor.bedroom_switch", "switch")
    ]
    self.ignore_fade_lights = ["bedroom_table"]
    self.groups = {
      "group_bedroom_bri": ["group_bedroom_adult_top", "group_bedroom_theo_top", "bedroom_bed_led", "bedroom_wardrobe"],
      "group_bedroom_color": ["group_bedroom_adult_top", "group_bedroom_theo_top", "bedroom_bed_led"],
      "group_bedroom_top": ["group_bedroom_adult_top", "group_bedroom_theo_top"]
    }
    self.lights = {
      "group_bedroom_adult_top": ["color", "brightness", "transition"],
      "group_bedroom_theo_top": ["color", "brightness", "transition"],
      "bedroom_bed_led": ["color", "brightness", "transition"],
      "bedroom_wardrobe": ["brightness", "transition"],
      "bedroom_table": []
    }
    self.presets = {
      "BRIGHT": {
        "group_bedroom_adult_top": {"state": True, "brightness": 254},
        "group_bedroom_theo_top": {"state": True, "brightness": 254},
        "bedroom_bed_led": {"state": True, "brightness": 254},
        "bedroom_wardrobe": {"state": True, "brightness": 254},
        "bedroom_table": {"state": True}
      },
      "DARK": {
        "group_bedroom_adult_top": {"state": False},
        "group_bedroom_theo_top": {"state": False},
        "bedroom_bed_led": {"state": True, "brightness": 3},
        "bedroom_wardrobe": {"state": "{{ states('binary_sensor.bedroom_wardrobe_door') == 'on' }}", "brightness": 3},
        "bedroom_table": {"state": False}
      },
      "OFF": {
        "group_bedroom_adult_top": {"state": False},
        "group_bedroom_theo_top": {"state": False},
        "bedroom_bed_led": {"state": False},
        "bedroom_wardrobe": {"state": False, "brightness": 3},
        "bedroom_table": {"state": False}
      }
    }
    self.room_init()


  def on_day(self, scene, mode, new=None, old=None):
    if mode == "new_scene":
      if old == "night":
        self.set_preset("BRIGHT")
      else:
        self.set_preset_if_on("BRIGHT")
    elif (
      mode in ["motion_sensor", "floor_motion_sensor", "door_sensor", "bed_sensor", "chair_sensor"]
      and new == "on"
      and self.auto_lights
    ):
      self.set_preset_or_restore("BRIGHT")
    elif mode == "table_motion_sensor" and new == "on" and not self.cover_active and self.auto_lights:
      self.set_preset_or_restore("BRIGHT")
    elif mode == "switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT", new, set_cooldown=True)
    elif mode == "virtual_switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT", new)
    elif mode == "theo_switch" and new in ["toggle", "on", "off"]:
      self.set_sleeping_scene("night")
    elif mode in ["switch", "theo_switch", "virtual_switch"] and "brightness" in new:
      self.toggle_brightness(new)
    else:
      return False


  def on_night(self, scene, mode, new=None, old=None):
    if mode == "new_scene":
      self.set_preset_if_on("DARK", min_delay=True)
    elif (
      mode == "floor_motion_sensor"
      and new == "on"
      and self.entity_is_off("input_boolean.alarm_ringing")
      and self.auto_lights
    ):
      self.set_preset("DARK", min_delay=True)
    elif mode in ["switch", "theo_switch"] and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT", new, set_day=True, set_cooldown=True)
    elif mode == "virtual_switch" and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT", new, set_day=True)
    elif mode in ["switch", "theo_switch", "virtual_switch"] and "brightness" in new:
      self.toggle_brightness(new, set_day=True)
    else:
      return False


  def on_dumb(self, scene, mode, new=None, old=None):
    if mode in ["switch", "theo_switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.toggle_preset("BRIGHT", new)
    elif mode in ["switch", "theo_switch", "virtual_switch"] and "brightness" in new:
      self.toggle_brightness(new)
    else:
      return False


  def on_away(self, scene, mode, new=None, old=None):
    if mode == "virtual_switch":
      self.toggle_on_away()
    else:
      return False


  @property
  def reason_to_keep_light(self):
    if self.sleeping_scene == "dumb":
      return "dumb_scene"
    if self.entity_is_on("input_boolean.alarm_ringing"):
      return "alarm_ringing"
    if self.person_inside and self.sleeping_scene != "night":
      return "person_inside"
    if not self.auto_lights:
      return "auto_lights_off"
    if (
      self.sleeping_scene == "night"
      and self.entity_is_on("binary_sensor.bedroom_wardrobe_door")
    ):
      return "wardrobe_open"
    if (
      self.entity_is_on("binary_sensor.bedroom_bed_occupied")
      and self.sleeping_scene != "night"
    ):
      return "bed_occupied"
    if self.entity_is_on("binary_sensor.bedroom_chair_occupancy"):
      return "chair_occupied"
    return None
