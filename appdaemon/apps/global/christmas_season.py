from base import Base

LIGHTS = [
  "kitchen_christmas_star",
  "living_room_christmas_star",
  "living_room_christmas_tree"
]


class ChristmasSeason(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_change, "input_boolean.christmas_season")
    self.listen_state(self.on_change, "input_select.living_scene")


  def on_change(self, entity, attribute, old, new, kwargs):
    christmas_season = self.is_entity_on("input_boolean.christmas_season")
    if christmas_season and self.get_living_scene() not in ["night", "light_cinema", "dark_cinema", "dumb"]:
      self.turn_on_all()
    else:
      self.turn_off_all()


  def turn_on_all(self):
    for light in LIGHTS:
      self.turn_on_entity(f"light.{light}")


  def turn_off_all(self):
    for light in LIGHTS:
      if self.entity_exists(f"light.{light}"):
        self.turn_off_entity(f"light.{light}")
