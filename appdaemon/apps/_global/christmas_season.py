import appdaemon.plugins.hass.hassapi as hass

LIGHTS = [
  "kitchen_christmas_star",
  "living_room_christmas_star",
  "living_room_christmas_tree"
]


class ChristmasSeason(hass.Hass):

  def initialize(self):
    self.listen_state(self.on_change, "input_boolean.christmas_season")
    self.listen_state(self.on_change, "input_select.living_scene")


  def on_change(self, entity, attribute, old, new, kwargs):
    christmas_season = self.get_state("input_boolean.christmas_season") == "on"
    scene = self.get_state("input_select.living_scene")
    if christmas_season and scene not in ["night", "light_cinema", "dark_cinema", "dumb"]:
      self.turn_on_all()
    else:
      self.turn_off_all()


  def turn_on_all(self):
    for light in LIGHTS:
      self.call_service("light/turn_on", entity_id=f"light.{light}")


  def turn_off_all(self):
    for light in LIGHTS:
      if self.entity_exists(f"light.{light}"):
        self.call_service("light/turn_off", entity_id=f"light.{light}")
