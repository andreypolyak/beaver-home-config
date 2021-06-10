from room_lights import RoomLights


class BalconyLights(RoomLights):

  def initialize(self):
    self.zone = "living"
    self.room = "balcony"
    self.delay = 14400
    self.max_delay = 14400
    self.min_delay = 14400
    self.sensors = [
      ("binary_sensor.living_room_balcony_door", "door_sensor"),
      ("binary_sensor.balcony_dark", "illuminance_sensor")
    ]
    self.switches = []
    self.turn_off_lights = [
      "balcony_window",
      "balcony_led"
    ]
    self.lights = {
      "balcony_window": [],
      "balcony_led": []
    }
    self.presets = {
      "BRIGHT": {
        "balcony_window": {"state": "on", "attributes": {"brightness": 254}},
        "balcony_led": {"state": "on"}
      },
      "DARK": {
        "balcony_window": {"state": "on", "attributes": {"brightness": 3}},
        "balcony_led": {"state": "on"}
      }
    }
    self.room_init()


  def on_day(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.turn_preset_if_on("BRIGHT", mode, state)
    elif (
      mode in ["door_sensor", "illuminance_sensor"]
      and new == "on"
      and self.is_auto_lights()
      and self.is_balcony_dark()
      and self.is_door_open(state, "living_room_balcony_door")
    ):
      self.light_toggle("BRIGHT", new, mode, state)
    elif mode in ["door_sensor", "illuminance_sensor"] and new == "off" and self.is_auto_lights():
      self.light_toggle("BRIGHT", new, mode, state)
    elif mode == "virtual_switch":
      self.light_toggle("BRIGHT", new, mode, state)
    else:
      return False


  def on_night(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
        self.turn_off_all(state)
      # self.turn_preset_if_on("DARK", mode, state)
    elif (
      mode in ["door_sensor", "illuminance_sensor"]
      and new == "on"
      and self.is_auto_lights()
      and self.is_balcony_dark()
      and self.is_door_open(state, "living_room_balcony_door")
    ):
      self.light_toggle("DARK", new, mode, state)
    elif mode in ["door_sensor", "illuminance_sensor"] and new == "off" and self.is_auto_lights():
      self.light_toggle("DARK", new, mode, state)
    elif mode == "virtual_switch":
      self.light_toggle("DARK", new, mode, state)
    else:
      return False


  def on_dumb(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "virtual_switch":
      self.light_toggle("DARK", new, mode, state)
    else:
      return False


  def on_party(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.turn_preset_if_on("DARK", mode, state)
    elif (
      mode in ["door_sensor", "illuminance_sensor"]
      and new == "on"
      and self.is_auto_lights()
      and self.is_balcony_dark()
      and self.is_door_open(state, "living_room_balcony_door")
    ):
      self.light_toggle("DARK", new, mode, state)
    elif mode in ["door_sensor", "illuminance_sensor"] and new == "off" and self.is_auto_lights():
      self.light_toggle("DARK", new, mode, state)
    elif mode == "virtual_switch":
      self.light_toggle("DARK", new, mode, state)
    else:
      return False


  def on_light_cinema(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.turn_preset_if_on("BRIGHT", mode, state)
    elif (
      mode in ["door_sensor", "illuminance_sensor"]
      and new == "on"
      and self.is_auto_lights()
      and self.is_balcony_dark()
      and self.is_door_open(state, "living_room_balcony_door")
    ):
      self.light_toggle("BRIGHT", new, mode, state)
    elif mode in ["door_sensor", "illuminance_sensor"] and new == "off" and self.is_auto_lights():
      self.light_toggle("BRIGHT", new, mode, state)
    elif mode == "virtual_switch":
      self.light_toggle("BRIGHT", new, mode, state)
    else:
      return False


  def on_dark_cinema(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.turn_preset_if_on("DARK", mode, state)
    elif (
      mode in ["door_sensor", "illuminance_sensor"]
      and new == "on"
      and self.is_auto_lights()
      and self.is_balcony_dark()
      and self.is_door_open(state, "living_room_balcony_door")
    ):
      self.light_toggle("DARK", new, mode, state)
    elif mode in ["door_sensor", "illuminance_sensor"] and new == "off" and self.is_auto_lights():
      self.light_toggle("DARK", new, mode, state)
    elif mode == "virtual_switch":
      self.light_toggle("DARK", new, mode, state)
    else:
      return False


  def on_away(self, scene, mode, state, new=None, old=None, entity=None):
    if mode == "virtual_switch":
      self.turn_off_all(state)
    else:
      return False


  def should_turn_off_by_timer(self):
    return None


  def is_balcony_dark(self):
    return self.get_state("binary_sensor.balcony_dark") == "on"
