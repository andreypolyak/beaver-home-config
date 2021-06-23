import appdaemon.plugins.hass.hassapi as hass


class NotifyAirQuality(hass.Hass):

  def initialize(self):
    self.notifications = self.get_app("notifications")
    self.listen_state(self.on_change, "sensor.bedroom_co2")
    self.listen_state(self.on_change, "sensor.living_room_co2")


  def on_change(self, entity, attribute, old, new, kwargs):
    try:
      new_value = int(float(new))
    except (TypeError, ValueError):
      return
    if new_value > 1000:
      room = entity.replace("sensor.", "").replace("_co2", "").replace("_", " ")
      message = f"🙊 Too much CO2 in the {room} ({new_value}). Please open windows."
      self.notifications.send("home_or_none", message, "air_quality", sound="Choo_Choo.caf",
                              min_delta=600, url="/lovelace/settings_climate")
