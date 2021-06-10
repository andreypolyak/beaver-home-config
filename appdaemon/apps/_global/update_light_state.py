import appdaemon.plugins.hass.hassapi as hass


class UpdateLightState(hass.Hass):

  def initialize(self):
    self.listen_event(self.on_update_light_state, "update_light_state")
    self.run_every(self.update_light_state, "now", 30)


  def on_update_light_state(self, event_name, data, kwargs):
    self.run_in(self.update_light_state, 5)


  def update_light_state(self, kwargs):
    payload = '{"state": ""}'
    self.call_service("mqtt/publish", topic="zigbee2mqtt/Group Main All/get", payload=payload)
    self.call_service("mqtt/publish", topic="zigbee2mqtt_entrance/Group Bathroom Entrance All/get", payload=payload)
    self.call_service("mqtt/publish", topic="zigbee2mqtt_bedroom/Group Bedroom All/get", payload=payload)
