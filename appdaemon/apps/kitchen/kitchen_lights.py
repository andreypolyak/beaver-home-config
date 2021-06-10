from room_lights import RoomLights


class KitchenLights(RoomLights):

  def initialize(self):
    self.zone = "living"
    self.room = "kitchen"
    self.delay = 240
    self.max_delay = 600
    self.min_delay = 30
    self.sensors = [
      ("binary_sensor.kitchen_motion", "motion_sensor"),
      ("binary_sensor.kitchen_table_motion", "motion_sensor"),
      ("binary_sensor.living_room_back_motion", "back_motion_sensor"),
      ("binary_sensor.bedroom_door", "door_sensor"),
      ("binary_sensor.entrance_door", "door_sensor"),
      ("binary_sensor.kitchen_chair_1_occupancy", "chair_sensor"),
      ("binary_sensor.kitchen_chair_2_occupancy", "chair_sensor")
    ]
    self.switches = [
      ("sensor.kitchen_switch", "switch")
    ]
    self.turn_off_lights = [
      "group_kitchen_color",
      "kitchen_vent"
    ]
    self.lights = {
      "group_kitchen_color": [
        "group_kitchen_top",
        "kitchen_table"
      ],
      "kitchen_vent": []
    }
    self.presets = {
      "BRIGHT": {
        "group_kitchen_color": {"state": "on", "attributes": {"brightness": 254}},
        "kitchen_vent": {"state": "on"}
      },
      "BRIGHT_CINEMA": {
        "kitchen_table": {"state": "off"},
        "group_kitchen_top": {"state": "on", "attributes": {"brightness": 254}},
        "kitchen_vent": {"state": "on"}
      },
      "DARK": {
        "kitchen_table": {"state": "off"},
        "group_kitchen_top": {"state": "on", "attributes": {"brightness": 3}},
        "kitchen_vent": {"state": "on"}
      },
      "NIGHT": {
        "kitchen_table": {"state": "on", "attributes": {"brightness": 3}},
        "group_kitchen_top": {"state": "off"},
        "kitchen_vent": {"state": "off"}
      }
    }
    self.room_init()


  def on_day(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.turn_preset_if_on("BRIGHT", mode, state)
    elif mode in ["motion_sensor", "door_sensor", "chair_sensor"] and new == "on" and self.is_auto_lights():
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
        self.turn_off_all(state)
      # self.turn_preset_if_on("NIGHT", mode, state, min_delay=True)
    elif mode in ["motion_sensor", "door_sensor", "chair_sensor"] and new == "on" and self.is_auto_lights():
      if self.get_state("binary_sensor.night_scene_in_living_zone_turned_on_long_enough") == "on":
        self.turn_preset("BRIGHT", mode, state)
        self.turn_on_scene("day")
      else:
        self.turn_preset_or_restore("NIGHT", mode, state, min_delay=True)
    elif mode == "back_motion_sensor" and new == "on" and not self.is_cover_active() and self.is_auto_lights():
      if self.get_state("binary_sensor.night_scene_in_living_zone_turned_on_long_enough") == "on":
        self.turn_preset("BRIGHT", mode, state)
        self.turn_on_scene("day")
      else:
        self.turn_preset_or_restore("NIGHT", mode, state, min_delay=True)
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
      self.turn_preset_if_on("DARK", mode, state, min_delay=True)
    elif mode in ["motion_sensor", "door_sensor", "chair_sensor"] and new == "on" and self.is_auto_lights():
      self.turn_preset_or_restore("DARK", mode, state, min_delay=True)
    elif mode == "back_motion_sensor" and new == "on" and not self.is_cover_active() and self.is_auto_lights():
      self.turn_preset_or_restore("DARK", mode, state, min_delay=True)
    elif mode in ["switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.light_toggle("DARK", new, mode, state, min_delay=True)
    elif mode == "switch" and "brightness" in new:
      self.overwrite_scene(new, "day", "BRIGHT", state)
    else:
      return False


  def on_light_cinema(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.turn_preset_if_on("BRIGHT_CINEMA", mode, state)
    elif mode in ["motion_sensor", "door_sensor", "chair_sensor"] and new == "on" and self.is_auto_lights():
      self.turn_preset_or_restore("BRIGHT_CINEMA", mode, state)
    elif mode == "back_motion_sensor" and new == "on" and not self.is_cover_active() and self.is_auto_lights():
      self.turn_preset_or_restore("BRIGHT_CINEMA", mode, state)
    elif mode in ["switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.light_toggle("BRIGHT_CINEMA", new, mode, state)
    elif mode == "switch" and "brightness" in new:
      self.toggle_brightness(new, state)
    else:
      return False


  def on_dark_cinema(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.turn_preset_if_on("DARK", mode, state, min_delay=True)
    elif mode in ["motion_sensor", "door_sensor", "chair_sensor"] and new == "on" and self.is_auto_lights():
      self.turn_preset_or_restore("DARK", mode, state, min_delay=True)
    elif mode == "back_motion_sensor" and new == "on" and not self.is_cover_active() and self.is_auto_lights():
      self.turn_preset_or_restore("DARK", mode, state, min_delay=True)
    elif mode in ["switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.light_toggle("DARK", new, mode, state, min_delay=True)
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
    if self.get_state(f"input_select.{self.zone}_scene") == "dumb":
      return "dumb_scene"
    if not self.is_auto_lights():
      return "auto_lights_off"
    if (
      self.get_state("binary_sensor.kitchen_chair_1_occupancy") == "on"
      or self.get_state("binary_sensor.kitchen_chair_2_occupancy") == "on"
    ):
      return "chair_occupied"
    return None
