from base import Base


class BedNightSwitch(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_bedroom_switch_change, "sensor.bedroom_bed_night_switch")
    self.listen_event(self.on_virtual_switch, "bedroom_bed_virtual_switch_individual_toggle")


  def on_bedroom_switch_change(self, entity, attribute, old, new, kwargs):
    if new not in ["on", "brightness_move_up"]:
      return
    # If alarm is ringing
    if self.entity_is_on("input_boolean.alarm_ringing"):
      if self.entity_is_on("input_boolean.alarm_snooze_allowed"):
        self.fire_event("snooze_alarm")
        self.turn_off_entity("input_boolean.alarm_snooze_allowed")
      else:
        text = "Откладывать будильник больше нельзя!"
        self.fire_event("yandex_speak_text", text=text, room="bedroom")
      return
    # If short press
    if new == "on":
      if self.sleeping_scene != "night" or self.entity_is_off("binary_sensor.bedroom_door"):
        self.log("Turning night mode in Bedroom")
        self.fire_event("close_bedroom_cover")
        self.set_sleeping_scene("night")
      else:
        self.turn_night_mode_everywhere()
      return
    # If long press
    if new == "brightness_move_up":
      self.turn_night_mode_everywhere()


  def on_virtual_switch(self, event_name, data, kwargs):
    transition = self.get_float_state("input_number.transition")
    if self.entity_is_off("light.group_bedroom_bed"):
      self.turn_on_entity("light.group_bedroom_bed", brightness=3, transition=transition)
    else:
      self.turn_off_entity("light.group_bedroom_bed", transition=transition)


  def turn_off_all_lights(self, kwargs):
    self.turn_off_entity("light.all_lights_night")
    if self.entity_is_on("binary_sensor.bedroom_wardrobe_door"):
      self.turn_off_entity("light.bedroom_wardrobe")
    if self.entity_is_on("binary_sensor.bedroom_table"):
      self.turn_off_entity("light.bedroom_table")


  def turn_night_mode_everywhere(self):
    self.log("Turning night mode everywhere")
    self.set_living_scene("night")
    self.set_sleeping_scene("night")
    self.log("Turning lights off everywhere")
    self.run_in(self.turn_off_all_lights, 5)
    self.turn_off_all_lights({})
    self.fire_event("close_bedroom_cover")
    self.fire_event("close_living_room_cover")
    self.fire_event("close_kitchen_cover")
