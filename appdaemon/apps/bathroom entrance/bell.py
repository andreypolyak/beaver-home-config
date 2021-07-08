from base import Base


class Bell(Base):

  def initialize(self):
    super().initialize()
    self.step = 0
    self.step_update_ts = 0
    self.last_ringed_ts = 0
    self.listen_state(self.on_bell_ring, "sensor.entrance_door_bell")


  def on_bell_ring(self, entity, attribute, old, new, kwargs):
    current_ts = self.get_now_ts()
    if self.get_delta_ts(self.step_update_ts) > 10:
      self.step = 0
    if new == "double" and self.step == 0:
      if self.persons.get_all_person_names_with_location("downstairs"):
        self.log("Unlocking the door by being downstairs")
        self.call_service("lock/unlock", entity_id="lock.entrance_lock")
      else:
        self.step = 1
        self.step_update_ts = current_ts
    elif new == "hold" and self.step == 1:
      self.step = 2
      self.step_update_ts = current_ts
    elif new == "single" and self.step == 2:
      self.step = 3
      self.step_update_ts = current_ts
    elif new == "single" and self.step == 3:
      self.step = 0
      self.step_update_ts = current_ts
      self.log("Unlocking the door by code")
      self.call_service("lock/unlock", entity_id="lock.entrance_lock")
    elif new in ["single", "double", "hold"] and self.get_delta_ts(self.last_ringed_ts) > 5:
      self.step = 0
      self.bell_ring()


  def bell_ring(self):
    self.last_ringed_ts = self.get_now_ts()
    living_scene = self.get_living_scene()
    # Pause TV
    if self.get_state("media_player.living_room_apple_tv") == "playing" and living_scene != "party":
      self.media_pause("living_room_apple_tv")
    # Bell sound
    if living_scene != "night":
      self.ring_on_sonos("living_room")
      if self.is_entity_off("binary_sensor.bathroom_door"):
        self.ring_on_sonos("bathroom")
    # Push notifications
    self.send_push("home_or_all", "🔔 Ding-Dong", "bell", sound="Anticipate.caf")
    # Lights
    entity = "light.entrance_cloakroom"
    if living_scene in ["day", "light_cinema"]:
      self.turn_on_entity(entity, flash="short", brightness=254, color_name="red")
      self.run_in(self.restore_light, 1)
    elif living_scene in ["dark_cinema", "party"]:
      self.turn_on_entity(entity, flash="short", brightness=1, color_name="red")
      self.run_in(self.restore_light, 1)


  def ring_on_sonos(self, room):
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
    self.call_service("script/fire_custom_event", custom_event_data="bathroom_entrance_virtual_switch_room_on")
