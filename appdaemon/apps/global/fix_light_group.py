from base import Base


class FixLightGroup(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_unavailable, "light.ha_group_all", new="unavailable")
    self.update_light()


  def on_unavailable(self, entity, attribute, old, new, kwargs):
    self.update_light()


  def update_light(self):
    self.call_service("homeassistant/update_entity", entity_id="light.ha_group_all")
