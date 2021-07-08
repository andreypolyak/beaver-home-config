from base import Base
import requests


class HaCountUpdates(Base):

  def initialize(self):
    super().initialize()
    self.run_every(self.check_updates, "now+300", 600)


  def check_updates(self, kwargs):
    current_version = self.get_state("sensor.ha_info", attribute="current_version")
    newest_version = self.get_state("sensor.ha_info", attribute="newest_version")
    try:
      releases = requests.get("https://api.github.com/repos/home-assistant/core/releases").json()
    except requests.exceptions.RequestException:
      return
    updates_available = 0
    already_available = False
    for release in releases:
      if not release["prerelease"]:
        if release["name"] == current_version:
          break
        elif release["name"] == newest_version:
          already_available = True
          updates_available += 1
        elif already_available:
          updates_available += 1
    self.set_value("input_number.ha_core_updates", updates_available)
