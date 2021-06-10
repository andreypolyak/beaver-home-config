import appdaemon.plugins.hass.hassapi as hass


class Party(hass.Hass):

  def initialize(self):
    self.listen_state(self.on_party_tv_on, "input_boolean.party_tv", new="on")
    self.listen_state(self.on_party_tv_off, "input_boolean.party_tv", new="off")
    self.listen_state(self.on_party_on, "input_select.living_scene", new="party")
    self.listen_state(self.on_party_off, "input_select.living_scene", old="party")
    self.listen_state(self.on_party_lights_on, "input_boolean.party_lights", new="on")
    self.listen_state(self.on_party_lights_off, "input_boolean.party_lights", new="off")
    self.listen_state(self.on_update_party_source, "input_select.party_source")
    self.update_party_sources({})
    self.listen_state(self.update_party_sources, "media_player.living_room_sonos", attribute="source_list")
    self.listen_state(self.on_tv_source, "media_player.living_room_sonos", attribute="source", new="TV")
    self.tv_was_on = True


  def on_tv_source(self, entity, attribute, old, new, kwargs):
    if self.get_state("input_select.living_scene") == "party":
      source = self.get_state("input_select.party_source")
      self.call_service("media_player/select_source", entity_id="media_player.living_room_sonos", source=source)


  def on_party_tv_on(self, entity, attribute, old, new, kwargs):
    if self.get_state("input_select.living_scene") == "party":
      if self.get_state("binary_sensor.living_room_tv") == "off":
        self.log("TV was turned off, turning it on for party")
        self.tv_was_on = False
        self.call_service("script/turn_on", entity_id="script.party_tv_start_and_turn_on_tv")
      else:
        self.tv_was_on = True
        self.call_service("script/turn_on", entity_id="script.party_tv_start")


  def on_party_lights_on(self, entity, attribute, old, new, kwargs):
    self.call_service("script/turn_on", entity_id="script.party_lights")


  def on_party_lights_off(self, entity, attribute, old, new, kwargs):
    self.call_service("light/turn_off", entity_id="light.group_living_room_speakers")


  def on_party_tv_off(self, entity, attribute, old, new, kwargs):
    if not self.tv_was_on:
      self.call_service("script/turn_on", entity_id="script.party_tv_stop_and_turn_off_tv")
    else:
      self.call_service("script/turn_on", entity_id="script.party_tv_stop")


  def on_update_party_source(self, entity, attribute, old, new, kwargs):
    if self.get_state("input_select.living_scene") == "party" and new != old:
      source = self.get_state("input_select.party_source")
      self.call_service("media_player/select_source", entity_id="media_player.living_room_sonos", source=source)


  def on_party_on(self, entity, attribute, old, new, kwargs):
    self.call_service("input_boolean/turn_on", entity_id="input_boolean.party_lights")
    self.call_service("input_boolean/turn_on", entity_id="input_boolean.party_tv")
    self.call_service("switch/turn_on", entity_id="switch.living_room_party_plug")
    self.call_service("switch/turn_on", entity_id="switch.living_room_party_laser_plug")
    self.call_service("media_player/media_pause", entity_id="media_player.kitchen_sonos")
    self.call_service("media_player/media_pause", entity_id="media_player.bedroom_sonos")
    self.call_service("media_player/media_pause", entity_id="media_player.bathroom_sonos")
    self.call_service("media_player/media_pause", entity_id="media_player.living_room_sonos")
    self.call_service("sonos/unjoin", entity_id="media_player.living_room_sonos")
    self.call_service("media_player/volume_mute", entity_id="media_player.living_room_sonos", is_volume_muted=False)
    self.call_service("media_player/volume_set", entity_id="media_player.living_room_sonos", volume_level="0.5")
    self.call_service("media_player/shuffle_set", entity_id="media_player.living_room_sonos", shuffle="true")
    source = self.get_state("input_select.party_source")
    self.call_service("media_player/select_source", entity_id="media_player.living_room_sonos", source=source)


  def on_party_off(self, entity, attribute, old, new, kwargs):
    self.call_service("input_boolean/turn_off", entity_id="input_boolean.party_lights")
    self.call_service("input_boolean/turn_off", entity_id="input_boolean.party_tv")
    self.call_service("switch/turn_off", entity_id="switch.living_room_party_plug")
    self.call_service("switch/turn_off", entity_id="switch.living_room_party_laser_plug")
    self.call_service("media_player/media_pause", entity_id="media_player.living_room_sonos")


  def update_party_sources(self, *args, **kwargs):
    selected_source = self.get_state("input_select.party_source")
    sources = self.get_state("media_player.living_room_sonos", attribute="source_list")
    self.call_service("input_select/set_options", entity_id="input_select.party_source", options=sources)
    if selected_source in sources:
      self.call_service("input_select/select_option", entity_id="input_select.party_source", option=selected_source)
