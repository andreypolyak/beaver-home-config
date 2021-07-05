import appdaemon.plugins.hass.hassapi as hass


class Alarm(hass.Hass):

  def initialize(self):
    self.person_name = self.args["person_name"]
    self.handles = []
    self.listen_event(self.cancel_alarm, event="custom_event", custom_event_data=f"cancel_alarm_{self.person_name}")
    self.listen_event(self.finish_alarm, event="custom_event", custom_event_data=f"finish_alarm_{self.person_name}")
    self.listen_event(self.start_alarm, event="custom_event", custom_event_data=f"start_alarm_{self.person_name}")


  def start_alarm(self, event_name, data, kwargs):
    self.log("Alarm started")
    self.cancel_all_handlers()
    self.call_service("input_boolean/turn_on", entity_id=f"input_boolean.alarm_{self.person_name}_ringing")
    self.handles.append(self.run_in(self.action_1, 1))
    self.handles.append(self.run_in(self.action_60, 60))
    self.handles.append(self.run_in(self.action_170, 170))
    self.handles.append(self.run_in(self.action_180, 180))
    self.handles.append(self.run_in(self.action_240, 240))
    self.handles.append(self.run_in(self.action_300, 300))
    self.handles.append(self.run_every(self.increase_volume, "now", 10))


  def cancel_alarm(self, event_name, data, kwargs):
    self.log("Alarm cancelled")
    transition = self.get_transition()
    self.call_service("input_boolean/turn_off", entity_id=f"input_boolean.alarm_{self.person_name}_ringing")
    self.cancel_all_handlers()
    self.call_service("media_player/media_pause", entity_id="media_player.bedroom_sonos")
    self.call_service("sonos/restore", entity_id="media_player.bedroom_sonos")
    self.call_service("light/turn_off", entity_id="light.group_bedroom_bri", transition=transition)
    self.call_service("light/turn_off", entity_id="light.group_bedroom_bed", transition=transition)
    self.call_service("cover/close_cover", entity_id="cover.bedroom_cover")


  def finish_alarm(self, event_name, data, kwargs):
    self.log("Alarm finished")
    transition = self.get_transition()
    hs_color = self.get_hs_color()
    self.call_service("input_boolean/turn_off", entity_id=f"input_boolean.alarm_{self.person_name}_ringing")
    self.cancel_all_handlers()
    self.call_service("media_player/media_pause", entity_id="media_player.bedroom_sonos")
    self.call_service("sonos/restore", entity_id="media_player.bedroom_sonos")
    entity = "light.group_bedroom_color"
    self.call_service("light/turn_on", entity_id=entity, brightness=254, transition=transition, hs_color=hs_color)
    self.call_service("light/turn_on", entity_id="light.bedroom_wardrobe", brightness=254, transition=transition)
    self.run_in(self.turn_on_day_scene, 1)
    self.call_service("light/turn_off", entity_id="light.group_bedroom_bed", transition=transition)
    self.run_in(self.speak_morning_info, 1)
    self.call_service("cover/open_cover", entity_id="cover.bedroom_cover")


  def action_1(self, kwargs):
    self.log("Alarm action 1")
    hs_color = self.get_hs_color()
    self.call_service("sonos/snapshot", entity_id="media_player.bedroom_sonos")
    self.call_service("media_player/media_pause", entity_id="media_player.bedroom_sonos")
    self.call_service("sonos/unjoin", entity_id="media_player.bedroom_sonos")
    self.call_service("light/turn_on", entity_id="light.bedroom_bed_led", brightness=254, hs_color=hs_color)


  def action_60(self, kwargs):
    self.log("Alarm action 60")
    self.set_sonos_volume(0.02)
    self.call_service("media_player/select_source", entity_id="media_player.bedroom_sonos", source="Sleepscapes | Rain")


  def action_170(self, kwargs):
    self.log("Alarm action 170")
    hs_color = self.get_hs_color()
    self.set_sonos_volume(0.24)
    self.call_service("light/turn_on", entity_id="light.group_bedroom_top", brightness=1, hs_color=hs_color)
    self.call_service("light/turn_on", entity_id="light.bedroom_wardrobe", brightness=1)
    self.call_service("cover/open_cover", entity_id="cover.bedroom_cover")


  def action_180(self, kwargs):
    self.log("Alarm action 180")
    self.set_sonos_volume(0.26)
    self.call_service("light/turn_on", entity_id="light.group_bedroom_top", brightness=254, transition=60)
    self.call_service("light/turn_on", entity_id="light.bedroom_wardrobe", brightness=254, transition=60)


  def action_240(self, kwargs):
    self.log("Alarm action 240")
    source = "Classic Rock 70s 80s 90s, Rock Classics - 70s Rock, 80s Rock, 90s Rock, Rock Classicos"
    self.call_service("media_player/select_source", entity_id="media_player.bedroom_sonos", source=source)


  def action_300(self, kwargs):
    self.log("Alarm action 300")
    self.call_service("light/turn_on", entity_id="light.group_bedroom_bed", brightness=254, transition=60)
    current_time = self.datetime().strftime("%H:%M")
    text = f"Пора вставать! Уже {current_time}!"
    self.fire_event("yandex_speak_text", text=text, room="bedroom", volume_level=1.0)


  def increase_volume(self, kwargs):
    sonos_state = self.get_state("media_player.bedroom_sonos", attribute="all")
    if sonos_state["state"] == "playing":
      new_volume_level = sonos_state["attributes"]["volume_level"] + 0.02
      self.set_sonos_volume(new_volume_level)


  def cancel_all_handlers(self):
    for handle in self.handles:
      if self.timer_running(handle):
        self.cancel_timer(handle)
    self.handles = []


  def get_hs_color(self):
    saturation = int(float(self.get_state("input_number.circadian_saturation")))
    hs_color = [30, saturation]
    return hs_color


  def set_sonos_volume(self, volume):
    self.call_service("media_player/volume_set", entity_id="media_player.bedroom_sonos", volume_level=volume)


  def turn_on_day_scene(self, kwargs):
    for zone in ["seleeping", "living"]:
      entity = f"input_select.{zone}_scene"
      if self.get_state(entity) == "night":
        self.log(f"Turning on day scene in {zone} zone")
        self.call_service("input_select/select_option", entity_id=entity, option="day")


  def speak_morning_info(self, kwargs):
    hour = int(self.datetime().strftime("%H"))
    minute = self.datetime().strftime("%M")
    text = ""
    if hour < 4:
      text += "Доброй ночи!"
    elif hour >= 4 and hour < 12:
      text += "Доброе утро!"
    elif hour >= 12 and hour < 18:
      text += "Добрый день!"
    elif hour >= 18:
      text += "Добрый вечер!"
    text += f" Сейчас {hour}:{minute}."
    weather = self.get_state("weather.home_hourly", attribute="all")
    current_temp = round(weather["attributes"]["temperature"])
    current_temp_degrees = self.morph_degrees(current_temp)
    text += f" За окном {current_temp} {current_temp_degrees}."
    min_temp = 9999
    max_temp = -9999
    will_rain = False
    will_snow = False
    for forecast in weather["attributes"]["forecast"][:12]:
      if forecast["temperature"] < min_temp:
        min_temp = round(forecast["temperature"])
      if forecast["temperature"] > max_temp:
        max_temp = round(forecast["temperature"])
      if "rainy" in forecast["condition"]:
        will_rain = True
      if "snowy" in forecast["condition"]:
        will_snow = True
    if min_temp != max_temp:
      max_temp_degrees = self.morph_degrees_range(max_temp)
      text += f" Сегодня будет от {min_temp} до {max_temp} {max_temp_degrees}."
    else:
      min_temp_degrees = self.morph_degrees(min_temp)
      text += f" Сегодня будет {min_temp} {min_temp_degrees}."
    if will_snow:
      text += " Возможен снег."
    elif will_rain:
      text += " Возможен дождь."
    else:
      text += " Осадки не ожидаются."
    self.fire_event("yandex_speak_text", text=text, room="living_room", volume_level=1.0)


  def morph_degrees(self, temp):
    abs_temp = abs(temp)
    if abs_temp >= 10 and abs_temp <= 14:
      return "градусов"
    elif abs_temp % 10 == 1:
      return "градус"
    elif abs_temp % 10 >= 2 and abs_temp % 10 <= 4:
      return "градуса"
    return "градусов"


  def morph_degrees_range(self, temp):
    abs_temp = abs(temp)
    if abs_temp % 10 == 1:
      return "градуса"
    return "градусов"


  def get_transition(self):
    return float(self.get_state("input_number.transition"))
