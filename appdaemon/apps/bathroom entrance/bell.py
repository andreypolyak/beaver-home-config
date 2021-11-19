from base import Base


class Bell(Base):

  def initialize(self):
    super().initialize()
    self.step = 0
    self.step_update_ts = 0
    self.last_ringed_ts = 0
    self.listen_state(self.on_bell_ring, "sensor.entrance_door_bell")


  def on_bell_ring(self, entity, attribute, old, new, kwargs):
    if self.get_delta_ts(self.step_update_ts) > 10:
      self.step = 0
    if new == "double" and self.step == 0 and len(self.get_person_names(location="downstairs")) > 0:
      self.log("Unlocking the door by being downstairs")
      self.fire_event("bell_unlock")
      self.call_service("lock/unlock", entity_id="lock.entrance_lock")
      return
    if new not in ["single", "double", "hold"]:
      return
    if not self.check_code(new) and self.get_delta_ts(self.last_ringed_ts) > 15:
      self.ring_bell()


  def check_code(self, new):
    code = str(self.args["code"])
    button_code = "1"
    if new == "double":
      button_code = "2"
    elif new == "hold":
      button_code = "0"
    if self.step > len(code) - 1 or code[self.step] != button_code:
      self.log(f"Incorrect code ({button_code}). Step {self.step}")
      self.step_update_ts = 0
      self.step = 0
      return False
    self.log(f"Correct code. Step {self.step}")
    if self.step == len(code) - 1:
      self.log("Unlocking the door by code")
      self.fire_event("bell_unlock")
      self.call_service("lock/unlock", entity_id="lock.entrance_lock")
      self.step = -1
    self.step += 1
    self.step_update_ts = self.get_now_ts()
    return True


  def ring_bell(self):
    self.call_service("rest_command/camera_snapshot")
    self.last_ringed_ts = self.get_now_ts()
    living_scene = self.living_scene
    # Pause TV
    if self.get_state("media_player.living_room_apple_tv") == "playing" and living_scene != "party":
      self.media_pause("living_room_apple_tv")
    # Bell sound
    if living_scene != "night":
      self.play_sound("living_room")
      if self.entity_is_off("binary_sensor.bathroom_door"):
        self.play_sound("bathroom")
    # Push notifications
    image = "/api/camera_proxy/camera.entrance_door_camera"
    url = "/lovelace/bathroom_entrance"
    actions = [
      {"action": "LOCK_UNLOCK", "title": "🔓 Unlock the door", "destructive": True},
      {"action": "URI", "title": "👀 Watch the latest motion", "destructive": True, "uri": "/media-browser/motioneye"}
    ]
    self.send_push("home_or_all", "🔔 Ding-Dong", "bell", sound="Anticipate.caf", image=image, url=url, actions=actions)
    # Lights
    entity = "light.entrance_cloakroom"
    if living_scene in ["day", "light_cinema"]:
      self.turn_on_entity(entity, flash="short", brightness=254, color_name="red")
      self.run_in(self.restore_light, 1)
    elif living_scene in ["dark_cinema", "party"]:
      self.turn_on_entity(entity, flash="short", brightness=1, color_name="red")
      self.run_in(self.restore_light, 1)


  def play_sound(self, room):
    entity = f"media_player.{room}_sonos"
    url = self.args["bell_sound_url"]
    self.sonos_snapshot(entity)
    self.volume_set(entity, 0.15)
    self.play_media(entity, url, "music")
    self.run_in(self.restore_sonos, 2, room=room)


  def restore_sonos(self, kwargs):
    room = kwargs["room"]
    self.sonos_restore(f"media_player.{room}_sonos")


  def restore_light(self, kwargs):
    self.fire_event("bathroom_entrance_virtual_switch_room_on")
