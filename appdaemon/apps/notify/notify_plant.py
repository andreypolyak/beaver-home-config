from base import Base


class NotifyPlant(Base):

  def initialize(self):
    super().initialize()
    sensors = self.get_state("sensor")
    for sensor in sensors:
      if "_moisture" in sensor:
        self.listen_state(self.on_change, sensor, immediate=True)


  def on_change(self, entity, attribute, old, new, kwargs):
    moisture = self.get_int_state(new)
    if moisture is None:
      return
    for zone in ["living", "sleeping"]:
      if self.get_scene(zone) == "night":
        return
    if moisture < 80:
      plant_name = self.convert_entity_to_name(entity.replace("_moisture", ""), lower=True)
      message = f"🪴 It's time to water the {plant_name}. Moisture there is {moisture}%"
      self.send_push("home_or_none", message, "plant", min_delta=21600)
