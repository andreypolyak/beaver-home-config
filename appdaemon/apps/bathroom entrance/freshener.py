import appdaemon.plugins.hass.hassapi as hass


class Freshener(hass.Hass):

  def initialize(self):
    self.storage = self.get_app("persistent_storage")
    self.storage.init("freshener.last_spray_ts", 0)
    self.handle = None
    self.listen_state(self.on_door_open, "binary_sensor.bathroom_door", new="on", old="off")
    self.listen_state(self.on_door_close, "binary_sensor.bathroom_door", new="off", old="on")
    self.listen_state(self.on_arrive, "input_select.living_scene", old="away")
    for binary_sensor in self.get_state("binary_sensor"):
      if "bathroom" in binary_sensor and binary_sensor.endswith("_motion"):
        self.listen_state(self.on_motion, binary_sensor, new="on", old="off")
    self.listen_state(self.on_flush, "sensor.bathroom_toilet_vibration")


  def on_arrive(self, entity, attribute, old, new, kwargs):
    self.spray({})


  def on_flush(self, entity, attribute, old, new, kwargs):
    if new in ["unavailable", "unknown", "None", ""]:
      return
    self.cancel_and_set_handle()


  def on_door_open(self, entity, attribute, old, new, kwargs):
    self.cancel_and_set_handle()


  def on_door_close(self, entity, attribute, old, new, kwargs):
    self.cancel_handle()


  def on_motion(self, entity, attribute, old, new, kwargs):
    self.cancel_and_set_handle()


  def spray(self, kwargs):
    last_spray_ts = self.storage.read("freshener.last_spray_ts")
    if (self.get_now_ts() - last_spray_ts) > 600:
      self.call_service("switch/turn_on", entity_id="switch.bathroom_freshener")
      self.storage.write("freshener.last_spray_ts", self.get_now_ts())


  def cancel_handle(self):
    if self.timer_running(self.handle):
      self.cancel_timer(self.handle)


  def cancel_and_set_handle(self):
    if self.timer_running(self.handle):
      self.cancel_timer(self.handle)
      self.handle = self.run_in(self.spray, 15)
