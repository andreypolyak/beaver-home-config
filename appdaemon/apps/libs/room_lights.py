from base import Base
import random

FADE_DURATION = 60
COOLDOWN_DELAY = 60


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
      self.listen_event(self.__on_virtual_switch, f"{self.room}_virtual_switch_room_{operation}")
      for light_name in self.lights.keys():
        self.listen_event(self.__on_individual_virtual_switch, f"{light_name}_virtual_switch_individual_{operation}")
    self.listen_event(self.__on_set_manual_color, f"{self.room}_set_manual_color")
    self.listen_event(self.__on_set_auto_color, f"{self.room}_set_auto_color")
    self.listen_event(self.__on_set_brightness, f"{self.room}_set_brightness")
    self.listen_event(self.__on_toggle_max_brightness, f"{self.room}_toggle_max_brightness")
    self.listen_state(self.__on_circadian_change, "input_number.circadian_saturation")
    self.listen_state(self.__on_set_lock_lights, f"input_boolean.lock_lights_{self.room}")

# Public room light control

  def set_preset(self, preset_name, min_delay=False, save_preset=True, set_cooldown=False):
    self.log(f"Set {preset_name} preset with following parameters: min_delay={min_delay}, "
             f"save_preset={save_preset}, set_cooldown={set_cooldown}")
    if save_preset:
      self.write_storage("state", preset_name, attribute="preset_name")
    light_set = self.__build_light_set_from_preset(preset_name)
    self.__set_light_set(light_set)
    if self.__is_light_off and set_cooldown:
      self.__set_cooldown_timer()
    else:
      self.__cancel_cooldown_timer()


  def set_preset_if_on(self, preset_name, min_delay=False):
    self.log(f"Set {preset_name} preset if lights on with following parameters: min_delay={min_delay}")
    if not self.__is_light_off:
      self.set_preset(preset_name, min_delay=min_delay)
    else:
      self.write_storage("state", preset_name, attribute="preset_name")


  def set_preset_or_restore(self, preset_name, min_delay=False):
    self.log(f"Set {preset_name} preset or restore lights with following parameters: min_delay={min_delay}")
    faded = self.read_storage("state", attribute="faded")
    cooldown_active = self.read_storage("state", attribute="cooldown")
    if faded:
      self.__unfade()
    elif not self.__is_light_off:
      # Or set_preset instead of set light timer?
      self.__set_light_timer()
    elif not cooldown_active:
      self.set_preset(preset_name, min_delay=min_delay)


  def toggle_preset(self, preset_name, command, min_delay=False, set_day=False, set_cooldown=False):
    self.log(f"Toggle {preset_name} preset with following parameters: command={command}, min_delay={min_delay}, "
             f"set_day={set_day}, set_cooldown={set_cooldown}")
    if command == "off" or (not self.__is_light_off and command == "toggle"):
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
    elif command == "brightness_move_down":
      self.__toggle_max_brightness()
    elif command == "brightness_move_up":
      self.__toggle_min_brightness()
    self.handle = self.run_in(self.__allow_button_hold, 3)


  def toggle_on_away(self):
    if self.__is_light_off:
      self.set_scene(self.zone, "day")
      self.set_preset("BRIGHT")
    else:
      self.set_preset("OFF", save_preset=False)

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
    faded = self.read_storage("state", attribute="faded")
    for light_name, light in light_set.items():
      if self.__is_light_off or light["state"] or faded:
        light_set[light_name]["state"] = True
      brightness_supported = self.__is_feature_supported(light_name, "brightness")
      if brightness is not None and brightness_supported and light_set[light_name]["state"]:
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
    if self.__is_light_off:
      self.__set_default_params()
      self.__cancel_light_timer()
    else:
      self.__set_light_timer()


  def __individual_virtual_switch(self, light_name, command):
    # TODO: optimize and do in one step
    faded = self.read_storage("state", attribute="faded")
    if faded:
      self.__unfade()
    light_set = self.read_storage("state", attribute="lights")
    light = light_set[light_name]
    if command == "on":
      light["state"] = True
    elif command == "off":
      light["state"] = False
    else:
      light["state"] = not light["state"]
    preset_name = self.read_storage("state", attribute="preset_name")
    if light["state"] and "brightness" in self.lights[light_name]:
      if "brightness" in light_set[light_name]:
        light["brightness"] = light_set[light_name]["brightness"]
      elif "brightness" in self.presets[preset_name][light_name]:
        light["brightness"] = self.presets[preset_name][light_name]["brightness"]
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
      same_color_active = self.read_storage("state", attribute="color") == color
    elif self.color_mode == "cct":
      color = 4700
      same_color_active = self.read_storage("state", attribute="color") == color
    else:
      color = None
      same_color_active = True
    if max_brightness == 254 and same_color_active:
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
    if "brightness" in light and not circadian:
      kwargs["brightness"] = light["brightness"]
    if self.__is_feature_supported(light_name, "color") and not fade:
      color = self.__get_color(self.read_storage("state", attribute="color"))
      kwargs[color["mode"]] = color["value"]
    elif circadian and not self.__is_feature_supported(light_name, "color"):
      return
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
    if self.entity_is_on(f"input_boolean.{self.zone}_zone_min_delay"):
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
    if self.timer_is_active(f"light_{self.room}"):
      self.timer_cancel(f"light_{self.room}")
    self.__cancel_faded_timer()


  def __set_faded_timer(self):
    self.timer_start(f"light_faded_{self.room}", FADE_DURATION)
    self.write_storage("state", True, attribute="faded")


  def __cancel_faded_timer(self):
    if self.timer_is_active(f"light_faded_{self.room}"):
      self.timer_cancel(f"light_faded_{self.room}")
    self.write_storage("state", False, attribute="faded")


  def __set_cooldown_timer(self):
    self.timer_start(f"light_cooldown_{self.room}", COOLDOWN_DELAY)
    self.write_storage("state", True, attribute="cooldown")


  def __cancel_cooldown_timer(self):
    if self.timer_is_active(f"light_cooldown_{self.room}"):
      self.timer_cancel(f"light_cooldown_{self.room}")
    self.write_storage("state", False, attribute="cooldown")

