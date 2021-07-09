from base import Base

MEDIA_PLAYERS = {
  "bathroom_sonos": {
    "default_volume": 0.6,
    "zone": "living",
    "scene_volumes": {
      "night": 0.4
    },
    "check_if_playing": ["input_boolean.bathroom_sonos_playing"]
  },
  "kitchen_sonos": {
    "default_volume": 0.3,
    "zone": "living",
    "scene_volumes": {
      "night": 0.2
    },
    "check_if_playing": ["input_boolean.kitchen_sonos_playing"]
  },
  "living_room_sonos": {
    "default_volume": 0.35,
    "zone": "living",
    "scene_volumes": {
      "night": 0.2
    },
    "check_if_playing": ["input_boolean.living_room_sonos_playing", "input_boolean.living_room_tv_playing"]
  },
  "bedroom_sonos": {
    "default_volume": 0.2,
    "zone": "sleeping",
    "scene_volumes": {
      "night": 0.1
    },
    "check_if_playing": ["input_boolean.bedroom_sonos_playing"]
  },
  "sonos_move": {
    "default_volume": 0.2,
    "zone": "sleeping",
    "scene_volumes": {
      "night": 0.1
    },
    "check_if_playing": ["input_boolean.sonos_move_playing"]
  },
  "living_room_yandex_station": {
    "default_volume": 1,
    "zone": "living",
    "scene_volumes": {
      "night": 0.3
    },
    "check_if_playing": ["binary_sensor.living_room_yandex_station_active"]
  },
  "bedroom_yandex_station": {
    "default_volume": 1,
    "zone": "sleeping",
    "scene_volumes": {
      "night": 0.3
    },
    "check_if_playing": ["binary_sensor.bedroom_yandex_station_active"]
  }
}


class MediaVolume(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_scene_change, "input_select.living_scene")
    self.listen_state(self.on_scene_change, "input_select.sleeping_scene")
    for media_player_name, media_player in MEDIA_PLAYERS.items():
      for check_if_playing_entity in media_player["check_if_playing"]:
        self.listen_state(self.on_stop_playing, check_if_playing_entity, new="off")


  def on_scene_change(self, entity, attribute, old, new, kwargs):
    zone = "living"
    if "sleeping" in entity:
      zone = "sleeping"
    for media_player_name, media_player in MEDIA_PLAYERS.items():
      if zone != media_player["zone"]:
        continue
      if self.is_playing_now(media_player["check_if_playing"]):
        continue
      volume_level = self.get_default_volume(media_player, new)
      self.log(f"Scene in {zone.capitalize()} zone changed to: {new}. "
               f"Setting default volume ({volume_level}) for {media_player_name}")
      self.set_volume(media_player_name, volume_level)


  def on_stop_playing(self, entity, attribute, old, new, kwargs):
    for media_player_name, media_player in MEDIA_PLAYERS.items():
      for check_if_playing_entity in media_player["check_if_playing"]:
        if entity != check_if_playing_entity:
          continue
        zone = media_player["zone"]
        scene = self.get_scene(zone)
        if self.is_playing_now(media_player["check_if_playing"]):
          return
        volume_level = self.get_default_volume(media_player, scene)
        self.log(f"{media_player_name} stopped playing. "
                 f"Setting default volume ({volume_level}) for {media_player_name}")
        self.set_volume(media_player_name, volume_level)
        return


  def is_playing_now(self, entities):
    for entity in entities:
      if self.is_entity_on(entity):
        return True
    return False


  def get_default_volume(self, media_player, scene):
    self.log(f"media_player: {media_player}, scene: {scene}")
    if "scene_volumes" in media_player and scene in media_player["scene_volumes"]:
      return media_player["scene_volumes"][scene]
    return media_player["default_volume"]


  def set_volume(self, media_player_name, volume_level):
    entity = f"sensor.{media_player_name}_connection"
    if self.entity_exists(entity) and self.get_state(entity) != "ok":
      return
    entity = f"media_player.{media_player_name}"
    self.volume_set(media_player_name, volume_level)
