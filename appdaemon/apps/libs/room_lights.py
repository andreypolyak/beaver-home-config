from base import Base
import random

FADE_DURATION = 60
COOLDOWN_DELAY = 60


# CHANGE: remove state from all signatures
# CHANGE: create "OFF" preset
# CHANGE: turn_off_all to set_preset("OFF")
# CHANGE: light_toggle to toggle_preset
# CHANGE: overwrite_scene to toggle_brightness(new, set_day=True)
# CHANGE: night_scene_light_toggle to toggle_preset(set_day=True)
# CHANGE: use set_cooldown in set_preset for switches and remove mode
# CHANGE: remove is_door_open
# CHANGE: differentiate switch and virtual_switch

# TODO: logging

class RoomLights(Base):

  def room_init(self):
    super().initialize()
    self.allow_button_hold = True
    default = self.__build_initial_state()
    self.init_storage(f"{self.room}_lights", "state", default)
    self.__sync_state()
    self.handle = None
    self.listen_state(self.__on_scene, f"input_select.{self.zone}_scene")
    for sensor in self.sensors:
      self.listen_state(self.__on_sensor, sensor[0], mode=sensor[1])
    for switch in self.switches:
      self.listen_state(self.__on_switch, switch[0], mode=switch[1])
    self.listen_event(self.__on_light_timer_finish, "timer.finished", entity_id=f"timer.light_{self.room}")
    self.listen_event(self.__on_faded_timer_finish, "timer.finished", entity_id=f"timer.light_faded_{self.room}")
    self.listen_event(self.__on_cooldown_timer_finish, "timer.finished", entity_id=f"timer.light_cooldown_{self.room}")
    for operation in ["on", "off", "toggle"]:
      custom_event_data = f"{self.room}_virtual_switch_room_{operation}"
      self.listen_event(self.__on_virtual_switch, "custom_event", custom_event_data=custom_event_data)
      for light_name in self.lights.keys():
        custom_event_data = f"{light_name}_virtual_switch_individual_{operation}"
        self.listen_event(self.__on_individual_virtual_switch, "custom_event", custom_event_data=custom_event_data)
    self.listen_event(self.__on_set_manual_color, "custom_event", custom_event_data=f"{self.room}_set_manual_color")
    self.listen_event(self.__on_set_auto_color, "custom_event", custom_event_data=f"{self.room}_set_auto_color")
    self.listen_event(self.__on_set_brightness, "custom_event", custom_event_data=f"{self.room}_set_brightness")
    custom_event_data = f"{self.room}_toggle_max_brightness"
    self.listen_event(self.__on_toggle_max_brightness, "custom_event", custom_event_data=custom_event_data)
    self.listen_state(self.__on_circadian_change, "input_number.circadian_saturation")
    self.listen_state(self.__on_set_auto_lights, f"input_boolean.auto_lights_{self.room}")


# Public room light control


  def set_preset(self, preset_name, min_delay=False, save_preset=True, set_cooldown=False):
    self.log(f"Set {preset_name} preset with following parameters: min_delay={min_delay}, "
             f"save_preset={save_preset}, set_cooldown={set_cooldown}")
    if save_preset:
      self.write_storage("state", preset_name, attribute="preset_name")
    light_set = self.__build_light_set_from_preset(preset_name)
    self.__set_light_set(light_set)
    if self.__is_light_off() and set_cooldown:
      self.__set_cooldown_timer()
    else:
      self.__cancel_cooldown_timer()


  def set_preset_if_on(self, preset_name, min_delay=False):
    self.log(f"Set {preset_name} preset if lights on with following parameters: min_delay={min_delay}")
    are_all_lights_off = self.__is_light_off()
    if not are_all_lights_off:
      self.set_preset(preset_name, min_delay=min_delay)


  def set_preset_or_restore(self, preset_name, min_delay=False):
    self.log(f"Set {preset_name} preset or restore lights with following parameters: min_delay={min_delay}")
    is_faded = self.read_storage("state", attribute="faded")
    are_all_lights_off = self.__is_light_off()
    is_cooldown = self.read_storage("state", attribute="cooldown")
    if is_faded:
      self.__unfade()
    elif not are_all_lights_off:
      # Or set_preset instead of set light timer?
      self.__set_light_timer()
    elif not is_cooldown:
      self.set_preset(preset_name, min_delay=min_delay)


  def toggle_preset(self, preset_name, command, min_delay=False, set_day=False, set_cooldown=False):
    self.log(f"Toggle {preset_name} preset with following parameters: command={command}, min_delay={min_delay}, "
             f"set_day={set_day}, set_cooldown={set_cooldown}")
    are_all_lights_off = self.__is_light_off()
    if command == "off" or (not are_all_lights_off and command == "toggle"):
      self.set_preset("OFF", save_preset=False, set_cooldown=set_cooldown)
      return
    self.set_preset(preset_name, min_delay=min_delay)
    if set_day:
      self.set_scene(self.zone, "day")


  def toggle_brightness(self, command, set_day=False):
    self.log(f"Toggle brightness with following parameters: command={command}, set_day={set_day}")
    if not self.__handle_button_hold(command):
      return
    if set_day:
      self.set_scene(self.zone, "day")
      self.set_preset("BRIGHT")
    elif command == "brightness_up":
      self.__toggle_max_brightness()
    elif command == "brightness_down":
      self.__toggle_min_brightness()
    self.handle = self.run_in(self.__allow_button_hold, 3)


