import appdaemon.plugins.hass.hassapi as hass
from random import randrange


class FunToilet(hass.Hass):

  def initialize(self):
    self.listen_state(self.on_door_close, "binary_sensor.bathroom_door", new="off", old="on")
    self.listen_state(self.on_door_open, "binary_sensor.bathroom_door", new="on", old="off")
    self.listen_state(self.on_fun_toilet_off, "input_boolean.fun_toilet", new="off", old="on")


  def on_door_close(self, entity, attribute, old, new, kwargs):
    self.start_playback()


  def on_door_open(self, entity, attribute, old, new, kwargs):
    self.stop_playback()


  def on_fun_toilet_off(self, entity, attribute, old, new, kwargs):
    self.stop_playback()


  def stop_playback(self):
    sonos_state = self.get_state("media_player.bathroom_sonos", attribute="all")
    if (
      "media_title" in sonos_state["attributes"]
      and sonos_state["attributes"]["media_title"] == "The Woodchuck Song"
      and sonos_state["state"] == "playing"
    ):
      self.call_service("media_player/media_pause", entity_id="media_player.bathroom_sonos")


  def start_playback(self):
    if (
      self.get_state("input_select.living_scene") == "day"
      and self.now_is_between("07:00:00", "10:00:00")
      and self.get_state("input_boolean.fun_toilet") == "on"
      and randrange(100) < 10
    ):
      self.call_service("media_player/media_pause", entity_id="media_player.bathroom_sonos")
      self.call_service("sonos/unjoin", entity_id="media_player.bathroom_sonos")
      source = "The Woodchuck Song"
      self.call_service("media_player/select_source", entity_id="media_player.bathroom_sonos", source=source)
      self.call_service("media_player/repeat_set", entity_id="media_player.bathroom_sonos", repeat="one")
