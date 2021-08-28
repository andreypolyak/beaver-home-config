from base import Base
from random import randrange


class FunToilet(Base):

  def initialize(self):
    super().initialize()
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
      self.media_pause("bathroom_sonos")


  def start_playback(self):
    if (
      self.living_scene
      and self.now_is_between("07:00:00", "10:00:00")
      and self.entity_is_on("input_boolean.fun_toilet")
      and randrange(100) < 10
    ):
      self.media_pause("bathroom_sonos")
      self.sonos_unjoin("bathroom_sonos")
      source = "The Woodchuck Song"
      self.select_source("bathroom_sonos", source)
      self.repeat_set("bathroom_sonos", "one")
