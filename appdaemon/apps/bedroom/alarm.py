from base import Base


class Alarm(Base):

  def initialize(self):
    super().initialize()
    self.person_name = self.args["person_name"]
    self.handles = []
    self.listen_event(self.cancel_alarm, event="custom_event", custom_event_data=f"cancel_alarm_{self.person_name}")
    self.listen_event(self.finish_alarm, event="custom_event", custom_event_data=f"finish_alarm_{self.person_name}")
    self.listen_event(self.start_alarm, event="custom_event", custom_event_data=f"start_alarm_{self.person_name}")


  def start_alarm(self, event_name, data, kwargs):
    self.log("Alarm started")
    self.cancel_all_handles()
    self.turn_on_entity(f"input_boolean.alarm_{self.person_name}_ringing")
    self.handles.append(self.run_in(self.action_1, 1))
    self.handles.append(self.run_in(self.action_60, 60))
    self.handles.append(self.run_in(self.action_170, 170))
    self.handles.append(self.run_in(self.action_180, 180))
    self.handles.append(self.run_in(self.action_240, 240))
    self.handles.append(self.run_in(self.action_300, 300))
    self.handles.append(self.run_every(self.increase_volume, "now", 10))


  def cancel_alarm(self, event_name, data, kwargs):
    self.log("Alarm cancelled")
    transition = self.get_float_state("input_number.transition")
    self.turn_off_entity(f"input_boolean.alarm_{self.person_name}_ringing")
    self.cancel_all_handles()
    self.media_pause("bedroom_sonos")
    self.sonos_restore("bedroom_sonos")
    self.turn_off_entity("light.group_bedroom_bri", transition=transition)
    self.turn_off_entity("light.group_bedroom_bed", transition=transition)
    self.close_cover("bedroom_cover")


  def finish_alarm(self, event_name, data, kwargs):
    self.log("Alarm finished")
    transition = self.get_float_state("input_number.transition")
    self.turn_off_entity(f"input_boolean.alarm_{self.person_name}_ringing")
    self.cancel_all_handles()
    self.media_pause("bedroom_sonos")
    self.sonos_restore("bedroom_sonos")
    self.turn_on_entity("light.group_bedroom_color", brightness=254, transition=transition, hs_color=self.hs_color)
    self.turn_on_entity("light.bedroom_wardrobe", brightness=254, transition=transition)
    self.run_in(self.turn_on_day_scene, 1)
    self.turn_off_entity("light.group_bedroom_bed", transition=transition)
    self.run_in(self.speak_morning_info, 1)
    self.open_cover("bedroom_cover")


  def action_1(self, kwargs):
    self.log("Alarm action 1")
    self.sonos_snapshot("bedroom_sonos")
    self.media_pause("bedroom_sonos")
    self.sonos_unjoin("bedroom_sonos")
    self.turn_on_entity("light.bedroom_bed_led", brightness=254, hs_color=self.hs_color)


  def action_60(self, kwargs):
    self.log("Alarm action 60")
    self.volume_set("bedroom_sonos", 0.02)
    self.select_source("bedroom_sonos", "Sleepscapes | Rain")


  def action_170(self, kwargs):
    self.log("Alarm action 170")
    self.volume_set("bedroom_sonos", 0.24)
    self.turn_on_entity("light.group_bedroom_top", brightness=1, hs_color=self.hs_color)
    self.turn_on_entity("light.bedroom_wardrobe", brightness=1)
    self.open_cover("bedroom_cover")


  def action_180(self, kwargs):
    self.log("Alarm action 180")
    self.volume_set("bedroom_sonos", 0.26)
    self.turn_on_entity("light.group_bedroom_top", brightness=254, transition=60)
    self.turn_on_entity("light.bedroom_wardrobe", brightness=254, transition=60)


  def action_240(self, kwargs):
    self.log("Alarm action 240")
    source = "Classic Rock 70s 80s 90s, Rock Classics - 70s Rock, 80s Rock, 90s Rock, Rock Classicos"
    self.select_source("bedroom_sonos", source)


  def action_300(self, kwargs):
    self.log("Alarm action 300")
    self.turn_on_entity("light.group_bedroom_bed", brightness=254, transition=60)
    current_time = self.datetime().strftime("%H:%M")
    text = f"Пора вставать! Уже {current_time}!"
    self.fire_event("yandex_speak_text", text=text, room="bedroom", volume_level=1.0)


  def increase_volume(self, kwargs):
    sonos_state = self.get_state("media_player.bedroom_sonos", attribute="all")
    if sonos_state["state"] == "playing":
      new_volume_level = sonos_state["attributes"]["volume_level"] + 0.02
      self.volume_set("bedroom_sonos", new_volume_level)


  def cancel_all_handles(self):
    for handle in self.handles:
      self.cancel_handle(handle)
    self.handles = []


  @property
  def hs_color(self):
    saturation = self.get_int_state("input_number.circadian_saturation")
    hs_color = [30, saturation]
    return hs_color


  def turn_on_day_scene(self, kwargs):
    for zone in ["seleeping", "living"]:
      if self.get_scene(zone) == "night":
        self.log(f"Turning on day scene in {zone} zone")
        self.set_scene(zone, "day")


  def speak_morning_info(self, kwargs):
    text = self.get_forecast(current_time=True)[0]
    self.fire_event("yandex_speak_text", text=text, room="living_room", volume_level=1.0)
