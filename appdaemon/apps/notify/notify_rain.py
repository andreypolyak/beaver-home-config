from base import Base


class NotifyRain(Base):

  def initialize(self):
    super().initialize()
    for sensor in self.get_state("sensor"):
      if not sensor.endswith("_yandex_rain"):
        continue
      self.listen_state(self.on_change, sensor)


  def on_change(self, entity, attribute, old, new, kwargs):
    person_name = entity.replace("sensor.", "").replace("_yandex_rain", "")
    if self.is_invalid(new) or self.get_state(f"input_text.{person_name}_rain") == new:
      return
    self.set_value(f"input_text.{person_name}_rain", new)
    if new == "В ближайшие 2 часа осадков не ожидается":
      return
    self.send_push(person_name, f"🌧️ {new}", "rain", min_delta=1800, url="/lovelace/outside")
