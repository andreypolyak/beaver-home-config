from base import Base


class Fridge(Base):

  def initialize(self):
    super().initialize()
    self.init_storage("fridge", "notified_ts", 0)
    self.handle = None
    self.listen_state(self.on_door_open, "binary_sensor.kitchen_freezer_door", new="on", old="off")
    self.listen_state(self.on_door_close, "binary_sensor.kitchen_freezer_door", new="off", old="on")
    self.listen_state(self.on_fridge_temp_change, "sensor.kitchen_fridge_temperature")
    self.listen_state(self.on_freezer_temp_change, "sensor.kitchen_freezer_temperature")


  def on_fridge_temp_change(self, entity, attribute, old, new, kwargs):
    temp = self.get_float_state(new)
    if temp is None or temp < 15:
      return
    notified_ts = self.read_storage("notified_ts")
    if self.get_delta_ts(notified_ts) > 3600:
      text = "Внимание! Повышенная температура в холодильнике!"
      self.fire_event("yandex_speak_text", text=text, room="living_room", volume_level=1.0)
      self.send_push("home_or_all", f"♨️ Fridge temperature is {round(temp)}!", "fridge", is_critical=True)
      self.write_storage("notified_ts", self.get_now_ts())


  def on_freezer_temp_change(self, entity, attribute, old, new, kwargs):
    temp = self.get_float_state(new)
    if temp is None or temp < -5:
      return
    notified_ts = self.read_storage("notified_ts")
    if self.get_delta_ts(notified_ts) > 3600:
      text = "Внимание! Повышенная температура в морозильнике!"
      self.fire_event("yandex_speak_text", text=text, room="living_room", volume_level=1.0)
      message = f"♨️ Freezer temperature is {round(temp)}!"
      self.send_push("home_or_all", message, "fridge", is_critical=True)
      self.write_storage("notified_ts", self.get_now_ts())


  def on_door_open(self, entity, attribute, old, new, kwargs):
    self.cancel_handle(self.handle)
    self.handle = self.run_in(self.alert, 120)


  def on_door_close(self, entity, attribute, old, new, kwargs):
    self.cancel_handle(self.handle)


  def alert(self, kwargs):
    self.cancel_handle(self.handle)
    if self.entity_is_on("binary_sensor.kitchen_freezer_door"):
      text = "Внимание! Дверь морозилки не закрыта!"
      self.fire_event("yandex_speak_text", text=text, room="living_room", volume_level=1.0)
      self.send_push("home_or_all", "🧊 Freezer isn't closed!", "fridge", is_critical=True)
