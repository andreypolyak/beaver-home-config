import appdaemon.plugins.hass.hassapi as hass

ROOMS = [
  "bathroom_entrance",
  "living_room",
  "kitchen"
]


class Night(hass.Hass):

  def initialize(self):
    self.storage = self.get_app("persistent_storage")
    self.storage.init("night.day_scene_in_sleeping_zone_ts", 0)
    self.handle = None
    self.listen_state(self.on_change, "input_select.sleeping_scene")
    self.listen_state(self.on_change, "input_select.living_scene")
    for room in ROOMS:
      self.listen_state(self.on_change, f"light.ha_template_room_{room}")


  def on_change(self, entity, attribute, old, new, kwargs):
    if entity == "input_select.sleeping_scene" and new == "day" and old == "night":
      self.storage.write("night.day_scene_in_sleeping_zone_ts", self.get_now_ts())
      if self.get_state("input_select.living_scene") == "night":
        self.call_service("input_select/select_option", entity_id="input_select.living_scene", option="day")
    if self.check_night_conditions():
      self.log("Setting timer to automatically turn on night scene in living zone")
      # self.handle = self.run_in(self.set_living_night, 240)
      self.handle = self.run_in(self.set_living_night, 1)
    elif self.timer_running(self.handle):
      self.cancel_timer(self.handle)


  def check_night_conditions(self):
    living_scene = self.get_state("input_select.living_scene")
    sleeping_scene = self.get_state("input_select.sleeping_scene")
    is_all_lights_off = True
    day_scene_in_sleeping_zone_ts = self.storage.read("night.day_scene_in_sleeping_zone_ts")
    for room in ROOMS:
      if self.get_state(f"light.ha_template_room_{room}") == "on":
        is_all_lights_off = False
    if (
      sleeping_scene == "night"
      and living_scene == "day"
      and is_all_lights_off
      and (self.get_now_ts() - day_scene_in_sleeping_zone_ts) > 600
    ):
      return True
    return False


  def set_living_night(self, kwargs):
    if self.check_night_conditions():
      self.log("Automatically turned on night scene in living zone")
      self.call_service("input_select/select_option", entity_id="input_select.living_scene", option="night")
