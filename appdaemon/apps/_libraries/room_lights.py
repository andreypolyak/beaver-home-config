import appdaemon.plugins.hass.hassapi as hass
import random
import json

FADE_DURATION = 60
COOLDOWN_DELAY = 60


class RoomLights(hass.Hass):

  def room_init(self):
    self.current_preset = "BRIGHT"
    self.person_inside = False
    self.supported_features = {}
    self.state_before_fade = {}
    self.is_max_delay = False
    self.is_min_delay = False
    self.allow_button_hold = True
    self.handle = None
    self.listen_state(self.__on_scene, f"input_select.{self.zone}_scene")
    for sensor in self.sensors:
      self.listen_state(self.__on_sensor, sensor[0], mode=sensor[1])
    for switch in self.switches:
      self.listen_state(self.__on_switch, switch[0], mode=switch[1])
    self.listen_event(self.__on_timer_finished, "timer.finished", entity_id=f"timer.light_{self.room}")
    self.listen_event(self.__on_faded_timer_finished, "timer.finished", entity_id=f"timer.light_faded_{self.room}")
    for operation in ["on", "off", "toggle"]:
      custom_event_data = f"{self.room}_virtual_switch_room_{operation}"
      self.listen_event(self.__on_virtual_switch, "custom_event", custom_event_data=custom_event_data)
      for light in self.__build_list_of_individual_lights():
        custom_event_data = f"{light}_virtual_switch_individual_{operation}"
        self.listen_event(self.__on_individual_virtual_switch, "custom_event", custom_event_data=custom_event_data)
    self.listen_event(self.__on_set_manual_color, "custom_event", custom_event_data=f"{self.room}_set_manual_color")
    self.listen_event(self.__on_set_auto_color, "custom_event", custom_event_data=f"{self.room}_set_auto_color")
    self.listen_event(self.__on_set_brightness, "custom_event", custom_event_data=f"{self.room}_set_brightness")
    self.listen_event(self.__on_toggle_max_brightness, "custom_event",
                      custom_event_data=f"{self.room}_toggle_max_brightness")
    self.listen_state(self.__on_lights_off, f"light.ha_group_{self.room}", new="off")
    self.listen_state(self.__on_circadian_change, "input_number.circadian_saturation")

