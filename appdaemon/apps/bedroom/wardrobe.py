from base import Base


class Wardrobe(Base):

  def initialize(self):
    super().initialize()
    self.handle = None
    self.listen_state(self.on_wardrobe_change, "binary_sensor.bedroom_wardrobe_door")


  def on_wardrobe_change(self, entity, attribute, old, new, kwargs):
    if self.is_invalid(new) or self.is_invalid(old):
      return
    self.cancel_handle(self.handle)
    self.handle = self.run_in(self.change_wardrobe, 1)


  def change_wardrobe(self, kwargs):
    self.cancel_handle(self.handle)
    door_open = self.entity_is_on("binary_sensor.bedroom_wardrobe_door")
    if door_open and self.entity_is_off("light.bedroom_wardrobe"):
      self.turn_on_entity("light.ha_template_individual_bedroom_wardrobe")
    elif not door_open and self.entity_is_off("light.group_bedroom_top"):
      self.turn_off_entity("light.ha_template_individual_bedroom_wardrobe")
