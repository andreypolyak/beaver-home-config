from base import Base

TIMES = ["08:00:00", "09:00:00", "10:00:00"]


class ElectricityStats(Base):

  def initialize(self):
    super().initialize()
    for time in TIMES:
      self.run_daily(self.send_stats, time)


  def send_stats(self, kwargs):
    meter_entity = "sensor.mosenergosbyt_meter"
    if self.date().day < 16 or self.date().day > 21:
      return
    indications = []
    meter_attributes = self.get_state(meter_entity, attribute="all")["attributes"]
    for tariff in range(1, 4):
      attribute = f"zone_t{tariff}_period_indication"
      if attribute not in meter_attributes or attribute is not None:
        return
      indication = self.get_int_state(f"sensor.saures_electricity_t{tariff}")
      if indication is None:
        return
      indications.append(indication)
    service = "lkcomu_interrao/push_indications"
    self.call_service(service, indications=indications, notification=True, entity_id=meter_entity)