# Control light set


  def __unfade(self):
    light_set = self.read_storage("state", attribute="lights")
    lights = self.__build_groups_from_light_set(light_set)
    for light_name, light in lights.items():
      self.__set_light(light_name, light)
    self.write_storage("state", True, attribute="max_delay")
    self.__set_light_timer()


  def __fade(self):
    light_set = {}
    fade_any = False
    lights = self.read_storage("state", attribute="lights")
    has_full_brightness = False
    for light_name in lights.keys():
      if (
        self.__is_feature_supported(light_name, "brightness")
        and lights[light_name]["state"]
        and "brightness" in lights[light_name]
        and lights[light_name]["brightness"] > 3
      ):
        has_full_brightness = True
        break
    for light_name in lights.keys():
      if not lights[light_name]["state"]:
        light_set[light_name] = {"state": False}
        continue
      if hasattr(self, "ignore_fade_lights") and light_name in self.ignore_fade_lights:
        continue
      if not self.__is_feature_supported(light_name, "brightness"):
        light_set[light_name] = {"state": False}
        continue
      if lights[light_name]["brightness"] == 3 and not has_full_brightness:
        light_set[light_name] = {"state": False}
        continue
      light_set[light_name] = {"state": True, "brightness": 2}
      fade_any = True
    if fade_any:
      self.log("Fading lights")
      groups = self.__build_groups_from_light_set(light_set)
      for light_name, light in groups.items():
        self.__set_light(light_name, light, fade=True)
      self.__set_faded_timer()
      return
    self.log("Turning lights off because they can't be faded")
    self.set_preset("OFF", save_preset=False)


  def __set_features(self, color=None, brightness=None):
    if color is not None:
      self.write_storage("state", color, attribute="color")
    light_set = self.read_storage("state", attribute="lights")
    are_all_lights_off = self.__is_light_off()
    is_faded = self.read_storage("state", attribute="faded")
    for light_name, light in light_set.items():
      if are_all_lights_off or light["state"] or is_faded:
        light_set[light_name]["state"] = True
      is_brightness_supported = self.__is_feature_supported(light_name, "brightness")
      if brightness is not None and is_brightness_supported and light_set[light_name]["state"]:
        light_set[light_name]["brightness"] = brightness
    self.__set_light_set(light_set)


  def __set_light_set(self, light_set, circadian=False):
    self.log(f"Setting new light state: {light_set} with parameters: circadian={circadian}")
    self.write_storage("state", light_set, attribute="lights")
    with_color = False
    for light in light_set.values():
      if light["state"]:
        with_color = True
        break
    groups = self.__build_groups_from_light_set(light_set, with_color=with_color)
    for light_name, light in groups.items():
      self.__set_light(light_name, light, circadian=circadian)
    if circadian:
      return
    are_all_lights_off = self.__is_light_off()
    if are_all_lights_off:
      self.__set_default_params()
      self.__cancel_light_timer()
    else:
      self.__set_light_timer()


  def __individual_virtual_switch(self, light_name, command):
    # TODO: optimize and do in one step
    is_faded = self.read_storage("state", attribute="faded")
    if is_faded:
      self.__unfade()
    light_set = self.read_storage("state", attribute="lights")
    light = light_set[light_name]
    if command == "on":
      light["state"] = True
    elif command == "off":
      light["state"] = False
    else:
      light["state"] = not light["state"]
    if light["state"] and "brightness" in self.lights[light_name]:
      if "brightness" in light_set[light_name]:
        light["brightness"] = light_set[light_name]["brightness"]
      else:
        light["brightness"] = 3
    light_set[light_name] = light
    self.__set_light_set(light_set)


  def __toggle_max_brightness(self):
    max_brightness = 0
    for light in self.read_storage("state", attribute="lights").values():
      if "brightness" in light and light["brightness"] > max_brightness:
        max_brightness = light["brightness"]
    if self.color_mode == "rgb":
      color = [30, 33]
      is_right_color = self.read_storage("state", attribute="color") == color
    elif self.color_mode == "cct":
      color = 4700
      is_right_color = self.read_storage("state", attribute="color") == color
    else:
      color = None
      is_right_color = True
    if max_brightness == 254 and is_right_color:
      self.write_storage("state", "auto", attribute="color")
      preset_name = self.read_storage("state", attribute="preset_name")
      self.set_preset(preset_name, save_preset=False)
    else:
      self.__set_features(color=color, brightness=254)


  def __toggle_min_brightness(self):
    min_brightness = 255
    for light in self.read_storage("state", attribute="lights").values():
      if "brightness" in light and light["brightness"] < min_brightness:
        min_brightness = light["brightness"]
    if min_brightness == 3:
      preset_name = self.read_storage("state", attribute="preset_name")
      self.set_preset(preset_name, save_preset=False)
    else:
      self.__set_features(brightness=3)


