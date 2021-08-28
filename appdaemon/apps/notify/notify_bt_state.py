from base import Base

ROOMS = ["kitchen", "entrance"]


class NotifyBtState(Base):

  def initialize(self):
    super().initialize()
    for room in ROOMS:
      self.listen_state(self.on_change, f"sensor.bt_{room}_discrepancy_3_hours", room=room)
      action = f"PI_{room.upper()}_RESTART"
      self.listen_event(self.on_pi_restart, event="mobile_app_notification_action", action=action, room=room)


  def on_change(self, entity, attribute, old, new, kwargs):
    if self.get_float_state(new) < 3:
      return
    room = kwargs["room"]
    actions = [{"action": f"PI_{room.upper()}_RESTART", "title": f"📌 Restart {room} Pi", "destructive": True}]
    message = f"👎 Bluetooth is unresponsible on {room} Pi. Do you want to restart it?"
    url = "/lovelace/settings_trackers"
    self.send_push("admin", message, "bt_state", sound="Ladder.caf", min_delta=86400, actions=actions, url=url)


  def on_pi_restart(self, event_name, data, kwargs):
    room = kwargs["room"]
    self.call_service(f"shell_command/restart_rpi_{room}")