# Timer callbacks

  def __on_light_timer_finish(self, event_name, data, kwargs):
    reason = self.reason_to_keep_light
    if reason:
      self.__set_light_timer()
      self.log(f"Lights were not faded because of: {reason}")
      return
    self.__fade()


  def __on_faded_timer_finish(self, event_name, data, kwargs):
    self.write_storage("state", False, attribute="max_delay")
    self.write_storage("state", False, attribute="faded")
    reason = self.reason_to_keep_light
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
      res = func(old, mode, new=new, old=old)
      if res is not False:
        self.__write_to_log(old=old, mode=mode, entity=entity, new=new)
    func_name = f"on_{new}"
    func = getattr(self, func_name, None)
    mode = "new_scene"
    if callable(func):
      res = func(new, mode, new=new, old=old)
      if res is not False:
        self.__write_to_log(new=new, mode=mode, entity=entity, old=old)


  def __on_sensor(self, entity, attribute, old, new, kwargs):
    if self.is_invalid(new):
      return
    scene = self.get_scene(self.zone)
    func_name = f"on_{scene}"
    func = getattr(self, func_name, None)
    entity = entity.replace("binary_sensor.", "").replace("sensor.", "")
    mode = kwargs["mode"]
    if callable(func):
      res = func(scene, mode, new=new, old=old)
      if res is not False:
        self.__write_to_log(scene=scene, mode=mode, entity=entity, new=new, old=old)


  def __on_switch(self, entity, attribute, old, new, kwargs):
    if self.is_invalid(new):
      return
    scene = self.get_scene(self.zone)
    func_name = f"on_{scene}"
    func = getattr(self, func_name, None)
    if new in ["on", "off"]:
      new = "toggle"
    entity = entity.replace("sensor.", "")
    mode = kwargs["mode"]
    if callable(func):
      res = func(scene, mode, new=new, old=old)
      if res is not False:
        self.__write_to_log(scene=scene, mode=mode, entity=entity, new=new, old=old)


  def __on_virtual_switch(self, event_name, data, kwargs):
    scene = self.get_scene(self.zone)
    func_name = f"on_{scene}"
    func = getattr(self, func_name, None)
    operation = "toggle"
    if "_virtual_switch_room_on" in event_name:
      operation = "on"
    elif "_virtual_switch_room_off" in event_name:
      operation = "off"
    entity = f"ha_template_{self.room}"
    mode = "virtual_switch"
    if callable(func):
      res = func(scene, mode, new=operation)
      if res is not False:
        self.__write_to_log(scene=scene, mode=mode, entity=entity, operation=operation)


  def __on_individual_virtual_switch(self, event_name, data, kwargs):
    command = "toggle"
    if "_virtual_switch_individual_on" in event_name:
      command = "on"
    elif "_virtual_switch_individual_off" in event_name:
      command = "off"
    light_name = event_name.replace(f"_virtual_switch_individual_{command}", "")
    self.__individual_virtual_switch(light_name, command)


  def __on_set_manual_color(self, event_name, data, kwargs):
    self.turn_off_entity(f"input_boolean.auto_colors_{self.room}")
    color = data["color"]
    if isinstance(color, str) and "(" in color and "(" in color:
      color = color.replace("(", "").replace(")", "").replace(" ", "")
      color = color.split(",")
    self.__set_features(color=color)


  def __on_set_auto_color(self, event_name, data, kwargs):
    self.turn_on_entity(f"input_boolean.auto_colors_{self.room}")
    self.__set_features(color="auto")


  def __on_set_brightness(self, event_name, data, kwargs):
    brightness = int(data["brightness"])
    self.__set_features(brightness=brightness)


  def __on_set_lock_lights(self, entity, attribute, old, new, kwargs):
    if new == "on":
      self.write_storage("state", True, attribute="lock_lights")
    else:
      self.write_storage("state", False, attribute="lock_lights")


  def __on_toggle_max_brightness(self, event_name, data, kwargs):
    self.__toggle_max_brightness()


  def __on_circadian_change(self, entity, attribute, old, new, kwargs):
    if (
      self.entity_is_off("input_boolean.circadian_update")
      or self.read_storage("state", attribute="color") != "auto"
      or self.get_scene(self.zone) not in ["day", "light_cinema"]
    ):
      return
    light_set = self.read_storage("state", attribute="lights")
    self.__set_light_set(light_set, circadian=True)

