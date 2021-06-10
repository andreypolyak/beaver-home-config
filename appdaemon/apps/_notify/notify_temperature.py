import appdaemon.plugins.hass.hassapi as hass


class NotifyTemperature(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    sensors = self.get_state("sensor")
    for sensor in sensors:
      if sensor.endswith("_temperature") and "balcony" not in sensor:
        self.listen_state(self.on_change, sensor)


  def on_change(self, entity, attribute, old, new, kwargs):
    if new in ["unavailable", "unknown", "None"]:
      return
    if "freezer" in entity or "fridge" in entity:
      return
    new_value = float(new)
    if new_value < 19:
      room = entity.replace("sensor.", "").replace("_temperature", "").replace("_", " ")
      message = f"🥶 Too cold in the {room} ({new_value}°C)!"
      self.persons.send_notification("home_or_all", message, "air_quality", sound="Choo_Choo.caf",
                                     min_delta=600, url="/lovelace/settings_climate")
