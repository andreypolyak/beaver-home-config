import appdaemon.plugins.hass.hassapi as hass

ROOMS = ["entrance", "living_room", "bedroom"]


class NotifyPiState(hass.Hass):

  def initialize(self):
    self.notifications = self.get_app("notifications")
    self.storage = self.get_app("persistent_storage")
    for room in ROOMS:
      self.storage.init(f"notify_pi_state.{room}_notified", True)
    self.restart_ts = self.get_now_ts()
    for room in ROOMS:
      self.listen_state(self.on_pi_change, f"sensor.rpi_temp_rpi_{room}")


  def on_pi_change(self, entity, attribute, old, new, kwargs):
    if new == "unknown":
      return
    room = self.get_room_from_entity(entity)
    room_name = room.replace("_", " ").capitalize()
    is_notified = self.storage.read(f"notify_pi_state.{room}_notified")
    if new == "unavailable" and is_notified:
      self.notifications.send("admin", f"🍓 {room_name} Raspberry Pi is offline", "pi", url="/lovelace/settings")
      self.storage.write(f"notify_pi_state.{room}_notified", False)
    elif old == "unavailable" and new != "unknown" and not is_notified:
      self.notifications.send("admin", f"🍓 {room_name} Raspberry Pi is online", "pi", url="/lovelace/settings")
      self.storage.write(f"notify_pi_state.{room}_notified", True)


  def get_room_from_entity(self, entity):
    for room in ROOMS:
      if room in entity:
        return room
    return None
