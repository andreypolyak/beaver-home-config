import appdaemon.plugins.hass.hassapi as hass
import os


class DeleteSnapshot(hass.Hass):

  def initialize(self):
    self.listen_event(self.on_delete_snapshot, "custom_event", custom_event_data="delete_snapshot")


  def on_delete_snapshot(self, event_name, data, kwargs):
    os.remove("/config/www/snapshot.jpg")
