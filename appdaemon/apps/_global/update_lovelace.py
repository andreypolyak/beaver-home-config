import appdaemon.plugins.hass.hassapi as hass
import re


class UpdateLovelace(hass.Hass):

  def initialize(self):
    self.listen_event(self.on_update, "custom_event", custom_event_data="update_lovelace")


  def on_update(self, event_name, data, kwargs):
    with open("/config/ui-lovelace.yaml", "r") as file:
      filedata = file.read()
    updated_at = f"# Updated at: {str(self.get_now())}\n"
    filedata = re.sub(r"# Updated at: .*\n", updated_at, filedata)
    with open("/config/ui-lovelace.yaml", "w") as file:
      file.write(filedata)
