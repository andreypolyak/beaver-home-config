from base import Base
import os


class Camera(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_away, "input_select.living_scene", new="away")
    self.listen_state(self.on_not_away, "input_select.living_scene", old="away")
    self.listen_event(self.on_delete_snapshot, "delete_snapshot")


  def on_away(self, entity, attribute, old, new, kwargs):
    self.call_service("reolink_dev/ptz_control", entity_id="camera.living_room_camera", command="TOPOS", preset=2)


  def on_not_away(self, entity, attribute, old, new, kwargs):
    self.call_service("reolink_dev/ptz_control", entity_id="camera.living_room_camera", command="TOPOS", preset=1)


  def on_delete_snapshot(self, event_name, data, kwargs):
    os.remove("/config/www/snapshot.jpg")
