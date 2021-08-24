from base import Base


class Freshener(Base):

  def initialize(self):
    super().initialize()
    self.init_storage("freshener", "last_spray_ts", 0)
    self.init_storage("freshener", "last_flush_ts", 0)
    self.handle = None
    self.listen_state(self.on_door_open, "binary_sensor.bathroom_door", new="on", old="off")
    self.listen_state(self.on_door_close, "binary_sensor.bathroom_door", new="off", old="on")
    self.listen_state(self.on_not_away, "input_select.living_scene", old="away")
    for binary_sensor in self.get_state("binary_sensor"):
      if "bathroom" in binary_sensor and binary_sensor.endswith("_motion"):
        self.listen_state(self.on_motion, binary_sensor, new="on", old="off")
    self.listen_state(self.on_flush, "sensor.bathroom_toilet_vibration")


  def on_not_away(self, entity, attribute, old, new, kwargs):
    self.log("Scene was changed from away, spray")
    self.spray({})


  def on_flush(self, entity, attribute, old, new, kwargs):
    if self.is_bad(new):
      return
    last_flush_ts = self.read_storage("last_flush_ts")
    flush_delta = self.get_delta_ts(last_flush_ts)
    self.write_storage("last_flush_ts", self.get_now_ts())
    if flush_delta < 120:
      self.log("Toilet flush, schedule spray")
      self.schedule_spray()
    else:
      self.log("Toilet flush, schedule spray with delay")
      self.schedule_spray(delay=300)


  def on_door_open(self, entity, attribute, old, new, kwargs):
    self.log("Bathroom door open, schedule spray")
    self.schedule_spray()


  def on_door_close(self, entity, attribute, old, new, kwargs):
    self.log("Bathroom door closed, cancel spray")
    self.cancel_handle(self.handle)


  def on_motion(self, entity, attribute, old, new, kwargs):
    if self.timer_running(self.handle):
      self.log("Motion occured, schedule spray")
      self.schedule_spray()


  def schedule_spray(self, delay=30):
    self.cancel_handle(self.handle)
    self.handle = self.run_in(self.spray, delay)


  def spray(self, kwargs):
    last_spray_ts = self.read_storage("last_spray_ts")
    if self.get_delta_ts(last_spray_ts) < 600:
      self.log("Spray cancelled because it occured recently")
      return
    if self.is_entity_on("binary_sensor.bathroom_door"):
      self.log("Spray")
      self.turn_on_entity("switch.bathroom_freshener")
      self.write_storage("last_spray_ts", self.get_now_ts())
    else:
      self.log("Door is open, schedule spray")
      self.schedule_spray()