# Control

  def turn_preset(self, preset, mode, state, min_delay=False, brightness=None,
                  hs_color=None, rgb_color=None, kelvin=None):
    self.__cancel_light_timers()
    self.is_min_delay = min_delay
    self.is_max_delay = False
    self.current_preset = preset
    turn_off_all = True
    for light, light_params in self.presets[preset].items():
      new_state = light_params["state"]
      if "{{" in new_state and "}}" in new_state:
        new_state = self.render_template(new_state)
      if new_state == "on":
        turn_off_all = False
        if not brightness and "attributes" in light_params and "brightness" in light_params["attributes"]:
          light_brightness = light_params["attributes"]["brightness"]
        else:
          light_brightness = brightness
        kwargs = {
          "brightness": light_brightness,
          "hs_color": hs_color,
          "rgb_color": rgb_color,
          "kelvin": kelvin
        }
        args = self.__build_light_args("on", light, state, **kwargs)
        self.__turn_on_ha_light(light, args)
      elif new_state == "off":
        args = self.__build_light_args("off", light, state)
        self.__turn_off_ha_light(light, args)

    if turn_off_all and "switch" in mode and mode != "virtual_switch":
      self.__set_cooldown_timer()
    elif "motion_sensor" not in mode:
      self.__cancel_cooldown_timer()

    if not turn_off_all:
      self.__set_light_timers()


  def turn_preset_if_on(self, preset, mode, state, min_delay=False):
    self.current_preset = preset
    is_light_on = self.__is_room_light_on(state)
    if is_light_on:
      self.turn_preset(preset, mode, state, min_delay=min_delay)


  def light_toggle(self, preset, operation, mode, state, min_delay=False):
    self.current_preset = preset
    is_light_on = self.__is_room_light_on(state)
    if operation == "off" or (is_light_on and operation != "on"):
      self.turn_off_all(state)
      if "switch" in mode:
        self.__set_cooldown_timer()
    else:
      self.turn_preset(preset, mode, state, min_delay=min_delay)


  def turn_off_all(self, state):
    self.log(f"Turning off all lights in {self.room}")
    for light in self.turn_off_lights:
      args = self.__build_light_args("off", light, state)
      self.__turn_off_ha_light(light, args)
    self.__cancel_light_timers()
    self.__cancel_cooldown_timer()


  def night_scene_light_toggle(self, preset, operation, mode, state, min_delay=False):
    is_light_on = self.__is_room_light_on(state)
    if is_light_on:
      self.light_toggle(preset, operation, mode, state)
    else:
      self.turn_preset(preset, mode, state)
      self.turn_on_scene("day")


  def turn_preset_or_restore(self, preset, mode, state, min_delay=False, turn_on=True):
    self.current_preset = preset
    self.__cancel_light_timers()
    is_light_on = self.__is_room_light_on(state)
    is_faded = self.__is_room_faded(state)
    cooldown_timer_not_active = state["timers"]["light_cooldown_period"] != "active"
    if is_light_on and is_faded:
      self.__restore_previous_state(state)
    elif is_light_on:
      self.__set_light_timers()
    elif cooldown_timer_not_active and turn_on:
      self.turn_preset(preset, mode, state, min_delay=min_delay)


  def toggle_brightness(self, action, state):
    if not self.__handle_button_hold(action):
      return
    if action == "brightness_up":
      self.__toggle_max_brightness()
    elif action == "brightness_down":
      self.__toggle_min_brightness()
    self.handle = self.run_in(self.__allow_button_hold, 3)


  def overwrite_scene(self, action, scene, preset, state):
    if not self.__handle_button_hold(action):
      return
    if action in ["brightness_up", "brightness_down"]:
      self.turn_on_scene(scene)
      self.turn_preset(preset, "long_press", state)
    self.handle = self.run_in(self.__allow_button_hold, 3)


  def __toggle_max_brightness(self):
    state = self.get_lights_state()
    if state["booleans"]["auto_colors"]:
      self.__set_max_brightness(state)
    else:
      self.__set_auto_color(state)


  def __toggle_min_brightness(self):
    state = self.get_lights_state()
    room_lights = state["lights"][f"ha_group_{self.room}"]
    if room_lights["state"] == "on" and room_lights["attributes"]["brightness"] <= 3:
      self.__set_brightness(254, state, turn_on_all=True)
    else:
      self.__set_min_brightness(state)


  def individual_light_toggle(self, light, preset, operation, state):
    is_light_on = self.__is_individual_light_on(light, state)
    if operation == "off" or (operation == "toggle" and is_light_on):
      args = self.__build_light_args("off", light, state)
      self.__turn_off_ha_light(light, args)
      is_any_light_is_on = self.__is_any_light_is_on(state, except_light=light)
      if not is_any_light_is_on:
        self.__cancel_light_timers()
        self.__set_cooldown_timer()
        return
    else:
      brightness = self.__get_max_brightness_in_current_preset()
      args = self.__build_light_args("on", light, state, brightness=brightness)
      self.__turn_on_ha_light(light, args)
    self.__set_light_timers()
    self.__cancel_cooldown_timer()


  def __set_brightness(self, brightness, state, turn_off_if_no_brightness=False, turn_on_all=False):
    lights = self.__build_list_of_individual_lights()
    is_any_light_is_on = self.__is_any_light_is_on(state)
    if not is_any_light_is_on:
      self.turn_preset(self.current_preset, "set_brightness", state, min_delay=self.is_min_delay, brightness=brightness)
      return
    for light in lights:
      supported_features = self.__get_supported_features(light, state)
      is_light_on = self.__is_individual_light_on(light, state)
      if supported_features["brightness"] and (is_light_on or turn_on_all):
        args = self.__build_light_args("on", light, state, brightness=brightness, ignore_color=True)
        self.__turn_on_ha_light(light, args)
      elif not supported_features["brightness"] and turn_off_if_no_brightness:
        args = self.__build_light_args("off", light, state)
        self.__turn_off_ha_light(light, args)
      elif not supported_features["brightness"] and turn_on_all:
        args = self.__build_light_args("on", light, state)
        self.__turn_on_ha_light(light, args)
    self.__set_light_timers()
    self.__cancel_cooldown_timer()


  def __restore_previous_state(self, state):
    for light_name, light_group in self.lights.items():
      # Light group without children lights
      if len(light_group) == 0:
        light_args = self.__build_light_args_for_restore(light_name, state)
        if light_args is not None:
          self.__turn_on_ha_light(light_name, light_args)
      # Light group with children
      else:
        light_group_args = {}
        for individual_light_name in light_group:
          light_args = self.__build_light_args_for_restore(individual_light_name, state)
          if light_args is not None:
            light_group_args[individual_light_name] = json.dumps(light_args)
        args_are_same = len(set(light_group_args.values())) == 1
        turn_on_all = len(light_group_args.values()) == len(light_group)
        turn_on_any = len(set(light_group_args.values())) > 0
        # Turn on group
        if args_are_same and turn_on_all:
          light_args = json.loads(list(light_group_args.values())[0])
          self.__turn_on_ha_light(light_name, light_args)
        # Turn on individually
        elif turn_on_any:
          for individual_light_name, light_args in light_group_args.items():
            light_args = json.loads(light_args)
            self.__turn_on_ha_light(individual_light_name, light_args)
    self.is_max_delay = True
    self.__set_light_timers()


  def __build_light_args_for_restore(self, light, state):
    if "lights" not in self.state_before_fade:
      self.state_before_fade = state
    light_params = self.state_before_fade["lights"][light]
    args = None
    if light_params["state"] == "on":
      args = {}
      supported_features = self.__get_supported_features(light, self.state_before_fade)
      light_attributes = light_params["attributes"]
      if "brightness" in light_attributes and supported_features["brightness"]:
        if light_attributes["brightness"] != 2:
          args["brightness"] = light_attributes["brightness"]
        else:
          args["brightness"] = 254
      if "hs_color" in light_attributes and supported_features["color"]:
        args["hs_color"] = light_attributes["hs_color"]
      elif "color_temp" in light_attributes and supported_features["temperature"]:
        args["color_temp"] = light_attributes["color_temp"]
      if supported_features["transition"]:
        args["transition"] = self.__get_transition()
    return args


  def __fade_lamp(self, light, state):
    if state["lights"][light]["state"] != "on":
      return False
    elif state["timers"]["light"] != "idle":
      return False
    elif hasattr(self, "ignore_fade_lights") and light in self.ignore_fade_lights:
      return False
    supported_features = self.__get_supported_features(light, state)
    args = {}
    if (
      supported_features["brightness"]
      and "brightness" in state["lights"][light]["attributes"]
      and state["lights"][light]["state"] == "on"
      and state["lights"][light]["attributes"]["brightness"] > 3
    ):
      args["brightness"] = 2
      if supported_features["transition"]:
        args["transition"] = 2
      self.log(f"Fading {light} light")
      self.__turn_on_ha_light(light, args)
      return True
    else:
      self.__turn_off_ha_light(light, {})
      return False


  def turn_on_scene(self, scene):
    self.log(f"Turning on {scene} scene")
    self.call_service("input_select/select_option", entity_id=f"input_select.{self.zone}_scene", option=scene)
    return True


  def __on_circadian_change(self, entity, attribute, old, new, kwargs):
    state = self.get_lights_state()
    lights = self.__build_list_of_individual_lights()
    should_circadian_update = self.get_state("input_boolean.circadian_update") == "on"
    current_scene = self.get_state(f"input_select.{self.zone}_scene")
    if (
      not should_circadian_update
      or not state["booleans"]["auto_colors"]
      or current_scene not in ["day", "light_cinema"]
    ):
      return
    for light in lights:
      is_light_on = self.__is_individual_light_on(light, state)
      if is_light_on:
        args = self.__build_light_args("on", light, state, transition=2)
        self.__turn_on_ha_light(light, args)


  def __set_auto_color(self, state):
    lights = self.__build_list_of_individual_lights()
    is_any_light_is_on = self.__is_any_light_is_on(state)
    if not is_any_light_is_on:
      self.turn_preset(self.current_preset, "set_auto_color", state, min_delay=self.is_min_delay)
      self.__turn_on_auto_colors()
      return
    for light in lights:
      is_light_on = self.__is_individual_light_on(light, state)
      if is_light_on:
        args = self.__build_light_args("on", light, state)
        self.__turn_on_ha_light(light, args)
    self.__turn_on_auto_colors()
    self.__set_light_timers()
    self.__cancel_cooldown_timer()


  def __set_manual_color(self, state, rgb_color=None, hs_color=None, kelvin=None, brightness=None, turn_on_all=False):
    self.__turn_off_auto_colors()
    self.log(f"rgb_color: {rgb_color}, hs_color: {hs_color}, kelvin: {kelvin}")
    lights = self.__build_list_of_individual_lights()
    is_any_light_is_on = self.__is_any_light_is_on(state)
    if not is_any_light_is_on:
      kwargs = {
        "min_delay": self.is_min_delay,
        "hs_color": hs_color,
        "rgb_color": rgb_color,
        "kelvin": kelvin
      }
      self.turn_preset(self.current_preset, "set_auto_color", state, **kwargs)
      return
    for light in lights:
      is_light_on = self.__is_individual_light_on(light, state)
      if is_light_on or turn_on_all:
        args = self.__build_light_args("on", light, state, hs_color=hs_color, rgb_color=rgb_color,
                                       kelvin=kelvin, brightness=brightness)
        self.__turn_on_ha_light(light, args)
    self.__set_light_timers()
    self.__cancel_cooldown_timer()


  def __set_max_brightness(self, state):
    # For some reason HA returns supported features=44 (no color support) for all light groups
    # supported_features = self.__get_supported_features(f"ha_group_{self.room}", state)
    supported_features = self.__get_supported_features(f"ha_template_room_{self.room}", state)
    self.log(f"supported_features: {supported_features}")
    if supported_features["color"]:
      self.__set_manual_color(state, hs_color=[30, 33], brightness=254, turn_on_all=True)
    elif supported_features["temperature"]:
      self.__set_manual_color(state, kelvin=4700, brightness=254, turn_on_all=True)
    else:
      self.__set_brightness(254, state)


  def __set_min_brightness(self, state):
    self.__set_auto_color(state)
    self.__set_brightness(3, state, turn_off_if_no_brightness=True)


  def is_cover_active(self):
    entity = f"input_boolean.{self.room}_cover_active"
    if self.entity_exists(entity) and self.get_state(entity) == "on":
      return True
    return False

