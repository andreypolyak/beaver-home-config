import appdaemon.plugins.hass.hassapi as hass


class LightDelay(hass.Hass):

  def initialize(self):
    self.listen_state(self.on_scene_change, "input_select.living_scene", immediate=True)
    self.listen_state(self.on_scene_change, "input_select.sleeping_scene")


  def on_scene_change(self, entity, attribute, old, new, kwargs):
    living_scene = self.get_state("input_select.living_scene")
    sleeping_scene = self.get_state("input_select.sleeping_scene")
    if living_scene in ["dark_cinema", "party", "night"]:
      self.call_service("input_boolean/turn_on", entity_id="input_boolean.living_zone_min_delay")
      self.call_service("input_boolean/turn_on", entity_id="input_boolean.sleeping_zone_min_delay")
    else:
      self.call_service("input_boolean/turn_off", entity_id="input_boolean.living_zone_min_delay")
      if sleeping_scene == "night":
        self.call_service("input_boolean/turn_on", entity_id="input_boolean.sleeping_zone_min_delay")
      else:
        self.call_service("input_boolean/turn_off", entity_id="input_boolean.sleeping_zone_min_delay")
