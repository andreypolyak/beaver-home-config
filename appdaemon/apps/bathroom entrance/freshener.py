from base import Base


class Freshener(Base):

  def initialize(self):
    super().initialize()
    self.init_storage("freshener", "last_spray_ts", 0)
    self.toilet_motion = False
    self.listen_state(self.on_light_off, "light.ha_group_bathroom_entrance", new="off", old="on")
    self.listen_state(self.on_not_away, "input_select.living_scene", old="away")
    for binary_sensor in self.get_state("binary_sensor"):
      if "bathroom" in binary_sensor and binary_sensor.endswith("_motion"):
        self.listen_state(self.on_motion, binary_sensor, new="on", old="off")


  def on_light_off(self, entity, attribute, old, new, kwargs):
    if self.toilet_motion:
      self.spray()
    self.toilet_motion = False


  def on_not_away(self, entity, attribute, old, new, kwargs):
    self.log("Scene was changed from away, spray")
    self.spray()


  def on_motion(self, entity, attribute, old, new, kwargs):
    self.log("Motion occured, schedule spray")
    self.toilet_motion = True


  def spray(self):
    last_spray_ts = self.read_storage("last_spray_ts")
    if self.get_delta_ts(last_spray_ts) < 600:
      self.log("Spray cancelled because it occured recently")
      return
    self.log("Spray")
    self.turn_on_entity("switch.bathroom_freshener")
    self.write_storage("last_spray_ts", self.get_now_ts())