# Control lights


  def __set_light(self, light_name, light, circadian=False, fade=False):
    if light["state"]:
      self.__turn_on_light(light_name, light, circadian=circadian, fade=fade)
    else:
      self.__turn_off_light(light_name, fade=fade)


  def __turn_on_light(self, light_name, light, circadian=False, fade=False):
    kwargs = {}
    if self.__is_feature_supported(light_name, "transition"):
      if circadian or fade:
        kwargs["transition"] = 2
      else:
        kwargs["transition"] = self.get_float_state("input_number.transition")
    if "brightness" in light:
      kwargs["brightness"] = light["brightness"]
    if self.__is_feature_supported(light_name, "color"):
      color = self.__get_color(self.read_storage("state", attribute="color"))
      kwargs[color["mode"]] = color["value"]
    self.log(f"Turn on {light_name} with args: {kwargs}")
    self.turn_on_entity(f"light.{light_name}", **kwargs)


  def __turn_off_light(self, light_name, fade=False):
    kwargs = {}
    if self.__is_feature_supported(light_name, "transition"):
      if fade:
        kwargs["transition"] = 2
      else:
        kwargs["transition"] = self.get_float_state("input_number.transition")
    self.log(f"Turn off {light_name} with args: {kwargs}")
    self.turn_off_entity(f"light.{light_name}", **kwargs)


# Control timers


  def __set_light_timer(self):
    if self.is_entity_on(f"input_boolean.{self.zone}_zone_min_delay"):
      delay = self.min_delay
    elif self.read_storage("state", attribute="max_delay"):
      delay = self.max_delay
    else:
      delay = self.delay
    delay += random.randrange(60)
    self.timer_start(f"light_{self.room}", delay)
    self.__cancel_faded_timer()
    self.__cancel_cooldown_timer()


  def __cancel_light_timer(self):
    self.timer_cancel(f"light_{self.room}")
    self.__cancel_faded_timer()


  def __set_faded_timer(self):
    self.timer_start(f"light_faded_{self.room}", FADE_DURATION)
    self.write_storage("state", True, attribute="faded")


  def __cancel_faded_timer(self):
    self.timer_cancel(f"light_faded_{self.room}")
    self.write_storage("state", False, attribute="faded")


  def __set_cooldown_timer(self):
    self.timer_start(f"light_cooldown_{self.room}", COOLDOWN_DELAY)
    self.write_storage("state", True, attribute="cooldown")


  def __cancel_cooldown_timer(self):
    self.timer_cancel(f"light_cooldown_{self.room}")
    self.write_storage("state", False, attribute="cooldown")


# Timer callbacks


  def __on_light_timer_finish(self, event_name, data, kwargs):
    reason = self.should_turn_off_by_timer()
    if reason:
      self.__set_light_timer()
      self.log(f"Lights were not faded because of: {reason}")
      return
    self.__fade()


  def __on_faded_timer_finish(self, event_name, data, kwargs):
    self.write_storage("state", False, attribute="max_delay")
    self.write_storage("state", False, attribute="faded")
    reason = self.should_turn_off_by_timer()
    if reason:
      self.log(f"Lights were not turned off because of: {reason}")
      self.__unfade()
      return
    self.set_preset("OFF", save_preset=False)


  def __on_cooldown_timer_finish(self, event_name, data, kwargs):
    self.write_storage("state", False, attribute="cooldown")


