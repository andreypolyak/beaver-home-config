from base import Base


class NotifyArrival(Base):

  def initialize(self):
    super().initialize()
    default = {
        "last_notified_about_district": 0,
        "last_notified_about_downstairs": 0,
        "left_home": 0,
        "arrived": 0
    }
    person_names = self.get_all_person_names(with_phone=True)
    for person_name in person_names:
      self.init_storage("notify_arrival", person_name, default)
    for entity in self.get_all_person_location_entities():
      self.listen_state(self.on_person_home, entity, new="home")
      self.listen_state(self.on_person_not_home, entity, old="home")
      self.listen_state(self.on_location_change, entity)


  def on_person_home(self, entity, attribute, old, new, kwargs):
    person_name = self.get_person_name_from_entity_name(entity)
    self.write_storage(person_name, self.get_now_ts(), attribute="arrived")


  def on_person_not_home(self, entity, attribute, old, new, kwargs):
    person_name = self.get_person_name_from_entity_name(entity)
    self.write_storage(person_name, self.get_now_ts(), attribute="left_home")


  def on_location_change(self, entity, attribute, old, new, kwargs):
    arriving_person_name = self.get_person_name_from_entity_name(entity)
    for person_name in self.get_all_person_names(with_location=True):
      person_location = self.get_state(f"input_select.{person_name}_location")
      if person_location != "home" or person_name == arriving_person_name:
        continue
      if new in ["district", "yard"] and old == "not_home":
        self.send_arrival_notification("district", arriving_person_name, person_name)
      if new == "downstairs":
        self.send_arrival_notification("downstairs", arriving_person_name, person_name)


  def send_arrival_notification(self, mode, arriving_person_name, person_name):
    location_text = "arriving home"
    if mode == "downstairs":
      location_text = mode
    person_state = self.read_storage(person_name, attribute="all")
    arriving_person_state = self.read_storage(arriving_person_name, attribute="all")
    if (
        self.get_delta_ts(arriving_person_state[f"last_notified_about_{mode}"]) > 600
        and self.get_delta_ts(arriving_person_state["left_home"]) > 1800
        and self.get_delta_ts(person_state["arrived"]) > 300
    ):
      self.write_storage(arriving_person_name, self.get_now_ts(), attribute=f"last_notified_about_{mode}")
      arriving_person_emoji = self.get_all_persons()[arriving_person_name]["emoji"]
      message = f"{arriving_person_emoji} {arriving_person_name.capitalize()} is {location_text}!"
      category = f"notify_arrival_{mode}"
      url = "/lovelace/outside"
      sound = "Hello.caf"
      ios_category = "notify_arrival"
      self.send_push(person_name, message, category, sound=sound, url=url, ios_category=ios_category)
