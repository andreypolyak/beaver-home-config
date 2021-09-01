from base import Base


class NotifyTemperature(Base):

  def initialize(self):
    super().initialize()
    for sensor in self.get_state("sensor"):
      if sensor.endswith("_temperature") and "balcony" not in sensor:
        self.listen_state(self.on_change, sensor)


  def on_change(self, entity, attribute, old, new, kwargs):
    if self.is_invalid(new):
      return
    if "freezer" in entity or "fridge" in entity:
      return
    temperature = self.get_float_state(new)
    if temperature is None or temperature > 19:
      return
    room = entity.replace("sensor.", "").replace("_temperature", "").replace("_", " ")
    message = f"🥶 Too cold in the {room} ({temperature}°C)!"
    url = "/lovelace/settings_climate"
    self.send_push("home_or_all", message, "temperature", sound="Choo_Choo.caf", min_delta=600, url=url)
