import appdaemon.plugins.hass.hassapi as hass

STATIONS = [
  {
    "button": "1_single",
    "source": "Наше Радио",
    "name": "Наше Радио"
  }, {
    "button": "2_single",
    "source": "R Orfey",
    "name": "Радио Орфей"
  }, {
    "button": "3_single",
    "source": "Ретро FM",
    "name": "Ретро FM"
  }, {
    "button": ["1_hold", "1_double"],
    "source": "Classic Rock 70s 80s 90s, Rock Classics - 70s Rock, 80s Rock, 90s Rock, Rock Classicos",
    "name": "Рочок"
  }, {
    "button": ["2_hold", "2_double"],
    "source": "EBM - Electronic Body Music",
    "name": "Мрачняк"
  }, {
    "button": ["3_hold", "3_double"],
    "source": "Acid House 1988/1989, 80s, 80er, Oldschool, Oldskool, Rave, Housemusic",
    "name": "Восьмидесятые"
  }
]


class MusicSwitch(hass.Hass):

  def initialize(self):
    self.listen_state(self.on_button_press, "sensor.kitchen_music_switch")


  def on_button_press(self, entity, attribute, old, new, kwargs):
    station = self.find_station(new)
    if not station:
      return
    source = station["source"]
    name = station["name"]
    self.fire_event("yandex_speak_text", text=f"Включаю {name}", room="living_room")
    self.call_service("media_player/media_pause", entity_id="media_player.kitchen_sonos")
    self.call_service("media_player/media_pause", entity_id="media_player.living_room_sonos")
    self.call_service("sonos/unjoin", entity_id="media_player.kitchen_sonos")
    self.call_service("media_player/select_source", entity_id="media_player.kitchen_sonos", source=source)


  def find_station(self, button):
    for station in STATIONS:
      if isinstance(station["button"], str) and station["button"] == button:
        return station
      elif isinstance(station["button"], list):
        for station_button in station["button"]:
          if station_button == button:
            return station
    return None
