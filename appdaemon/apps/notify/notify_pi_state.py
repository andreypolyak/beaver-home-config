from base import Base

ROOMS = ["entrance", "living_room", "bedroom"]


class NotifyPiState(Base):

  def initialize(self):
    super().initialize()
    for room in ROOMS:
      self.init_storage("notify_pi_state", f"{room}_notified", True)
    self.restart_ts = self.get_now_ts()
    for room in ROOMS:
      self.listen_state(self.on_pi_change, f"sensor.rpi_temp_rpi_{room}")


  def on_pi_change(self, entity, attribute, old, new, kwargs):
    if new == "unknown":
      return
    room = self.get_room_from_entity(entity)
    room_name = room.replace("_", " ").capitalize()
    notified = self.read_storage(f"{room}_notified")
    if new == "unavailable" and notified:
      message = f"🍓 {room_name} Raspberry Pi is offline"
      self.send_push("admin", message, "pi_state", sound="Alert.caf", url="/lovelace/settings")
      self.write_storage(f"{room}_notified", False)
    elif old == "unavailable" and new != "unknown" and not notified:
      message = f"🍓 {room_name} Raspberry Pi is online"
      self.send_push("admin", message, "pi_state", sound="Alert.caf", url="/lovelace/settings")
      self.write_storage(f"{room}_notified", True)


  def get_room_from_entity(self, entity):
    for room in ROOMS:
      if room in entity:
        return room
    return None