# Callbacks


  def __on_scene(self, entity, attribute, old, new, kwargs):
    self.__set_default_params()
    func_name = f"on_{old}"
    func = getattr(self, func_name, None)
    entity = entity.replace("input_select.", "")
    mode = "old_scene"
    if callable(func):
      res = func(old, mode, new=new, old=old, entity=entity)
      if res is not False:
        self.write_to_log(old, mode, entity, new, old)
    func_name = f"on_{new}"
    func = getattr(self, func_name, None)
    mode = "new_scene"
    if callable(func):
      res = func(new, mode, new=new, old=old, entity=entity)
      if res is not False:
        self.write_to_log(new, mode, entity, new, old)


  def __on_sensor(self, entity, attribute, old, new, kwargs):
    if self.is_bad(new):
      return
    scene = self.get_scene(self.zone)
    func_name = f"on_{scene}"
    func = getattr(self, func_name, None)
    entity = entity.replace("binary_sensor.", "").replace("sensor.", "")
    mode = kwargs["mode"]
    if callable(func):
      res = func(scene, mode, new=new, old=old, entity=entity)
      if res is not False:
        self.write_to_log(scene, mode, entity, new, old)


  def __on_switch(self, entity, attribute, old, new, kwargs):
    scene = self.get_scene(self.zone)
    func_name = f"on_{scene}"
    func = getattr(self, func_name, None)
    if new in ["on", "off"]:
      new = "toggle"
    elif new == "rotate_left":
      new = "brightness_up"
    elif new == "rotate_right":
      new = "brightness_down"
    elif new == "rotate_stop":
      new = "brightness_stop"
    entity = entity.replace("sensor.", "")
    mode = kwargs["mode"]
    if callable(func):
      res = func(scene, mode, new=new, old=old, entity=entity)
      if res is not False:
        self.write_to_log(scene, mode, entity, new, old)


  def __on_virtual_switch(self, event_name, data, kwargs):
    scene = self.get_scene(self.zone)
    event_data = data["custom_event_data"]
    func_name = f"on_{scene}"
    func = getattr(self, func_name, None)
    operation = "toggle"
    if "_virtual_switch_room_on" in event_data:
      operation = "on"
    elif "_virtual_switch_room_off" in event_data:
      operation = "off"
    entity = f"ha_template_{self.room}"
    mode = "virtual_switch"
    if callable(func):
      res = func(scene, mode, new=operation, entity=entity)
      if res is not False:
        self.write_to_log(scene, mode, entity, operation, None)


  def __on_individual_virtual_switch(self, event_name, data, kwargs):
    event_data = data["custom_event_data"]
    command = "toggle"
    if "_virtual_switch_individual_on" in event_data:
      command = "on"
    elif "_virtual_switch_individual_off" in event_data:
      command = "off"
    light_name = event_data.replace(f"_virtual_switch_individual_{command}", "")
    self.__individual_virtual_switch(light_name, command)


  def __on_set_manual_color(self, event_name, data, kwargs):
    self.turn_off_entity(f"input_boolean.auto_colors_{self.room}")
    color = data["custom_event_data2"]
    self.__set_features(color=color)


  def __on_set_auto_color(self, event_name, data, kwargs):
    self.turn_on_entity(f"input_boolean.auto_colors_{self.room}")
    self.__set_features(color="auto")


  def __on_set_brightness(self, event_name, data, kwargs):
    brightness = int(data["custom_event_data2"])
    self.__set_features(brightness=brightness)


  def __on_set_auto_lights(self, entity, attribute, old, new, kwargs):
    if new == "on":
      self.write_storage("state", True, attribute="auto_lights")
    else:
      self.write_storage("state", False, attribute="auto_lights")


  def __on_toggle_max_brightness(self, event_name, data, kwargs):
    self.__toggle_max_brightness()


  def __on_circadian_change(self, entity, attribute, old, new, kwargs):
    if (
      self.is_entity_off("input_boolean.circadian_update")
      or self.read_storage("state", attribute="color") != "auto"
      or self.get_scene(self.zone) not in ["day", "light_cinema"]
    ):
      return
    light_set = self.read_storage("state", attribute="lights")
    self.__set_light_set(light_set, circadian=True)


# Public helpers


  def is_cover_active(self):
    entity = f"input_boolean.{self.room}_cover_active"
    if self.entity_exists(entity) and self.is_entity_on(entity):
      return True
    return False


  def write_to_log(self, scene, mode, entity, new, old):
    # TODO: redo in future?
    log_str = "Room trigger: "
    if scene:
      log_str += f"scene={scene}"
    if mode:
      log_str += f", mode={mode}"
    if entity:
      log_str += f", entity={entity}"
    if new:
      log_str += f", new={new}"
    if old:
      log_str += f", old={old}"
    self.log(log_str)


  def is_person_inside(self):
    is_person_inside = False
    entity = f"input_boolean.person_inside_{self.room}"
    if self.entity_exists(entity) and self.is_entity_on(entity):
      is_person_inside = True
    return is_person_inside


  def is_auto_lights(self):
    return self.read_storage("state", attribute="auto_lights")


