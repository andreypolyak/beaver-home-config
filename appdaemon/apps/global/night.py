from base import Base

LIVING_ZONE_ROOMS = [
  "bathroom_entrance",
  "living_room",
  "kitchen"
]


class Night(Base):

  def initialize(self):
    super().initialize()
    self.init_storage("night", "night_in_sleeping_ts", 0)
    self.init_storage("night", "day_in_living_ts", 0)
    self.listen_state(self.on_change, "input_select.sleeping_scene")
    self.listen_state(self.on_change, "input_select.living_scene")
    for room in LIVING_ZONE_ROOMS:
      self.listen_state(self.on_change, f"light.ha_template_room_{room}")


  def on_change(self, entity, attribute, old, new, kwargs):
    if "sleeping_scene" in entity and new == "night":
      self.write_storage("night_in_sleeping_ts", self.get_now_ts())
    if "living_scene" in entity and new == "day" and old == "night":
      self.write_storage("day_in_living_ts", self.get_now_ts())
    night_in_sleeping_ts = self.read_storage("night_in_sleeping_ts")
    day_in_living_ts = self.read_storage("day_in_living_ts")
    if (
      self.sleeping_scene == "night"
      and self.living_scene == "day"
      and self.all_lights_off
      and self.get_delta_ts(night_in_sleeping_ts) <= 1200
      and self.get_delta_ts(day_in_living_ts) > 1200
    ):
      self.log("Turning night scene in living zone because no lights is turned on "
               "and night scene was turned on in sleeping zone")
      self.set_living_scene("night")
    elif (
      "sleeping_scene" in entity
      and new == "day"
      and self.living_scene == "night"
    ):
      self.log("Turning day scene in living zone because day scene was turned on in sleeping zone")
      self.set_living_scene("day")
    elif (
      "living_scene" in entity
      and new == "night"
      and self.sleeping_scene == "day"
    ):
      self.log("Turning night scene in sleeping zone because night scene was turned on in living zone")
      self.set_sleeping_scene("night")


  @property
  def all_lights_off(self):
    for room in LIVING_ZONE_ROOMS:
      if self.is_entity_on(f"light.ha_template_room_{room}"):
        return False
    return True
