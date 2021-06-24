import appdaemon.plugins.hass.hassapi as hass


class BedSwitch(hass.Hass):

  def initialize(self):
    self.listen_state(self.on_bedroom_switch_change, "sensor.bedroom_bed_night_switch")
    self.listen_event(self.on_virtual_switch, "custom_event",
                      custom_event_data="bedroom_bed_virtual_switch_individual_toggle")


  def on_bedroom_switch_change(self, entity, attribute, old, new, kwargs):
    if new not in ["on", "brightness_move_up"]:
      return
    alarm_ringing = self.get_state("input_boolean.alarm_ringing") == "on"
    alarm_snooze_allowed = self.get_state("input_boolean.alarm_snooze_allowed") == "on"
    if alarm_ringing and alarm_snooze_allowed:
      self.fire_event("custom_event", custom_event_data="snooze_alarm")
      self.call_service("input_boolean/turn_off", entity_id="input_boolean.alarm_snooze_allowed")
      return
    if new == "on":
      if self.get_state("input_select.sleeping_scene") != "night":
        self.log("Turning night mode in Bedroom")
        self.call_service("input_select/select_option", entity_id="input_select.sleeping_scene", option="night")
      else:
        self.turn_night_mode_everywhere()
    elif new == "brightness_move_up":
      self.turn_night_mode_everywhere()


  def on_virtual_switch(self, event_name, data, kwargs):
    if self.get_state("light.group_bedroom_bed") == "off":
      self.call_service("light/turn_on", entity_id="light.group_bedroom_bed",
                        brightness=3, transition=self.get_transition())
    else:
      self.call_service("light/turn_off", entity_id="light.group_bedroom_bed", transition=self.get_transition())


  def turn_off_all_lights(self, kwargs):
    self.call_service("script/turn_off_all_lights_night")
    should_turn_off_wardrobe = self.get_state("binary_sensor.bedroom_wardrobe_door") == "on"
    should_turn_off_table = self.get_state("binary_sensor.bedroom_table") == "on"
    if should_turn_off_wardrobe:
      self.call_service("light/turn_off", entity_id="light.bedroom_wardrobe")
    if should_turn_off_table:
      self.call_service("light/turn_off", entity_id="light.bedroom_table")


  def turn_night_mode_everywhere(self):
    self.log("Turning night mode everywhere")
    self.call_service("input_select/select_option", entity_id="input_select.living_scene", option="night")
    self.call_service("input_select/select_option", entity_id="input_select.sleeping_scene", option="night")
    self.log("Turning lights off everywhere")
    self.run_in(self.turn_off_all_lights, 5)
    self.turn_off_all_lights({})
    self.fire_event("close_bedroom_cover")
    self.fire_event("close_living_room_cover")
    self.fire_event("partly_open_kitchen_cover")


  def get_transition(self):
    return float(self.get_state("input_number.transition"))
