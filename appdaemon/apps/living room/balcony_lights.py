from room_lights import RoomLights


class BalconyLights(RoomLights):

  def initialize(self):
    self.zone = "living"
    self.room = "balcony"
    self.color_mode = "cct"
    self.delay = 14400
    self.max_delay = 14400
    self.min_delay = 14400
    self.sensors = [
      ("binary_sensor.living_room_balcony_door", "door_sensor"),
      ("binary_sensor.balcony_dark", "illuminance_sensor")
    ]
    self.switches = []
    self.groups = {}
    self.lights = {
      "balcony_window": ["color", "brightness", "transition"],
      "balcony_led": []
    }
    self.presets = {
      "BRIGHT": {
        "balcony_window": {"state": True, "brightness": 254},
        "balcony_led": {"state": True}
      },
      "DARK": {
        "balcony_window": {"state": True, "brightness": 3},
        "balcony_led": {"state": True}
      },
      "OFF": {
        "balcony_window": {"state": False},
        "balcony_led": {"state": False}
      }
    }
    self.room_init()


  def on_day(self, scene, mode, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.set_preset_if_on("BRIGHT")
    elif mode in ["door_sensor", "illuminance_sensor"] and new == "on" and self.should_turn_on:
      self.set_preset("BRIGHT")
    elif mode in ["door_sensor", "illuminance_sensor"] and new == "off" and self.auto_lights:
      self.set_preset("OFF")
    elif mode == "virtual_switch":
      self.toggle_preset("BRIGHT", new)
    else:
      return False


  def on_night(self, scene, mode, new=None, old=None, entity=None):
    if mode == "new_scene":
        self.set_preset("OFF")
    elif mode in ["door_sensor", "illuminance_sensor"] and new == "on" and self.should_turn_on:
      self.set_preset("DARK")
    elif mode in ["door_sensor", "illuminance_sensor"] and new == "off" and self.auto_lights:
      self.set_preset("OFF")
    elif mode == "virtual_switch":
      self.toggle_preset("DARK", new)
    else:
      return False


  def on_dumb(self, scene, mode, new=None, old=None, entity=None):
    if mode == "virtual_switch":
      self.toggle_preset("DARK", new)
    else:
      return False


  def on_party(self, scene, mode, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.set_preset_if_on("DARK")
    elif mode in ["door_sensor", "illuminance_sensor"] and new == "on" and self.should_turn_on:
      self.set_preset("DARK")
    elif mode in ["door_sensor", "illuminance_sensor"] and new == "off" and self.auto_lights:
      self.set_preset("OFF")
    elif mode == "virtual_switch":
      self.toggle_preset("DARK", new)
    else:
      return False


  def on_light_cinema(self, scene, mode, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.set_preset_if_on("BRIGHT")
    elif mode in ["door_sensor", "illuminance_sensor"] and new == "on" and self.should_turn_on:
      self.set_preset("BRIGHT")
    elif mode in ["door_sensor", "illuminance_sensor"] and new == "off" and self.auto_lights:
      self.set_preset("OFF")
    elif mode == "virtual_switch":
      self.toggle_preset("BRIGHT", new)
    else:
      return False


  def on_dark_cinema(self, scene, mode, new=None, old=None, entity=None):
    if mode == "new_scene":
      self.set_preset_if_on("DARK")
    elif mode in ["door_sensor", "illuminance_sensor"] and new == "on" and self.should_turn_on:
      self.set_preset("DARK")
    elif mode in ["door_sensor", "illuminance_sensor"] and new == "off" and self.auto_lights:
      self.set_preset("OFF")
    elif mode == "virtual_switch":
      self.toggle_preset("DARK", new)
    else:
      return False


  def on_away(self, scene, mode, new=None, old=None, entity=None):
    if mode == "virtual_switch":
      self.toggle_on_away()
    else:
      return False


  @property
  def reason_to_keep_light(self):
    return None


  @property
  def balcony_dark(self):
    return self.entity_is_on("binary_sensor.balcony_dark")


  @property
  def balcony_door_open(self):
    return self.entity_is_on("binary_sensor.living_room_balcony_door")


  @property
  def should_turn_on(self):
    return self.auto_lights and self.balcony_dark and self.balcony_door_open