# Callbacks

  def __on_scene(self, entity, attribute, old, new, kwargs):
    self.__turn_on_auto_colors()
    self.__turn_on_auto_lights()
    func_name = f"on_{old}"
    func = getattr(self, func_name, None)
    state = self.get_lights_state()
    entity = entity.replace("input_select.", "")
    mode = "old_scene"
    if callable(func):
      res = func(old, mode, state, new=new, old=old, entity=entity)
      if res is not False:
        self.write_to_log(old, mode, entity, new, old)
    func_name = f"on_{new}"
    func = getattr(self, func_name, None)
    mode = "new_scene"
    if callable(func):
      res = func(new, mode, state, new=new, old=old, entity=entity)
      if res is not False:
        self.write_to_log(new, mode, entity, new, old)


  def __on_sensor(self, entity, attribute, old, new, kwargs):
    if new in ["unavailable", "unknown", "None", ""]:
      return
    scene = self.get_state(f"input_select.{self.zone}_scene")
    func_name = f"on_{scene}"
    func = getattr(self, func_name, None)
    state = self.get_lights_state()
    entity = entity.replace("binary_sensor.", "").replace("sensor.", "")
    mode = kwargs["mode"]
    if callable(func):
      res = func(scene, mode, state, new=new, old=old, entity=entity)
      if res is not False:
        self.write_to_log(scene, mode, entity, new, old)


  def __on_switch(self, entity, attribute, old, new, kwargs):
    scene = self.get_state(f"input_select.{self.zone}_scene")
    func_name = f"on_{scene}"
    func = getattr(self, func_name, None)
    state = self.get_lights_state()
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
      res = func(scene, mode, state, new=new, old=old, entity=entity)
      if res is not False:
        self.write_to_log(scene, mode, entity, new, old)


  def __on_virtual_switch(self, event_name, data, kwargs):
    scene = self.get_state(f"input_select.{self.zone}_scene")
    event_data = data["custom_event_data"]
    func_name = f"on_{scene}"
    func = getattr(self, func_name, None)
    state = self.get_lights_state()
    operation = "toggle"
    if "_virtual_switch_room_on" in event_data:
      operation = "on"
    elif "_virtual_switch_room_off" in event_data:
      operation = "off"
    entity = f"ha_template_{self.room}"
    mode = "virtual_switch"
    if callable(func):
      res = func(scene, mode, state, new=operation, entity=entity)
      if res is not False:
        self.write_to_log(scene, mode, entity, operation, None)


  def __on_individual_virtual_switch(self, event_name, data, kwargs):
    event_data = data["custom_event_data"]
    operation = "toggle"
    if "_virtual_switch_individual_on" in event_data:
      operation = "on"
    elif "_virtual_switch_individual_off" in event_data:
      operation = "off"
    light = data["custom_event_data"].replace(f"_virtual_switch_individual_{operation}", "")
    state = self.get_lights_state()
    preset = self.current_preset
    self.individual_light_toggle(light, preset, operation, state)


  def __on_set_manual_color(self, event_name, data, kwargs):
    state = self.get_lights_state()
    rgb_color = None
    hs_color = None
    kelvin = None
    input_color = data["custom_event_data2"]
    if isinstance(input_color, list) and len(input_color) == 3:
      rgb_color = input_color
      self.__set_manual_color(state, rgb_color=rgb_color)
    elif isinstance(input_color, list) and len(input_color) == 2:
      hs_color = input_color
      self.__set_manual_color(state, hs_color=hs_color)
    else:
      kelvin = input_color
      self.__set_manual_color(state, kelvin=kelvin)


  def __on_set_auto_color(self, event_name, data, kwargs):
    state = self.get_lights_state()
    self.__set_auto_color(state)


  def __on_set_brightness(self, event_name, data, kwargs):
    state = self.get_lights_state()
    brightness = int(data["custom_event_data2"])
    self.__set_brightness(brightness, state)


  def __on_toggle_max_brightness(self, event_name, data, kwargs):
    self.__toggle_max_brightness()


  def __on_lights_off(self, entity, attribute, old, new, kwargs):
    self.__turn_on_auto_colors()

