from base import Base
import os


class DeleteSnapshot(Base):

  def initialize(self):
    super().initialize()
    self.listen_event(self.on_delete_snapshot, "custom_event", custom_event_data="delete_snapshot")


  def on_delete_snapshot(self, event_name, data, kwargs):
    os.remove("/config/www/snapshot.jpg")
