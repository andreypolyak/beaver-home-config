from base import Base

ROOMS = {
  "living_room": {
    "controller": "living_room_sofa_led",
    "sample_lights": ["group_living_room_top", "group_living_room_speakers", "living_room_sofa"]
  }
}


class FixGledopto(Base):

  def initialize(self):
    super().initialize()
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
    self.turn_off_entity(kwargs["light"])


  def on_brightness_change(self, entity, attribute, old, new, kwargs):
    room = kwargs["room"]
    sample_lights = ROOMS[room]["sample_lights"]
    bri = self.get_brightness(entity)
    if bri is None:
      return
    for sample_light in sample_lights:
      sample_bri = self.get_brightness(f"light.{sample_light}")
      if sample_bri is None:
        continue
      if abs(sample_bri - bri) > 10:
        self.log(f"Fixed {entity} brightness ({bri}->{sample_bri}) based on info from {sample_light}")
        self.turn_on_entity(entity, brightness=sample_bri)
        return


  def get_brightness(self, entity):
    bri = self.get_state(entity, attribute="brightness")
    if self.is_entity_off(entity) or bri is None:
      return None
    return bri
