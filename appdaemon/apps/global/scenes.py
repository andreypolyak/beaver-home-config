from base import Base


class Scenes(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_scene_change, "input_select.living_scene", zone="living")
    self.listen_state(self.on_scene_change, "input_select.sleeping_scene", zone="sleeping")
    input_booleans = self.get_state("input_boolean")
    for input_boolean in input_booleans:
      if "input_boolean.scene_living_" in input_boolean or "input_boolean.scene_sleeping_" in input_boolean:
        self.listen_state(self.on_boolean_change, input_boolean, new="on")


  def on_scene_change(self, entity, attribute, old, new, kwargs):
    zone = kwargs["zone"]
    self.turn_on_entity(f"input_boolean.scene_{zone}_{new}")
    self.turn_off_entity(f"input_boolean.scene_{zone}_{old}")


  def on_boolean_change(self, entity, attribute, old, new, kwargs):
    zones = ["living", "sleeping"]
    for zone in zones:
      scene = entity.replace(f"input_boolean.scene_{zone}_", "")
      if zone in entity and self.get_scene(zone) != scene:
        self.log(f"Setting {scene} scene in {zone} zone because boolean was turned on")
        self.set_scene(zone, scene)
