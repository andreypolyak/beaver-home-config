import appdaemon.plugins.hass.hassapi as hass


class Bell(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    self.notifications = self.get_app("notifications")
    self.step = 0
    self.step_update_ts = 0
    self.last_ringed_ts = 0
    self.listen_state(self.on_bell_ring, "sensor.entrance_door_bell")


  def on_bell_ring(self, entity, attribute, old, new, kwargs):
    current_ts = self.get_now_ts()
    if (current_ts - self.step_update_ts) > 10:
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
    elif new in ["single", "double", "hold"] and (current_ts - self.last_ringed_ts) > 5:
      self.step = 0
      self.bell_ring()


  def bell_ring(self):
    self.last_ringed_ts = self.get_now_ts()
    current_living_scene = self.get_state("input_select.living_scene")
    # Pause TV
    if self.get_state("media_player.living_room_apple_tv") == "playing" and current_living_scene != "party":
      self.call_service("media_player/media_pause", entity_id="media_player.living_room_apple_tv")
    # Bell sound
    if current_living_scene != "night":
      self.call_service("sonos/snapshot", entity_id="all")
      url = self.args["bell_sound_url"]
      self.call_service("media_player/volume_set", entity_id="media_player.living_room_sonos", volume_level=0.15)
      self.call_service("media_player/play_media", entity_id="media_player.living_room_sonos",
                        media_content_type="music", media_content_id=url)
      if self.get_state("binary_sensor.bathroom_door") == "off":
        self.call_service("media_player/volume_set", entity_id="media_player.bathroom_sonos", volume_level=0.15)
        self.call_service("media_player/play_media", entity_id="media_player.bathroom_sonos",
                          media_content_type="music", media_content_id=url)
      self.run_in(self.restore_sonos, 2)
    # Push notifications
    self.notifications.send("home_or_all", "🔔 Ding-Dong", "bell", sound="Anticipate.caf")
    # Lights
    if current_living_scene in ["day", "light_cinema"]:
      self.call_service("light/turn_on", entity_id="light.entrance_cloakroom", flash="short",
                        brightness=254, color_name="red")
      self.run_in(self.restore_light, 1)
    elif current_living_scene in ["dark_cinema", "party"]:
      self.call_service("light/turn_on", entity_id="light.entrance_cloakroom", flash="short",
                        brightness=1, color_name="red")
      self.run_in(self.restore_light, 1)


  def restore_sonos(self, kwargs):
    self.call_service("sonos/restore", entity_id="all")


  def restore_light(self, kwargs):
    self.call_service("script/fire_custom_event", custom_event_data="bathroom_entrance_virtual_switch_room_on")
