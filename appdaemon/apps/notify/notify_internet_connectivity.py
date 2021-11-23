from base import Base


class NotifyInternetConnectivity(Base):

  def initialize(self):
    super().initialize()
    self.listen_state(self.on_change, "binary_sensor.internet_connectivity")


  def on_change(self, entity, attribute, old, new, kwargs):
    if new == "on" and old == "off":
      text = "🔗 Internet is back!"
    elif new == "off" and old == "on":
      text = "🔗 No internet connection is found :("
    else:
      return
    self.send_push("admin", text, "interent_connectivity", sound="Complete.caf", url="/lovelace/settings_network")
