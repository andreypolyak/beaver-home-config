import appdaemon.plugins.hass.hassapi as hass


class Plant(hass.Hass):

  def initialize(self):
    self.notifications = self.get_app("notifications")
    sensors = self.get_state("sensor")
    for sensor in sensors:
      if "_moisture" in sensor:
        self.listen_state(self.on_change, sensor)


  def on_change(self, entity, attribute, old, new, kwargs):
    try:
      moisture = int(float(new))
    except ValueError:
      return
    for zone in ["living", "sleeping"]:
      if self.get_state(f"input_select.{zone}_scene") == "night":
        return
    if moisture < 80:
      plant_name = entity.replace("sensor.", "").replace("_moisture", "").replace("_", " ")
      text = f"🪴 It's time to water the {plant_name}. Moisture there is {moisture}%"
      self.notifications.send("home_or_none", text, "plant", min_delta=21600)
