import appdaemon.plugins.hass.hassapi as hass


class NotifyArrival(hass.Hass):

  def initialize(self):
    self.storage = self.get_app("persistent_storage")
    self.persons = self.get_app("persons")
    self.notifications = self.get_app("notifications")

    default = {
        "last_notified_about_district": 0,
        "last_notified_about_downstairs": 0,
        "left_home": 0,
        "arrived": 0
    }
    person_names = self.persons.get_all_person_names(with_phone=True)
    for person_name in person_names:
      self.storage.init(f"notify_arrival.{person_name}", default)
    for entity in self.persons.get_all_person_location_entities():
      self.listen_state(self.on_location_change, entity)


  def on_location_change(self, entity, attribute, old, new, kwargs):
    current_ts = self.get_now_ts()
    arriving_person_name = self.persons.get_person_name_from_entity_name(entity)
    if new != "home" and old == "home":
      self.storage.write(f"notify_arrival.{arriving_person_name}", current_ts, attribute="left_home")
    if new == "home":
      self.storage.write(f"notify_arrival.{arriving_person_name}", current_ts, attribute="arrived")

    arriving_person_state = self.storage.read(f"notify_arrival.{arriving_person_name}", attribute="all")
    for person_name in self.persons.get_all_person_names(with_location=True):
      person_state = self.storage.read(f"notify_arrival.{person_name}", attribute="all")
      person_location = self.get_state(f"input_select.{person_name}_location")
      if (
          person_name != arriving_person_name
          and person_location == "home"
          and new != "not_home"
          and old == "not_home"
          and (current_ts - arriving_person_state["last_notified_about_district"]) > 600
          and (current_ts - arriving_person_state["left_home"]) > 1800
          and (current_ts - person_state["arrived"]) > 300
      ):
        self.storage.write(f"notify_arrival.{arriving_person_name}", current_ts,
                           attribute="last_notified_about_district")
        arriving_person_emoji = self.persons.get_info(arriving_person_name)["emoji"]
        message = f"{arriving_person_emoji} {arriving_person_name.capitalize()} is arriving home!"
        self.notifications.send(person_name, message, "notify_arrival_district", sound="Hello.caf",
                                url="/lovelace/outside", ios_category="notify_arrival")
      if (
          person_name != arriving_person_name
          and person_location == "home"
          and new == "downstairs"
          and old != "downstairs"
          and (current_ts - arriving_person_state["last_notified_about_downstairs"]) > 600
          and (current_ts - arriving_person_state["left_home"]) > 1800
          and (current_ts - person_state["arrived"]) > 300
      ):
        self.storage.write(f"notify_arrival.{arriving_person_name}", current_ts,
                           attribute="last_notified_about_downstairs")
        arriving_person_emoji = self.persons.get_info(arriving_person_name)["emoji"]
        message = f"{arriving_person_emoji} {arriving_person_name.capitalize()} is downstairs!"
        self.notifications.send(person_name, message, "notify_arrival_downstairs", sound="Hello.caf",
                                url="/lovelace/outside", ios_category="notify_arrival")
