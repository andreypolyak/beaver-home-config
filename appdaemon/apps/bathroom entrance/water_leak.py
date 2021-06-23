import appdaemon.plugins.hass.hassapi as hass

SENSORS = [
  {
    "name": "bathroom_washing_machine",
    "en": "washing machine",
    "ru": "в ванной комнате под стиральной машиной"
  }, {
    "name": "bathroom_bath",
    "en": "bath",
    "ru": "в ванной комнате под ванной"
  }, {
    "name": "bathroom_toilet",
    "en": "toilet",
    "ru": "в ванной комнате под туалетом"
  }, {
    "name": "kitchen_sink",
    "en": "kitchen sink",
    "ru": "на кухне под раковиной"
  }
]


class WaterLeak(hass.Hass):

  def initialize(self):
    self.notifications = self.get_app("notifications")
    for sensor in SENSORS:
      sensor_name = sensor["name"]
      self.listen_state(self.on_leak, f"binary_sensor.{sensor_name}_leak", new="on", old="off", sensor=sensor)


  def on_leak(self, entity, attribute, old, new, kwargs):
    sensor = kwargs["sensor"]
    sensor_en = sensor["en"]
    sensor_ru = sensor["ru"]
    text = f"Внимание! Обнаружена вода {sensor_ru}!"
    self.fire_event("yandex_speak_text", text=text, room="living_room", volume_level=1.0)
    self.notifications.send("home_or_all", f"💧 Water leak under {sensor_en}!", "leak", is_critical=True)
