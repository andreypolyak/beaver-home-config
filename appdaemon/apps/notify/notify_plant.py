from base import Base


class NotifyPlant(Base):

  def initialize(self):
    super().initialize()
    for sensor in self.get_state("sensor"):
      if "_moisture" in sensor:
        self.listen_state(self.on_change, sensor, immediate=True)


  def on_change(self, entity, attribute, old, new, kwargs):
    moisture = self.get_int_state(new)
    if moisture is None:
      return
    for zone in ["living", "sleeping"]:
      if self.get_scene(zone) == "night":
        return
    plant_name = entity.replace("sensor.", "")
    threshold = self.get_int_state(f"input_number.{plant_name}_threshold")
    if moisture < threshold:
      plant_name = entity.replace("sensor.", "").replace("_moisture", "").replace("_", " ").title()
      message = f"🪴 It's time to water the {plant_name}. Moisture there is {moisture}%"
      self.send_push("home_or_none", message, "plant", min_delta=21600)
