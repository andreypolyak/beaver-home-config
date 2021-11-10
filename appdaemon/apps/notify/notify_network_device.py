from base import Base


class NotifyNetworkDevice(Base):

  def initialize(self):
    super().initialize()
    self.listen_event(self.on_new_network_device, "new_network_device")


  def on_new_network_device(self, event_name, data, kwargs):
    attributes = data["state"]["attributes"]
    if "name" in attributes and len(attributes["name"]) > 0:
      name = attributes["name"]
    elif "friendly_name" in attributes and len(attributes["friendly_name"]) > 0:
      name = attributes["friendly_name"]
    elif "hostname" in attributes and len(attributes["hostname"]) > 0:
      name = attributes["hostname"]
    elif "oui" in attributes and len(attributes["oui"]) > 0:
      name = attributes["oui"]
    elif "mac" in attributes and len(attributes["mac"]) > 0:
      name = attributes["mac"]
    else:
      name = data["entity"].replace("device_tracker.", "")
    ip_text = ""
    if "ip" in attributes:
      ip = attributes["ip"]
      ip_text = f" ({ip})"
    if attributes["is_wired"]:
      text = f"🕸️ New ethernet device {name} connected{ip_text}"
    elif "essid" in attributes:
      network_name = attributes["essid"]
      text = f"🕸️ New WiFi device {name} connected to {network_name}{ip_text}"
    else:
      text = f"🕸️ New WiFi device {name} connected{ip_text}"
    self.send_push("admin", text, "network_device", url="/lovelace/settings_trackers")
