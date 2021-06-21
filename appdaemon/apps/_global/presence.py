import appdaemon.plugins.hass.hassapi as hass


class Presence(hass.Hass):

  def initialize(self):
    self.persons = self.get_app("persons")
    for entity in self.persons.get_all_person_location_entities():
      self.listen_state(self.on_location_change, entity)
    self.listen_state(self.on_living_scene, "input_select.living_scene")
    self.listen_state(self.on_sleeping_scene, "input_select.sleeping_scene")
    self.listen_state(self.on_activity, "lock.entrance_lock", new="unlocked", old="locked")
    self.listen_state(self.on_activity, "binary_sensor.entrance_door", new="on", old="off")
    self.run_every(self.turn_off_all, "now", 3600)
    sensors = self.get_state("sensor")
    for sensor in sensors:
      if sensor.endswith("_switch"):
        self.listen_state(self.on_activity, sensor)


  def on_location_change(self, entity, attribute, old, new, kwargs):
    is_anyone_home = self.persons.is_anyone_home()
    if (
      not is_anyone_home
      and self.get_state("input_select.living_scene") != "away"
      and self.get_state("input_boolean.guest_mode") != "on"
    ):
      self.log("Change scene to Away")
      self.call_service("input_select/select_option", entity_id="input_select.living_scene", option="away")


  def on_living_scene(self, entity, attribute, old, new, kwargs):
    if new == "away" and old != "away":
      self.call_service("input_select/select_option", entity_id="input_select.sleeping_scene", option="away")
      self.turn_off_all({})
      self.run_in(self.turn_off_all, 10)
    elif new != "away" and old == "away" and self.get_state("input_select.sleeping_scene") == "away":
      self.call_service("input_select/select_option", entity_id="input_select.sleeping_scene", option="day")


  def on_sleeping_scene(self, entity, attribute, old, new, kwargs):
    if new == "away" and old != "away":
      self.call_service("input_select/select_option", entity_id="input_select.living_scene", option="away")
    if new != "away" and old == "away" and self.get_state("input_select.living_scene") == "away":
      self.call_service("input_select/select_option", entity_id="input_select.living_scene", option="day")


  def on_activity(self, entity, attribute, old, new, kwargs):
    if self.get_state("input_select.living_scene") == "away" and new not in ["unavailable", "unknown", "", "None"]:
      self.log(f"Change scene to Day because activity occured on: {entity}")
      self.call_service("input_select/select_option", entity_id="input_select.living_scene", option="day")
      self.call_service("input_select/select_option", entity_id="input_select.sleeping_scene", option="day")


  def turn_off_all(self, kwargs):
    if self.get_state("input_select.living_scene") != "away":
      return
    timers = self.get_state("timer")
    for timer in timers.keys():
      if "timer.light_" in timer:
        self.call_service("timer/cancel", entity_id=timer)
    # self.call_service("homeassistant/turn_off", entity_id="group.all")
    self.call_service("script/turn_off_all_lights")
