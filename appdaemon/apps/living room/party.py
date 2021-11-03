from base import Base


class Party(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_party_on, "input_select.living_scene", new="party")
    self.listen_state(self.on_party_off, "input_select.living_scene", old="party")
    self.listen_state(self.on_party_lights_on, "input_boolean.party_lights", new="on")
    self.listen_state(self.on_party_lights_off, "input_boolean.party_lights", new="off")
    self.listen_state(self.on_update_party_source, "input_select.party_source")
    sonos_entity = "media_player.living_room_sonos"
    self.listen_state(self.update_party_sources, sonos_entity, attribute="source_list", immediate=True)
    self.listen_state(self.on_tv_source, sonos_entity, attribute="source", new="TV")
    self.tv_was_on = True


  def on_tv_source(self, entity, attribute, old, new, kwargs):
    if self.living_scene == "party":
      source = self.get_state("input_select.party_source")
      self.select_source("living_room_sonos", source)


  def on_party_lights_on(self, entity, attribute, old, new, kwargs):
    self.turn_on_entity("script.party_lights")


  def on_party_lights_off(self, entity, attribute, old, new, kwargs):
    self.turn_off_entity("light.group_living_room_speakers")


  def on_update_party_source(self, entity, attribute, old, new, kwargs):
    if self.living_scene == "party" and new != old:
      source = self.get_state("input_select.party_source")
      self.select_source("living_room_sonos", source)


  def on_party_on(self, entity, attribute, old, new, kwargs):
    self.turn_on_entity("input_boolean.party_lights")
    self.turn_on_entity("switch.living_room_party_plug")
    self.turn_on_entity("switch.living_room_party_laser_plug")
    self.sonos_unjoin("living_room_sonos")
    self.media_pause("living_room_sonos")
    self.media_pause("bedroom_sonos")
    self.media_pause("kitchen_sonos")
    self.media_pause("bathroom_sonos")
    self.volume_unmute("living_room_sonos")
    self.volume_set("living_room_sonos", 0.5)
    self.set_shuffle("living_room_sonos")
    source = self.get_state("input_select.party_source")
    self.select_source("living_room_sonos", source)


  def on_party_off(self, entity, attribute, old, new, kwargs):
    self.turn_off_entity("input_boolean.party_lights")
    self.turn_off_entity("switch.living_room_party_plug")
    self.turn_off_entity("switch.living_room_party_laser_plug")
    self.media_pause("living_room_sonos")


  def update_party_sources(self, *args, **kwargs):
    selected_source = self.get_state("input_select.party_source")
    sources = self.get_state("media_player.living_room_sonos", attribute="source_list")
    self.set_options("party_source", options=sources)
    if selected_source in sources:
      self.select_option("party_source", selected_source)
