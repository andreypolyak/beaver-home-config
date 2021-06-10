import appdaemon.plugins.hass.hassapi as hass

PERSONS = {
  "andrey": {
    "name": "andrey",
    "ru_name": "Андрей",
    "phone": "andrey_iphone_11_pro_max",
    "admin": True,
    "emoji": "🕺"
  },
  "katya": {
    "name": "katya",
    "ru_name": "Катя",
    "phone": "katya_iphone_12_pro_max",
    "admin": False,
    "emoji": "💃"
  },
  "theo": {
    "name": "theo",
    "ru_name": "Тео",
    "phone": None,
    "admin": False,
    "emoji": "👦"
  }
}


class Persons(hass.Hass):

  def initialize(self):
    self.storage = self.get_app("persistent_storage")
    for person_name in PERSONS:
      self.storage.init(f"persons.{person_name}", {})


  def get_info(self, name):
    return PERSONS[name]


  def get_all_persons(self):
    persons = []
    for _, person in PERSONS.items():
      persons.append(person)
    return persons


  def get_all_person_names(self):
    person_names = []
    for _, person in PERSONS.items():
      person_names.append(person["name"])
    return person_names


  def get_all_person_names_except_provided(self, person_name):
    person_names = []
    for _, person in PERSONS.items():
      if person["name"] != person_name:
        person_names.append(person["name"])
    return person_names


  def get_person_name_from_entity_name(self, entity):
    for _, person in PERSONS.items():
      if person["name"] in entity:
        return person["name"]
    return


  def get_person_from_entity_name(self, entity):
    for _, person in PERSONS.items():
      if person["name"] in entity:
        return person
    return


  def get_min_proximity(self):
    min_proximity = None
    for _, person in PERSONS.items():
      proximity = self.__get_proximity(person["name"])
      if not proximity:
        continue
      if min_proximity is None or proximity < min_proximity:
        min_proximity = proximity
    return min_proximity


  def get_person_names_with_location(self, location):
    get_person_names_with_location = []
    for _, person in PERSONS.items():
      person_name = person["name"]
      entity = f"input_select.{person_name}_location"
      if self.entity_exists(entity) and self.get_state(entity) == location:
        get_person_names_with_location.append(person["name"])
    return get_person_names_with_location


  def is_anyone_home(self):
    is_anyone_home = False
    for _, person in PERSONS.items():
      person_name = person["name"]
      entity = f"input_select.{person_name}_location"
      if self.entity_exists(entity) and self.get_state(entity) == "home":
        is_anyone_home = True
    return is_anyone_home


  def get_person_names_inside_proximity(self, proximity_max):
    person_names_inside_proximity = []
    for _, person in PERSONS.items():
      proximity = self.__get_proximity(person["name"])
      if not proximity:
        continue
      if proximity <= proximity_max:
        person_names_inside_proximity.append(person["name"])
    return person_names_inside_proximity


  def update_location(self, to):
    persons = []
    if isinstance(to, list):
      for person_name in to:
        if person_name in PERSONS:
          persons.append(PERSONS[person_name])
    elif isinstance(to, str):
      if to in PERSONS:
        persons.append(PERSONS[to])
    for person in persons:
      person_phone = person["phone"]
      if person_phone:
        self.call_service(f"notify/mobile_app_{person_phone}", message="request_location_update")


  def send_notification(self, to, message, category, sound="none", is_critical=False,
                        min_delta=None, max_proximity=None, url=None, ios_category=None, actions=None):
    persons = []
    if isinstance(to, list):
      for person_name in to:
        if person_name in PERSONS:
          persons.append(PERSONS[person_name])
    elif to == "admin":
      persons = self.__get_admin_persons()
    elif to == "home_or_all":
      persons_at_home = self.__get_persons_at_home()
      if len(persons_at_home) > 0:
        persons = persons_at_home
      else:
        persons = self.get_all_persons()
    elif to == "home_or_none":
      persons_at_home = self.__get_persons_at_home()
      if len(persons_at_home) > 0:
        persons = persons_at_home
    elif to == "proximity" and max_proximity:
      persons = self.get_persons_inside_proximity(max_proximity)
    elif isinstance(to, str):
      if to in PERSONS:
        persons.append(PERSONS[to])

    for person in persons:
      if min_delta:
        delta = self.__get_notification_ts_delta(person["name"], category)
        if (delta and delta < min_delta):
          continue
      person_name = person["name"]
      self.storage.write(f"persons.{person_name}", self.get_now_ts(), attribute=category)
      if ios_category:
        category = ios_category
      self.__send_notification(person, message, category, sound, is_critical, url, actions)


  def __get_persons_at_home(self):
    persons_at_home = []
    for _, person in PERSONS.items():
      person_name = person["name"]
      entity = f"person.{person_name}"
      if self.entity_exists(entity) and self.get_state(entity) == "home":
        persons_at_home.append(person)
    return persons_at_home


  def __get_admin_persons(self):
    admin_persons = []
    for _, person in PERSONS.items():
      if person["admin"]:
        admin_persons.append(person)
    return admin_persons


  def __get_persons_inside_proximity(self, proximity_max):
    persons_inside_proximity = []
    for _, person in PERSONS.items():
      proximity = self.__get_proximity(person["name"])
      if not proximity:
        continue
      if proximity <= proximity_max:
        persons_inside_proximity.append(person["name"])
    return persons_inside_proximity


  def __get_notification_ts_delta(self, person_name, category):
    category_ts = self.storage.read(f"persons.{person_name}", attribute=category)
    if category_ts:
      delta = self.get_now_ts() - category_ts
      return delta
    return


  def __send_notification(self, person, message, category, sound, is_critical, url, actions):
    person_phone = person["phone"]
    person_name = person["name"]
    if not person_phone:
      return
    # HA App Push
    properties = self.__get_notification_properties(person_name, category, sound, is_critical, url, actions)
    self.call_service(f"notify/mobile_app_{person_phone}", message=message, data=properties)
    # Telegram
    telegram_name = person_name.capitalize()
    telegram_message = f"{telegram_name} → {message}"
    self.call_service("telegram_bot/send_message", message=telegram_message, target=self.args["chat_id"])
    # HA Sensor
    sensor_name = person_name.capitalize()[0]
    sensor_message = f"\"{sensor_name}→{message}\""[:99]
    if self.get_state("input_text.last_notification") == sensor_message:
      self.call_service("input_text/set_value", entity_id="input_text.last_notification", value="")
    self.call_service("input_text/set_value", entity_id="input_text.last_notification", value=sensor_message)
    # Log
    self.log(f"Send notification with properties: {properties}")


  def __get_notification_properties(self, person_name, category, sound, is_critical, url, actions):
    properties = {
      "action_data": {"person_name": person_name},
      "apns_headers": {"apns-collapse-id": category},
      "push": {
        "sound": sound
      }
    }
    if is_critical:
      properties["push"]["sound"] = {"name": "default", "critical": 1, "volume": 1.0}
    if url:
      properties["url"] = url
    if actions:
      properties["actions"] = actions
    return properties


  def __get_proximity(self, person_name):
    entity = f"proximity.ha_{person_name}_home"
    if not self.entity_exists(entity):
      return None
    try:
      proximity = float(self.get_state(entity))
      return proximity
    except ValueError:
      return 0
