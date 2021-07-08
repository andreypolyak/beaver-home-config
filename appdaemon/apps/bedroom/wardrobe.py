from base import Base


class Wardrobe(Base):

  def initialize(self):
    super().initialize()
    self.handle = None
    self.listen_state(self.on_wardrobe_change, "binary_sensor.bedroom_wardrobe_door")


  def on_wardrobe_change(self, entity, attribute, old, new, kwargs):
    if self.is_bad(new) or self.is_bad(old):
      return
    self.cancel_handle(self.handle)
    self.handle = self.run_in(self.change_wardrobe, 1)


  def change_wardrobe(self, kwargs):
    self.cancel_handle(self.handle)
    is_door_open = self.is_entity_on("binary_sensor.bedroom_wardrobe_door")
    if is_door_open and self.is_entity_off("light.bedroom_wardrobe"):
      self.turn_on_wardrobe()
    elif not is_door_open and self.is_entity_off("light.group_bedroom_top"):
      self.turn_off_wardrobe()


  def turn_on_wardrobe(self):
    self.log("Turning on wardrobe light")
    entity = "light.bedroom_wardrobe"
    transition = self.get_float_state("input_number.transition")
    self.turn_on_entity(entity, brightness=2, transition=transition)


  def turn_off_wardrobe(self):
    self.log("Turning off wardrobe light")
    entity = "light.bedroom_wardrobe"
    transition = self.get_float_state("input_number.transition")
    self.turn_off_entity(entity, transition=transition)
