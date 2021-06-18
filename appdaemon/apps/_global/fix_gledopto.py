import appdaemon.plugins.hass.hassapi as hass

ROOMS = {
  "bedroom": {
    "controller": "bedroom_bed_led",
    "sample_lights": ["group_bedroom_adult_top", "group_bedroom_theo_top", "bedroom_wardrobe"]
  },
  "living_room": {
    "controller": "living_room_sofa_led",
    "sample_lights": ["group_living_room_top", "group_living_room_speakers", "living_room_sofa"]
  }
}


class FixGledopto(hass.Hass):

  def initialize(self):
    # Hacks for Gledopto controller
    for room, data in ROOMS.items():
      controller = data["controller"]
      cct_light = f"light.{controller}_cct"
      rgb_light = f"light.{controller}_rgb"
      for period in [1, 60, 120, 300]:
        # Turn off CCT LED after restart
        self.run_in(self.turn_off_light, period, light=cct_light)
      # Sometimes Gledopto sets minimal brightness when 'transition': 2, 'hs_color': [30, 100] request is sent
      # To fix it I compare brightness of Gledopto controller with other light in the room
      self.listen_state(self.on_brightness_change, rgb_light, attribute="brightness", room=room)


  def turn_off_light(self, kwargs):
    light = kwargs["light"]
    self.call_service("light/turn_off", entity_id=light)


  def on_brightness_change(self, entity, attribute, old, new, kwargs):
    room = kwargs["room"]
    sample_lights = ROOMS[room]["sample_lights"]
    if self.get_state(entity) != "on":
      return None
    bri = self.get_state(entity, attribute="brightness")
    for sample_light in sample_lights:
      sample_entity = f"light.{sample_light}"
      if self.get_state(sample_entity) != "on":
        continue
      sample_bri = self.get_state(sample_entity, attribute="brightness")
      if abs(sample_bri - bri) > 10:
        self.log(f"Fixed {entity} brightness ({bri}->{sample_bri}) based on info from {sample_entity}")
        self.call_service("light/turn_on", entity_id=entity, brightness=sample_bri)
        return
