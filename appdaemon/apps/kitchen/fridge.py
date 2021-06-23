import appdaemon.plugins.hass.hassapi as hass


class Fridge(hass.Hass):

  def initialize(self):
    self.notifications = self.get_app("notifications")
    self.storage = self.get_app("persistent_storage")
    self.storage.init("fridge.notified_ts", 0)
    self.handle = None
    self.listen_state(self.on_door_open, "binary_sensor.kitchen_freezer_door", new="on", old="off")
    self.listen_state(self.on_door_close, "binary_sensor.kitchen_freezer_door", new="off", old="on")
    self.listen_state(self.on_fridge_temp_change, "sensor.kitchen_fridge_temperature")
    self.listen_state(self.on_freezer_temp_change, "sensor.kitchen_freezer_temperature")


  def on_fridge_temp_change(self, entity, attribute, old, new, kwargs):
    try:
      temp = round(float(new))
      if temp >= 15:
        notified_ts = self.storage.read("fridge.notified_ts")
        if (self.get_now_ts() - notified_ts) > 3600:
          text = "Внимание! Повышенная температура в холодильнике!"
          self.fire_event("yandex_speak_text", text=text, room="living_room", volume_level=1.0)
          self.notifications.send("home_or_all", f"♨️ Fridge temperature is {temp}!", "fridge", is_critical=True)
          self.storage.write("fridge.notified_ts", self.get_now_ts())
    except ValueError:
      pass


  def on_freezer_temp_change(self, entity, attribute, old, new, kwargs):
    try:
      temp = round(float(new))
      if temp >= -5:
        notified_ts = self.storage.read("fridge.notified_ts")
        if (self.get_now_ts() - notified_ts) > 3600:
          text = "Внимание! Повышенная температура в морозильнике!"
          self.fire_event("yandex_speak_text", text=text, room="living_room", volume_level=1.0)
          text = f"♨️ Freezer temperature is {temp}!"
          self.notifications.send("home_or_all", text, "fridge", is_critical=True)
          self.storage.write("fridge.notified_ts", self.get_now_ts())
    except ValueError:
      pass


  def on_door_open(self, entity, attribute, old, new, kwargs):
    self.cancel_handle()
    self.handle = self.run_in(self.alert, 120)


  def on_door_close(self, entity, attribute, old, new, kwargs):
    self.cancel_handle()


  def alert(self, kwargs):
    self.cancel_handle()
    if self.get_state("binary_sensor.kitchen_freezer_door") == "on":
      text = "Внимание! Дверь морозилки не закрыта!"
      self.fire_event("yandex_speak_text", text=text, room="living_room", volume_level=1.0)
      self.notifications.send("home_or_all", "🧊 Freezer isn't closed!", "fridge", is_critical=True)


  def cancel_handle(self):
    if self.timer_running(self.handle):
      self.cancel_timer(self.handle)
