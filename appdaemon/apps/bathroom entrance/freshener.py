from base import Base


class Freshener(Base):

  def initialize(self):
    super().initialize()
    self.init_storage("freshener", "last_spray_ts", 0)
    self.toilet_was_occupied = False
    self.listen_state(self.on_light_off, "light.ha_group_bathroom_entrance", new="off", old="on")
    self.listen_state(self.on_not_away, "input_select.living_scene", old="away")
    self.listen_state(self.on_occupation, "binary_sensor.bathroom_toilet_occupancy", new="off", old="on")


  def on_light_off(self, entity, attribute, old, new, kwargs):
    if self.toilet_was_occupied:
      self.spray()
    self.toilet_was_occupied = False


  def on_not_away(self, entity, attribute, old, new, kwargs):
    self.log("Scene was changed from away, spray")
    self.spray()


  def on_occupation(self, entity, attribute, old, new, kwargs):
    self.log("Toilet was occupied, schedule spray")
    self.toilet_was_occupied = True


  def spray(self):
    last_spray_ts = self.read_storage("last_spray_ts")
    if self.get_delta_ts(last_spray_ts) < 600:
      self.log("Spray cancelled because it occured recently")
      return
    self.log("Spray")
    self.turn_on_entity("switch.bathroom_freshener")
    self.write_storage("last_spray_ts", self.get_now_ts())
