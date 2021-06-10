from room_lights import RoomLights


class BedroomLights(RoomLights):

  def initialize(self):
    self.zone = "sleeping"
    self.room = "bedroom"
    self.delay = 300
    self.max_delay = 720
    self.min_delay = 30
    self.sensors = [
      ("binary_sensor.bedroom_bed_motion", "motion_sensor"),
      ("binary_sensor.bedroom_table_motion", "table_motion_sensor"),
      ("binary_sensor.bedroom_floor_motion", "floor_motion_sensor"),
      ("binary_sensor.bedroom_door", "door_sensor"),
      ("binary_sensor.bedroom_chair_occupancy", "chair_sensor"),
      ("binary_sensor.bedroom_bed_occupancy_any", "bed_sensor")
    ]
    self.switches = [
      ("sensor.bedroom_theo_switch", "theo_switch"),
      ("sensor.bedroom_switch", "switch")
    ]
    self.turn_off_lights = [
      "group_bedroom_bri",
      "bedroom_bed_led_rgb",
      "bedroom_table"
    ]
    self.ignore_fade_lights = ["bedroom_table"]
    self.lights = {
      "group_bedroom_color": [
        "group_bedroom_adult_top",
        "group_bedroom_theo_top",
        "bedroom_bed_led_rgb"
      ],
      "bedroom_wardrobe": [],
      "bedroom_table": []
    }
    self.presets = {
      "BRIGHT": {
        "group_bedroom_color": {"state": "on", "attributes": {"brightness": 254}},
        "bedroom_wardrobe": {"state": "on", "attributes": {"brightness": 254}},
        "bedroom_table": {"state": "on"}
      },
      "DARK": {
        "bedroom_bed_led_rgb": {"state": "on", "attributes": {"brightness": 3}},
        "group_bedroom_top": {"state": "off"},
        "bedroom_wardrobe": {
          "state": "{{ states('binary_sensor.bedroom_wardrobe_door') }}",
          "attributes": {"brightness": 3}
        },
        "bedroom_table": {"state": "off"}
      },
      "OFF": {
        "group_bedroom_color": {"state": "off"},
        "bedroom_wardrobe": {
          "state": "{{ states('binary_sensor.bedroom_wardrobe_door') }}",
          "attributes": {"brightness": 3}
        },
        "bedroom_table": {"state": "off"}
      }
    }
    self.room_init()


  def on_day(self, scene, mode, state, new=None, old=None, entity=None):
    self.log(f"mode: {mode}, new: {new}")
    if mode == "new_scene":
      if old == "night":
        self.turn_preset("BRIGHT", mode, state)
      else:
        self.turn_preset_if_on("BRIGHT", mode, state)
    elif (
      mode in ["motion_sensor", "floor_motion_sensor", "door_sensor", "bed_sensor", "chair_sensor"]
      and new == "on"
      and self.is_auto_lights()
    ):
      self.turn_preset_or_restore("BRIGHT", mode, state)
    elif mode == "table_motion_sensor" and new == "on" and not self.is_cover_active() and self.is_auto_lights():
      self.turn_preset_or_restore("BRIGHT", mode, state)
    elif mode in ["switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.light_toggle("BRIGHT", "toggle", mode, state)
    elif mode == "theo_switch" and new in ["toggle", "on", "off"]:
      self.turn_on_scene("night")
    elif mode in ["switch", "theo_switch", "virtual_switch"] and "brightness" in new:
      self.toggle_brightness(new, state)
    else:
      return False


  def on_night(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.turn_preset_if_on("OFF", mode, state)
    elif (
      mode == "floor_motion_sensor"
      and new == "on"
      and self.get_state("input_boolean.alarm_ringing") != "on"
      and self.is_auto_lights()
    ):
      self.turn_preset("DARK", mode, state, min_delay=True)
    elif mode in ["switch", "theo_switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.night_scene_light_toggle("BRIGHT", new, mode, state)
    elif mode in ["switch", "theo_switch", "virtual_switch"] and "brightness" in new:
      self.overwrite_scene(new, "day", "BRIGHT", state)
    else:
      return False


  def on_dumb(self, scene, mode, state, new=None, old=None, entity=None):
    if mode in ["switch", "theo_switch", "virtual_switch"] and new in ["toggle", "on", "off"]:
      self.light_toggle("BRIGHT", new, mode, state)
    elif mode in ["switch", "theo_switch", "virtual_switch"] and "brightness" in new:
      self.toggle_brightness(new, state)
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
    if self.get_state("input_boolean.alarm_ringing") == "on":
      return "alarm_ringing"
    if self.is_person_inside() and self.get_state("input_select.sleeping_scene") != "night":
      return "person_inside"
    if not self.is_auto_lights():
      return "auto_lights_off"
    if (
      self.get_state("input_select.sleeping_scene") == "night"
      and self.get_state("binary_sensor.bedroom_wardrobe_door") == "on"
    ):
      return "wardrobe_open"
    if (
      self.get_state("binary_sensor.binary_sensor.bedroom_bed_occupied") == "on"
      and self.get_state("input_select.sleeping_scene") != "night"
    ):
      return "bed_occupied"
    if self.get_state("binary_sensor.bedroom_chair_occupancy") == "on":
      return "chair_occupied"
    return None
