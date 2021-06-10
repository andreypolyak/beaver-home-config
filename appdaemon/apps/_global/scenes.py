import appdaemon.plugins.hass.hassapi as hass


class Scenes(hass.Hass):

  def initialize(self):
    self.listen_state(self.on_scene_change, "input_select.living_scene", zone="living")
    self.listen_state(self.on_scene_change, "input_select.sleeping_scene", zone="sleeping")
    input_booleans = self.get_state("input_boolean")
    for input_boolean in input_booleans:
      if "input_boolean.scene_living_" in input_boolean or "input_boolean.scene_sleeping_" in input_boolean:
        self.listen_state(self.on_boolean_change, input_boolean)


  def on_scene_change(self, entity, attribute, old, new, kwargs):
    zone = kwargs["zone"]
    input_boolean = f"input_boolean.scene_{zone}_{new}"
    if self.entity_exists(input_boolean) and self.get_state(input_boolean) == "off":
      self.call_service("input_boolean/turn_on", entity_id=input_boolean)
    input_boolean = f"input_boolean.scene_{zone}_{old}"
    if self.entity_exists(input_boolean) and self.get_state(input_boolean) == "on":
      self.call_service("input_boolean/turn_off", entity_id=input_boolean)


  def on_boolean_change(self, entity, attribute, old, new, kwargs):
    zones = ["living", "sleeping"]
    for zone in zones:
      scene = entity.replace(f"input_boolean.scene_{zone}_", "")
      current_scene = self.get_state(f"input_select.{zone}_scene")
      if f"input_boolean.scene_{zone}_" in entity and new == "on" and current_scene != scene:
        self.log(f"Setting {scene} scene in {zone} zone because boolean was turned on")
        self.call_service("input_select/select_option", entity_id=f"input_select.{zone}_scene", option=scene)