# Timers

  def __on_faded_timer_finished(self, event_name, data, kwargs):
    self.is_max_delay = False
    state = self.get_lights_state()
    reason = self.should_turn_off_by_timer()
    if not reason or reason == "person_inside":
      for light in self.turn_off_lights:
        args = self.__build_light_args("off", light, state)
        self.__turn_off_ha_light(light, args)
    else:
      self.__set_light_timers()
      self.log(f"Lights were not turned off because of: {reason}")


  def __on_timer_finished(self, event_name, data, kwargs):
    state = self.get_lights_state()
    reason = self.should_turn_off_by_timer()
    if reason:
      self.__set_light_timers()
      self.log(f"Lights were not faded because of: {reason}")
      return
    self.state_before_fade = state
    is_any_faded = False
    for light_name, light_group in self.lights.items():
      # Light group without children lights
      if len(light_group) == 0:
        result = self.__fade_lamp(light_name, state)
        is_any_faded = is_any_faded or result
      # Light group with children
      else:
        fade_any = False
        turn_off_any = False
        for individual_light_name in light_group:
          if self.__light_should_be_faded(individual_light_name, state):
            fade_any = True
          else:
            turn_off_any = True
        if fade_any != turn_off_any:
          result = self.__fade_lamp(light_name, state)
          is_any_faded = is_any_faded or result
        else:
          for individual_light_name in light_group:
            result = self.__fade_lamp(individual_light_name, state)
            is_any_faded = is_any_faded or result
    if is_any_faded:
      self.__set_faded_timer()


  def __set_light_timers(self):
    if self.get_state(f"input_boolean.{self.zone}_zone_min_delay") == "on":
      delay = self.min_delay
    elif self.is_max_delay:
      delay = self.max_delay
    else:
      delay = self.delay
    delay += random.randrange(60)
    self.call_service("timer/start", entity_id=f"timer.light_{self.room}", duration=delay)


  def __cancel_light_timers(self):
    self.call_service("timer/cancel", entity_id=f"timer.light_{self.room}")
    self.call_service("timer/cancel", entity_id=f"timer.light_faded_{self.room}")


  def __set_cooldown_timer(self):
    self.call_service("timer/start", entity_id=f"timer.light_cooldown_period_{self.room}", duration=COOLDOWN_DELAY)


  def __cancel_cooldown_timer(self):
    self.call_service("timer/cancel", entity_id=f"timer.light_cooldown_period_{self.room}")


  def __set_faded_timer(self):
    self.call_service("timer/start", entity_id=f"timer.light_faded_{self.room}", duration=FADE_DURATION)