# Properties

  @property
  def cover_active(self):
    if not hasattr(self, "covers"):
      return False
    for room in self.covers:
      if self.entity_is_on(f"input_boolean.{room}_cover_active"):
        return True
    return False


  @property
  def person_inside(self):
    entity = f"binary_sensor.person_inside_{self.room}"
    if self.entity_exists(entity) and self.entity_is_on(entity):
      return True
    return False


  @property
  def lock_lights(self):
    return self.read_storage("state", attribute="lock_lights")

# Helpers

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


  @property
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
      kelvin = 1200 + (100 - saturation) * 50
      xy = self.__kelvin_to_xy(kelvin)
      color["mode"] = "xy_color"
      color["value"] = xy
    elif isinstance(input_color, str) and input_color == "auto" and self.color_mode == "cct":
      saturation = self.get_int_state("input_number.circadian_saturation")
      # 3575 Kelvin is cold enough color temperature, no need to have temperature from 3575 to 6500
      kelvin = 3575 - saturation * ((3575 - 2000) / 100)
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
    self.write_storage("state", False, attribute="max_delay")
    if self.entity_is_on(f"input_boolean.lock_lights_{self.room}"):
      self.turn_off_entity(f"input_boolean.lock_lights_{self.room}")


  def __build_initial_state(self):
    state = {
      "lights": {},
      "preset_name": "BRIGHT",
      "faded": self.timer_is_active(f"light_faded_{self.room}"),
      "cooldown": self.timer_is_active(f"light_cooldown_{self.room}"),
      "color": "auto",
      "lock_lights": self.entity_is_on(f"input_boolean.lock_lights_{self.room}"),
      "max_delay": False
    }
    state["lights"] = self.__build_light_set_from_preset("BRIGHT")
    return state


  def __sync_state(self):
    if self.read_storage("state", attribute="faded") and not self.timer_is_active(f"light_faded_{self.room}"):
      self.__set_faded_timer()
    elif not self.__is_light_off and not self.timer_is_active(f"light_{self.room}"):
      self.__set_light_timer()
    if self.read_storage("state", attribute="cooldown") and not self.timer_is_active(f"light_cooldown_{self.room}"):
      self.__set_cooldown_timer()
    if self.read_storage("state", attribute="lock_lights"):
      self.turn_on_entity(f"input_boolean.lock_lights_{self.room}")
    else:
      self.turn_off_entity(f"input_boolean.lock_lights_{self.room}")


  def __write_to_log(self, **kwargs):
    log_str = "Room trigger with params: "
    for arg_name, arg_value in kwargs.items():
      log_str += f"{arg_name}={arg_value}, "
    self.log(log_str[:-2])


  def __kelvin_to_xy(self, kelvin):
    # Table from https://www.waveformlighting.com/files/blackBodyLocus_10.txt
    values = {
      "1200": [0.625043976741368, 0.367454828640607],
      "1250": [0.618299624701903, 0.372495061588915],
      "1300": [0.611630593056105, 0.377232925955066],
      "1350": [0.605037289071589, 0.381664568631302],
      "1400": [0.598520140114478, 0.385788815057729],
      "1450": [0.592079736269747, 0.389606847004059],
      "1500": [0.585716902268969, 0.393121905838739],
      "1550": [0.579432718621644, 0.396339017050928],
      "1600": [0.573228507819347, 0.399264733637420],
      "1650": [0.567105798015014, 0.401906897160888],
      "1700": [0.561066273656675, 0.404274415996570],
      "1750": [0.555111720136911, 0.406377060648321],
      "1800": [0.549243967554590, 0.408225276139745],
      "1850": [0.543464837117342, 0.409830011455734],
      "1900": [0.537776092484472, 0.411202565887823],
      "1950": [0.532179397406758, 0.412354451969443],
      "2000": [0.526676280311873, 0.413297274507630],
      "2050": [0.521268105968449, 0.414042625047528],
      "2100": [0.515956053999373, 0.414601990958848],
      "2150": [0.510741103773325, 0.414986678216401],
      "2200": [0.505624025055233, 0.415207746862562],
      "2250": [0.500605373718514, 0.415275958087495],
      "2300": [0.495685491796189, 0.415201731840687],
      "2350": [0.490864511159246, 0.414995113890958],
      "2400": [0.486142360147258, 0.414665751277374],
      "2450": [0.481518772529133, 0.414222875135951],
      "2500": [0.476993298233858, 0.413675289942435],
      "2550": [0.472565315357245, 0.413031368275923],
      "2600": [0.468234043017033, 0.412299050278290],
      "2650": [0.463998554692746, 0.411485847057383],
      "2700": [0.459857791746717, 0.410598847355503],
      "2750": [0.455810576877562, 0.409644726876854],
      "2800": [0.451855627306685, 0.408629759737106],
      "2850": [0.447991567541816, 0.407559831563923],
      "2900": [0.444216941599399, 0.406440453838584],
      "2950": [0.440530224599989, 0.405276779125295],
      "3000": [0.436929833678155, 0.404073616886221],
      "3050": [0.433414138171168, 0.402835449626724],
      "3100": [0.429981469069442, 0.401566449156763],
      "3150": [0.426630127726814, 0.400270492791288],
      "3200": [0.423358393840696, 0.398951179344833],
      "3250": [0.420164532721440, 0.397611844803810],
      "3300": [0.417046801877253, 0.396255577584578],
      "3350": [0.414003456946084, 0.394885233306455],
      "3400": [0.411032757009395, 0.393503449026874],
      "3450": [0.408132969324891, 0.392112656901240],
      "3500": [0.405302373516452, 0.390715097242847],
      "3550": [0.402539265259722, 0.389312830968992],
      "3600": [0.399841959501467, 0.387907751428262],
      "3650": [0.397208793249882, 0.386501595611205],
      "3700": [0.394638127971748, 0.385095954752460],
      "3750": [0.392128351630781, 0.383692284336979],
      "3800": [0.389677880399752, 0.382291913526683],
      "3850": [0.387285160077084, 0.380896054026513],
      "3900": [0.384948667236696, 0.379505808410940],
      "3950": [0.382666910137919, 0.378122177933306],
      "4000": [0.380438429420364, 0.376746069841299],
      "4050": [0.378261798606731, 0.375378304222286],
      "4100": [0.376135624434723, 0.374019620402386],
      "4150": [0.374058547037489, 0.372670682922962],
      "4200": [0.372029239990332, 0.371332087117875],
      "4250": [0.370046410239904, 0.370004364314267],
      "4300": [0.368108797930561, 0.368687986678976],
      "4350": [0.366215176141282, 0.367383371731904],
      "4400": [0.364364350545175, 0.366090886546814],
      "4450": [0.362555159002508, 0.364810851659140],
      "4500": [0.360786471097048, 0.363543544699483],
      "4550": [0.359057187624530, 0.362289203770517],
      "4600": [0.357366240041146, 0.361048030584121],
      "4650": [0.355712589879109, 0.359820193374621],
      "4700": [0.354095228135586, 0.358605829603133],
      "4750": [0.352513174640586, 0.357405048467119],
      "4800": [0.350965477408777, 0.356217933228418],
      "4850": [0.349451211979616, 0.355044543372218],
      "4900": [0.347969480749661, 0.353884916608634],
      "4950": [0.346519412300469, 0.352739070727817],
      "5000": [0.345100160725069, 0.351607005318840],
      "5050": [0.343710904955591, 0.350488703361895],
      "5100": [0.342350848094336, 0.349384132702732],
      "5150": [0.341019216750211, 0.348293247417664],
      "5200": [0.339715260382228, 0.347215989076895],
      "5250": [0.338438250651491, 0.346152287913411],
      "5300": [0.337187480782876, 0.345102063904155],
      "5350": [0.335962264937442, 0.344065227769781],
      "5400": [0.334761937596386, 0.343041681898789],
      "5450": [0.333585852957265, 0.342031321201502],
      "5500": [0.332433384343009, 0.341034033898904],
      "5550": [0.331303923624177, 0.340049702251049],
      "5600": [0.330196880654761, 0.339078203229392],
      "5650": [0.329111682721794, 0.338119409137101],
      "5700": [0.328047774008889, 0.337173188181098],
      "5750": [0.327004615073793, 0.336239404999346],
      "5800": [0.325981682339978, 0.335317921146619],
      "5850": [0.324978467602219, 0.334408595541759],
      "5900": [0.323994477546069, 0.333511284879243],
      "5950": [0.323029233281125, 0.332625844007640],
      "6000": [0.322082269887888, 0.331752126277376],
      "6050": [0.321153135978060, 0.330889983860056],
      "6100": [0.320241393268040, 0.330039268041404],
      "6150": [0.319346616165388, 0.329199829489774],
      "6200": [0.318468391368004, 0.328371518502004]
    }
    return values[str(kelvin)]
