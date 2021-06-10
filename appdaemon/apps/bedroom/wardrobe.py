import appdaemon.plugins.hass.hassapi as hass


class Wardrobe(hass.Hass):

  def initialize(self):
    self.handle = None
    self.listen_state(self.on_wardrobe_change, "binary_sensor.bedroom_wardrobe_door")


  def on_wardrobe_change(self, entity, attribute, old, new, kwargs):
    if new in ["unavailable", "unknown", "None"] or old in ["unavailable", "unknown", "None"]:
      return
    if self.timer_running(self.handle):
      self.cancel_timer(self.handle)
    self.handle = self.run_in(self.change_wardrobe, 1)


  def change_wardrobe(self, kwargs):
    if self.timer_running(self.handle):
      self.cancel_timer(self.handle)
    is_door_open = self.get_state("binary_sensor.bedroom_wardrobe_door") == "on"
    if is_door_open and self.get_state("light.bedroom_wardrobe") == "off":
      self.turn_on_wardrobe()
    elif not is_door_open and self.get_state("light.group_bedroom_top") == "off":
      self.turn_off_wardrobe()


  def turn_on_wardrobe(self):
    self.log("Turning on wardrobe light")
    self.call_service("light/turn_on", entity_id="light.bedroom_wardrobe", brightness=2,
                      transition=self.get_transition())


  def turn_off_wardrobe(self):
    self.log("Turning off wardrobe light")
    self.call_service("light/turn_off", entity_id="light.bedroom_wardrobe", transition=self.get_transition())


  def get_transition(self):
    return float(self.get_state("input_number.transition"))