# Helpers

  def get_scene_turned_on_period(self):
    scene_last_changed_str = self.get_state(f"input_select.{self.zone}_scene", attribute="last_changed")
    scene_last_changed = self.convert_utc(scene_last_changed_str).timestamp()
    diff = self.get_now_ts() - scene_last_changed
    return diff


  def write_to_log(self, scene, mode, entity, new, old):
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


  def __get_supported_features(self, light, state):
    if light in self.supported_features:
      return self.supported_features[light]
    features = {
      "brightness": False,
      "color": False,
      "transition": False,
      "temperature": False
    }
    try:
      supported_features = state["lights"][light]["attributes"]["supported_features"]
    except KeyError:
      supported_features = self.get_state(f"light.{light}", attribute="supported_features")
    supported_features_str = str(format(supported_features, "b")).rjust(8, "0")
    if supported_features_str[7] == "1":
      features["brightness"] = True
    if supported_features_str[3] == "1":
      features["color"] = True
    if supported_features_str[2] == "1":
      features["transition"] = True
    if supported_features_str[6] == "1":
      features["temperature"] = True
    self.supported_features[light] = features
    self.log(f"Supported features for {light}: {features}", level="DEBUG")
    return features


  def get_lights_state(self):
    state = {
      "lights": {},
      "sensors": {},
      "timers": {},
      "booleans": {}
    }
    for light, group_lights in self.lights.items():
      state["lights"][light] = self.get_state(f"light.{light}", attribute="all")
      for light in group_lights:
        state["lights"][light] = self.get_state(f"light.{light}", attribute="all")
    for light in self.turn_off_lights:
      state["lights"][light] = self.get_state(f"light.{light}", attribute="all")
    light = f"ha_group_{self.room}"
    state["lights"][light] = self.get_state(f"light.{light}", attribute="all")
    for _, preset in self.presets.items():
      for light in preset:
        if light not in state["lights"]:
          state["lights"][light] = self.get_state(f"light.{light}", attribute="all")
    for sensor in self.sensors:
      sensor_name = sensor[0].replace("binary_sensor.", "")
      state["sensors"][sensor_name] = self.get_state(sensor[0])
    state["timers"]["light_faded"] = self.get_state(f"timer.light_faded_{self.room}")
    state["timers"]["light"] = self.get_state(f"timer.light_{self.room}")
    state["timers"]["light_cooldown_period"] = self.get_state(f"timer.light_cooldown_period_{self.room}")
    state["booleans"]["auto_colors"] = self.get_state(f"input_boolean.auto_colors_{self.room}") == "on"
    state["booleans"]["auto_lights"] = self.get_state(f"input_boolean.auto_lights_{self.room}") == "on"
    return state


  def is_person_inside(self):
    is_person_inside = False
    entity = f"input_boolean.person_inside_{self.room}"
    if self.entity_exists(entity) and self.get_state(entity) == "on":
      is_person_inside = True
    return is_person_inside


  def is_door_open(self, state, sensor):
    return state["sensors"][sensor] == "on"


  def is_auto_lights(self):
    if self.get_state(f"input_boolean.auto_lights_{self.room}") == "on":
      return True
    return False


  def __build_light_args(self, operation, light, state, brightness=None, hs_color=None,
                         rgb_color=None, kelvin=None, ignore_color=False, transition=None):
    args = {}
    supported_features = self.__get_supported_features(light, state)
    if supported_features["transition"]:
      if transition:
        args["transition"] = transition
      else:
        args["transition"] = self.__get_transition()
    if operation == "on":
      if supported_features["color"] and not ignore_color:
        if rgb_color:
          args["rgb_color"] = rgb_color
        elif hs_color:
          args["hs_color"] = hs_color
        else:
          saturation = int(float(self.get_state("input_number.circadian_saturation")))
          args["hs_color"] = [30, saturation]
      elif supported_features["temperature"] and not ignore_color:
        if kelvin:
          args["kelvin"] = kelvin
        else:
          ct = int(float(self.get_state("input_number.circadian_kelvin")))
          args["kelvin"] = ct
      if brightness and supported_features["brightness"]:
        args["brightness"] = brightness
    return args


  def __build_list_of_individual_lights(self):
    individual_lights = []
    for light_name, light_group in self.lights.items():
      if len(light_group) == 0:
        individual_lights.append(light_name)
      else:
        for light in light_group:
          individual_lights.append(light)
    return individual_lights


  def __allow_button_hold(self, kwargs):
    self.allow_button_hold = True


  def __is_any_light_is_on(self, state, except_light=None):
    individual_lights = self.__build_list_of_individual_lights()
    is_any_light_is_on = False
    for individual_light in individual_lights:
      if individual_light != except_light and state["lights"][individual_light]["state"] == "on":
        is_any_light_is_on = True
    return is_any_light_is_on


  def __get_max_brightness_in_current_preset(self):
    brightness = -1
    for light, light_params in self.presets[self.current_preset].items():
      if "attributes" in light_params and "brightness" in light_params["attributes"]:
        light_brightness = light_params["attributes"]["brightness"]
        if light_brightness > brightness:
          brightness = light_brightness
    if brightness == -1:
      brightness = 254
    return brightness


  def __get_transition(self):
    return float(self.get_state("input_number.transition"))


  def __is_room_light_on(self, state):
    return state["lights"][f"ha_group_{self.room}"]["state"] == "on"


  def __is_individual_light_on(self, light, state):
    return state["lights"][light]["state"] == "on"


  def __turn_on_ha_light(self, light, args):
    self.call_service("light/turn_on", entity_id=f"light.{light}", **args)
    self.log(f"Turned on {light} with following parameters: {args}")


  def __turn_off_ha_light(self, light, args):
    self.call_service("light/turn_off", entity_id=f"light.{light}", **args)
    self.log(f"Turned off {light} with following parameters: {args}")


  def __is_room_faded(self, state):
    if state["timers"]["light_faded"] == "active":
      return True
    if (
      "brightness" in state["lights"][f"ha_group_{self.room}"]["attributes"]
      and state["lights"][f"ha_group_{self.room}"]["attributes"]["brightness"] == 2
    ):
      return True
    return False


  def __light_should_be_faded(self, light, state):
    supported_features = self.__get_supported_features(light, state)
    if (
      supported_features["brightness"]
      and "brightness" in state["lights"][light]["attributes"]
      and state["lights"][light]["state"] == "on"
      and state["lights"][light]["attributes"]["brightness"] > 3
    ):
      return True
    return False


  def __turn_on_auto_colors(self):
    self.call_service("input_boolean/turn_on", entity_id=f"input_boolean.auto_colors_{self.room}")


  def __turn_off_auto_colors(self):
    self.call_service("input_boolean/turn_off", entity_id=f"input_boolean.auto_colors_{self.room}")


  def __turn_on_auto_lights(self):
    self.call_service("input_boolean/turn_on", entity_id=f"input_boolean.auto_lights_{self.room}")


  def __handle_button_hold(self, action):
    if self.timer_running(self.handle):
      self.cancel_timer(self.handle)
    if action == "brightness_stop":
      self.allow_button_hold = True
      return False
    if not self.allow_button_hold:
      return False
    self.allow_button_hold = False
    return True
