import appdaemon.plugins.hass.hassapi as hass


class PersistentStorage(hass.Hass):

  def initialize(self):
    pass


  def read(self, entity, attribute=None):
    state = self.get_state(entity, namespace="persistent_storage", attribute="all")["attributes"]
    self.log(f"Reading {entity} state: {state}")
    if attribute == "all":
      return state
    elif attribute and attribute in state:
      return state[attribute]
    elif attribute:
      return None
    if "default_data" in state:
      return state["default_data"]
    else:
      return None


  def write(self, entity, value, attribute=None):
    attributes = {}
    replace = False
    if attribute == "all":
      replace = True
      attributes = value
    elif attribute:
      attributes[attribute] = value
    else:
      attributes["default_data"] = value
    self.log(f"Writing to {entity} state: {attributes}")
    self.set_state(entity, namespace="persistent_storage", attributes=attributes, replace=replace)


  def init(self, entity, default):
    app_name = entity.split(".")[0]
    object_name = entity.split(".")[1]
    state = self.get_state(entity, namespace="persistent_storage", attribute="all")
    if not state or "attributes" not in state:
      self.log(f"Setting default state in app {app_name} for object {object_name}")
      if type(default) is not dict:
        default = {"default_data": default}
      self.set_state(entity, namespace="persistent_storage", state="on", attributes=default)
      return
    else:
      if type(default) is not dict:
        if "default_data" not in state["attributes"]:
          self.log(f"Setting default state in app {app_name} for object {object_name}")
          default = {"default_data": default}
          self.set_state(entity, namespace="persistent_storage", state="on", attributes=default)
          return
      else:
        for key, value in default.items():
          if key not in state["attributes"]:
            self.log(f"Setting default state in app {app_name} for object {object_name}")
            self.set_state(entity, namespace="persistent_storage", state="on", attributes=default)
            return
    saved_state = str(self.get_state(entity, namespace="persistent_storage", attribute="all")["attributes"])
    self.log(f"Using saved state in app {app_name} for object {object_name}: {saved_state}")
