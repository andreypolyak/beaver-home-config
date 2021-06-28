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

LOCATIONS = ["not_home", "district", "yard", "downstairs", "home"]


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


  def get_all_person_location_entities(self):
    location_entities = []
    for person_name in self.get_all_person_names():
      entity = f"input_select.{person_name}_location"
      if self.entity_exists(entity):
        location_entities.append(entity)
    return location_entities


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


  def get_persons_at_home(self):
    persons_at_home = []
    for _, person in PERSONS.items():
      person_name = person["name"]
      entity = f"input_select.{person_name}_location"
      if self.entity_exists(entity) and self.get_state(entity) == "home":
        persons_at_home.append(person)
    return persons_at_home


  def get_admin_persons(self):
    admin_persons = []
    for _, person in PERSONS.items():
      if person["admin"]:
        admin_persons.append(person)
    return admin_persons
