import appdaemon.plugins.hass.hassapi as hass

LIVING_ZONE_ROOMS = [
  "bathroom_entrance",
  "living_room",
  "kitchen"
]


class Night(hass.Hass):

  def initialize(self):
    self.storage = self.get_app("persistent_storage")
    self.storage.init("night.night_in_sleeping_ts", 0)
    self.storage.init("night.day_in_living_ts", 0)
    self.listen_state(self.on_change, "input_select.sleeping_scene")
    self.listen_state(self.on_change, "input_select.living_scene")
    for room in LIVING_ZONE_ROOMS:
      self.listen_state(self.on_change, f"light.ha_template_room_{room}")


  def on_change(self, entity, attribute, old, new, kwargs):
    if entity == "input_select.sleeping_scene" and new == "night":
      self.storage.write("night.night_in_sleeping_ts", self.get_now_ts())
    if entity == "input_select.living_scene" and new == "day" and old == "night":
      self.storage.write("night.day_in_living_ts", self.get_now_ts())
    living_scene = self.get_state("input_select.living_scene")
    sleeping_scene = self.get_state("input_select.sleeping_scene")
    night_in_sleeping_ts = self.storage.read("night.night_in_sleeping_ts")
    day_in_living_ts = self.storage.read("night.day_in_living_ts")
    if (
      sleeping_scene == "night"
      and living_scene == "day"
      and self.is_all_lights_off()
      and (self.get_now_ts() - night_in_sleeping_ts) <= 1200
      and (self.get_now_ts() - day_in_living_ts) > 1200
    ):
      self.log("Turning night scene in living zone because no lights is turned on "
               "and night scene was turned on in sleeping zone")
      self.call_service("input_select/select_option", entity_id="input_select.living_scene", option="night")
    elif sleeping_scene == "day" and living_scene == "night":
      self.log("Turning day scene in living zone because day scene was turned on in sleeping zone")
      self.call_service("input_select/select_option", entity_id="input_select.living_scene", option="day")


  def is_all_lights_off(self):
    for room in LIVING_ZONE_ROOMS:
      if self.get_state(f"light.ha_template_room_{room}") == "on":
        return False
    return True
