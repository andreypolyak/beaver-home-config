from base import Base
from datetime import datetime

TIMES = ["08:00:00", "09:00:00", "10:00:00"]


class ElectricityStats(Base):

  def initialize(self):
    super().initialize()
    for time in TIMES:
      self.run_daily(self.send_stats, time)
    self.listen_event(self.on_push_indications, "lkcomu_interrao_push_indications")


  def on_push_indications(self, event_name, data, kwargs):
    success = data["success"]
    if success:
      text = "🔌 Successfully sent electricity stats to Mosenergosbyt"
    else:
      text = "🔌 Error occured while sending electricity stats to Mosenergosbyt"
    self.send_push("admin", text, "electricity_stats")


  def send_stats(self, kwargs):
    meter_entity = "sensor.mosenergosbyt_meter"
    if self.date().day < 16 or self.date().day > 21:
      return
    indications = []
    last_indications_date = self.get_state(meter_entity, attribute="last_indications_date")
    try:
      last_indications_month = datetime.strptime(last_indications_date, "%Y-%m-%d").strftime("%m")
    except:
      return
    current_month = self.get_now().strftime("%m")
    if last_indications_month == current_month:
      return
    for tariff in range(1, 4):
      indication = self.get_int_state(f"sensor.saures_electricity_t{tariff}")
      if indication is None:
        return
      indications.append(indication)
    kwargs = {
      "indications": indications,
      "entity_id": meter_entity
    }
    self.call_service("lkcomu_interrao/push_indications", **kwargs)