# Private helpers


  def __build_light_set_from_preset(self, preset_name):
    light_set = {}
    for light_name, light in self.presets[preset_name].items():
      light_set[light_name] = light.copy()
      if isinstance(light["state"], str):
        light_set[light_name]["state"] = self.render_template(light["state"])
    return light_set


  def __build_groups_from_light_set(self, light_set, with_color=False):
    feature_groups = {}
    for light_name, light in light_set.items():
      key = self.__build_light_features_key(light_name, light, with_color=with_color)
      if key not in feature_groups:
        feature_groups[key] = []
      feature_groups[key].append(light_name)
    groups = {}
    for feature_group in feature_groups.values():
      found_group = False
      for group_name, group in self.groups.items():
        if set(group) == set(feature_group):
          groups[group_name] = light_set[feature_group[0]]
          found_group = True
          continue
      if not found_group:
        for light_name in feature_group:
          groups[light_name] = light_set[light_name]
    return groups


  def __build_light_features_key(self, light_name, light, with_color=False):
    state = light["state"]
    brightness = 0
    if "brightness" in light:
      brightness = light["brightness"]
    key = str(state)
    if state:
      if "brightness" in self.lights[light_name]:
        key += f"brightness{brightness}"
      if with_color and "color" in self.lights[light_name]:
        key += "color"
    else:
      if "transition" in self.lights[light_name]:
        key += "transition"
    return key


  def __handle_button_hold(self, action):
    self.cancel_handle(self.handle)
    if action == "brightness_stop":
      self.allow_button_hold = True
      return False
    if not self.allow_button_hold:
      return False
    self.allow_button_hold = False
    return True


  def __allow_button_hold(self, kwargs):
    self.allow_button_hold = True


  def __is_feature_supported(self, light_name, feature):
    if light_name in self.lights and feature in self.lights[light_name]:
      return True
    if light_name in self.groups:
      for child_light_name in self.groups[light_name]:
        if feature not in self.lights[child_light_name]:
          return False
      return True
    return False


  def __is_light_off(self):
    for light in self.read_storage("state", attribute="lights").values():
      if light["state"]:
        return False
    return True


  def __get_color(self, input_color):
    color = {
      "mode": "",
      "value": ""
    }
    if isinstance(input_color, str) and input_color == "auto" and self.color_mode == "rgb":
      saturation = self.get_int_state("input_number.circadian_saturation")
      color["mode"] = "hs_color"
      color["value"] = [30, saturation]
    elif isinstance(input_color, str) and input_color == "auto" and self.color_mode == "cct":
      saturation = self.get_int_state("input_number.circadian_saturation")
      kelvin = 6500 - saturation * ((6500 - 2000) / 100)
      color["mode"] = "kelvin"
      color["value"] = kelvin
    elif isinstance(input_color, list) and len(input_color) == 3:
      color["mode"] = "rgb_color"
      color["value"] = input_color
    elif isinstance(input_color, list) and len(input_color) == 2:
      color["mode"] = "hs_color"
      color["value"] = input_color
    else:
      color["mode"] = "kelvin"
      color["value"] = input_color
    return color


  def __set_default_params(self):
    self.write_storage("state", "auto", attribute="color")
    self.write_storage("state", True, attribute="auto_lights")
    self.write_storage("state", False, attribute="max_delay")


  def __build_initial_state(self):
    state = {
      "lights": {},
      "preset_name": "BRIGHT",
      "faded": self.is_timer_active(f"light_faded_{self.room}"),
      "cooldown": self.is_timer_active(f"light_cooldown_{self.room}"),
      "color": "auto",
      "auto_lights": self.is_entity_on(f"input_boolean.auto_lights_{self.room}"),
      "max_delay": False
    }
    state["lights"] = self.__build_light_set_from_preset("BRIGHT")
    return state


  def __sync_state(self):
    self.write_storage("state", self.is_timer_active(f"light_faded_{self.room}"), attribute="faded")
    self.write_storage("state", self.is_timer_active(f"light_cooldown_{self.room}"), attribute="cooldown")
    self.write_storage("state", self.is_entity_on(f"input_boolean.auto_lights_{self.room}"), attribute="auto_lights")
