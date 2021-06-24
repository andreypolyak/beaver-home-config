import appdaemon.plugins.hass.hassapi as hass


class ElectricityStats(hass.Hass):

  def initialize(self):
    self.run_daily(self.send_stats, "08:00:00")
    self.run_daily(self.send_stats, "09:00:00")
    self.run_daily(self.send_stats, "10:00:00")


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
      try:
        indication = int(float(self.get_state(f"sensor.saures_electricity_t{tariff}")))
        indications.append(indication)
      except:
        return
    self.call_service("lkcomu_interrao/push_indications", indications=indications, notification=True,
                      entity_id=meter_entity)
