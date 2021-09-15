from base import Base


class Camera(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_bell_ring, "sensor.entrance_door_bell", new="single")
    self.listen_state(self.on_match, "image_processing.entrance_door_camera", attribute="matched_faces")


  def on_match(self, entity, attribute, old, new, kwargs):
    if "Andrey" in new:
      text = new["Andrey"]
      self.fire_event("telegram_log", text=str(text))


  def on_bell_ring(self, entity, attribute, old, new, kwargs):
    self.call_service("rest_command/camera_snapshot")
    # dt = self.datetime().strftime("%Y-%m-%d %H:%M:%S")
    # filename = f"/config/www/bell_photos/{dt}.jpg"
    # self.call_service("camera/snapshot", entity_id="camera.entrance_door_camera", filename=filename)
    self.call_service("image_processing/scan", entity_id="image_processing.entrance_door_camera")
