from base import Base


class Presence(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_nearest_person_change, "input_select.nearest_person_location", immediate=True)
    self.listen_state(self.on_living_scene, "input_select.living_scene")
    self.listen_state(self.on_sleeping_scene, "input_select.sleeping_scene")
    self.listen_state(self.on_activity, "lock.entrance_lock", new="unlocked", old="locked")
    self.listen_state(self.on_activity, "binary_sensor.entrance_door", new="on", old="off")
    self.run_every(self.turn_off_all, "now+300", 3600)
    for sensor in self.get_state("sensor"):
      if sensor.endswith("_switch"):
        self.listen_state(self.on_activity, sensor)


  def on_nearest_person_change(self, entity, attribute, old, new, kwargs):
    if new == "not_home" and self.get_living_scene() != "away" and self.is_entity_off("input_boolean.guest_mode"):
      self.log(f"Change scene to Away because nearest person changed location to {new}")
      self.set_living_scene("away")


  def on_living_scene(self, entity, attribute, old, new, kwargs):
    if new == "away" and old != "away":
      self.set_sleeping_scene("away")
      self.turn_off_all({})
      self.run_in(self.turn_off_all, 10)
      self.run_in(self.update_light_state, 20)
    elif new != "away" and old == "away" and self.get_sleeping_scene() == "away":
      self.set_sleeping_scene("day")


  def on_sleeping_scene(self, entity, attribute, old, new, kwargs):
    if new == "away" and old != "away":
      self.set_living_scene("away")
    if new != "away" and old == "away" and self.get_living_scene() == "away":
      self.set_living_scene("day")


  def on_activity(self, entity, attribute, old, new, kwargs):
    if self.is_bad(new) or self.get_living_scene() != "away":
      return
    self.log(f"Change scene to Day because activity occured on: {entity}")
    self.set_living_scene("day")
    self.set_sleeping_scene("day")


  def turn_off_all(self, kwargs):
    if self.get_living_scene() != "away":
      return
    for timer in self.get_state("timer"):
      if "timer.light_" in timer:
        self.timer_cancel(timer)
    self.turn_off_entity("light.all_lights")


  def update_light_state(self, kwargs):
    self.call_service("script/update_light_state")
