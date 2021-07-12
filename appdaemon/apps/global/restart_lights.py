from base import Base


SWITCHES = {
  "bedroom_sonoff_mini": ["bedroom_top_1", "bedroom_top_2", "bedroom_top_3"],
  "bedroom_theo_sonoff_mini": ["bedroom_theo_top_1", "bedroom_theo_top_2"],
  "kitchen_sonoff_mini": ["kitchen_top_1", "kitchen_top_2", "kitchen_top_3"],
  "living_room_sonoff_mini": ["living_room_top_1", "living_room_top_2", "living_room_top_3", "living_room_top_4"]
}


class RestartLights(Base):

  def initialize(self):
    super().initialize()
    self.handles = {}
    self.unavailable_lights = {}
    for switch, lights in SWITCHES.items():
      self.unavailable_lights[switch] = []
      self.handles[switch] = None
      for light in lights:
        self.listen_state(self.on_unavailable, f"light.{light}", new="unavailable", immediate=True)
        self.listen_state(self.on_available, f"light.{light}", old="unavailable", immediate=True)


  def on_unavailable(self, entity, attribute, old, new, kwargs):
    entity = entity.replace("light.", "")
    self.log(f"Unavailable light entity found: {entity}")
    for switch, lights in SWITCHES.items():
      if entity not in lights:
        continue
      if entity not in self.unavailable_lights[switch]:
        self.unavailable_lights[switch].append(entity)
      self.cancel_handle(self.handles[switch])
      self.handles[switch] = self.run_in(self.check_reset, 300, switch=switch)
      return


  def on_available(self, entity, attribute, old, new, kwargs):
    entity = entity.replace("light.", "")
    self.log(f"Available light entity found: {entity}")
    for switch, lights in SWITCHES.items():
      if entity not in lights:
        continue
      if entity in self.unavailable_lights[switch]:
        self.unavailable_lights[switch].remove(entity)
      if len(self.unavailable_lights[switch]) == 0:
        self.cancel_handle(self.handles[switch])
      return


  def check_reset(self, kwargs):
    switch = kwargs["switch"]
    failed_lights = []
    for light in SWITCHES[switch]:
      if self.get_state(f"light.{light}") == "unavailable":
        failed_lights.append(light)
    if len(failed_lights) == 0:
      self.log(f"{switch} reset will not be performed because no unavailable light were found")
      return
    if self.get_living_scene() == "away":
      self.log(f"{switch} quiet reset because scene is away")
      self.reset(switch)
      self.run_in(self.turn_off_all, 10)
      return
    self.log(f"{switch} reset with notification")
    switch_name = switch.replace("_sonoff_mini", "").replace("_", " ").title()
    message = f"🥺 {switch_name} lights are unavailable, restarting them"
    self.send_push("home_or_none", message, "restart_lights", url="/lovelace/settings_entities")
    self.reset(switch)


  def reset(self, switch):
    self.turn_off_entity(f"switch.{switch}")
    self.run_in(self.turn_on_switch, 2, switch=switch)


  def turn_on_switch(self, kwargs):
    switch = kwargs["switch"]
    self.turn_on_entity(f"switch.{switch}")


  def turn_off_all(self, kwargs):
    if self.get_living_scene() == "away":
      self.turn_off_entity("light.ha_group_all")
