import appdaemon.plugins.hass.hassapi as hass


class GledoptoCct(hass.Hass):

  def initialize(self):
    lights = self.get_state("light")
    for light in lights:
      if "_cct" in light:
        for period in [1, 60, 120, 300]:
          self.run_in(self.turn_off_light, period, light=light)


  def turn_off_light(self, kwargs):
    light = kwargs["light"]
    self.call_service("light/turn_off", entity_id=light)
