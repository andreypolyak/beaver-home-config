from base import Base


class NotifyForecast(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_day_scene, "input_select.living_scene", new="day", old="night")


  def on_day_scene(self, entity, attribute, old, new, kwargs):
    (text, emoji) = self.get_forecast()
    self.send_push("home_or_none", f"{emoji} {text}", "forecast", min_delta=28800, url="/lovelace/outside")
