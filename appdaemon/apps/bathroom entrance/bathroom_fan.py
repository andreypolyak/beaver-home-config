from base import Base


class BathroomFan(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_bathroom_door, "binary_sensor.bathroom_door", immediate=True)


  def on_bathroom_door(self, entity, attribute, old, new, kwargs):
    if new == "off":
      self.turn_on_entity("switch.bathroom_fan")
    else:
      self.turn_off_entity("switch.bathroom_fan")
