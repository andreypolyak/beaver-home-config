from base import Base


class NotifyAirQuality(Base):

  def initialize(self):
    super().initialize()
    for sensor in self.get_state("sensor"):
      if "_co2" in sensor:
        self.listen_state(self.on_change, sensor)


  def on_change(self, entity, attribute, old, new, kwargs):
    ppm = self.get_int_state(new)
    if ppm is None or ppm < 1000:
      return
    room = entity.replace("sensor.", "").replace("_co2", "").replace("_", " ")
    message = f"🙊 Too much CO2 in the {room} ({ppm}). Please open windows."
    url = "/lovelace/settings_climate"
    self.send_push("home_or_none", message, "air_quality", sound="Choo_Choo.caf", min_delta=600, url=url)
