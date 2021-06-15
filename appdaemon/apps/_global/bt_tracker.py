import appdaemon.plugins.hass.hassapi as hass

ROOMS = ["entrance", "kitchen"]


class BtTracker(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    self.storage = self.get_app("persistent_storage")
    for room in ROOMS:
      self.storage.init(f"bt_tracker.{room}_restart_required_since_ts", None)
    self.run_every(self.process, "now", 300)


  def process(self, kwargs):
    restart_required = self.check_if_restart_required_now()
    self.restart_if_required_long_enough(restart_required)


  def check_if_restart_required_now(self):
    restart_required = {}
    for room in ROOMS:
      for person in self.persons.get_all_persons():
        person_phone = person["phone"]
        if not person_phone:
          continue
        bt_tracker = self.get_state(f"device_tracker.bt_{room}_{person_phone}_tracker")
        wifi_tracker = self.get_state(f"device_tracker.wifi_{room}_{person_phone}")
        ha_tracker = self.get_state(f"device_tracker.ha_{person_phone}")
        if (
          bt_tracker == "unavailable"
          or (bt_tracker != wifi_tracker and wifi_tracker == ha_tracker)
          or (bt_tracker != ha_tracker and wifi_tracker == ha_tracker)
        ):
          restart_required[room] = True
        elif room not in restart_required:
          restart_required[room] = False
    self.log(f"Room Assistant restart required for: {restart_required}")
    return restart_required


  def restart_if_required_long_enough(self, restart_required):
    for room in ROOMS:
      restart_required_since_ts = self.storage.read(f"bt_tracker.{room}_restart_required_since_ts")
      if restart_required[room]:
        if restart_required_since_ts is None:
          self.set_restart_required_since_ts(room, self.get_now_ts())
        elif (self.get_now_ts() - restart_required_since_ts) > 7200:
          self.persons.send_notification("admin", f"RESTART {room}", "test")
          self.call_service(f"shell_command/restart_room_assistant_{room}")
          self.set_restart_required_since_ts(room, None)
      else:
        self.set_restart_required_since_ts(room, None)


  def set_restart_required_since_ts(self, room, ts):
    self.storage.write(f"bt_tracker.{room}_restart_required_since_ts", ts)
