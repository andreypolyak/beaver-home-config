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


  def are_all_persons_inside_location(self, location):
    locations = LOCATIONS[:]
    if location not in locations:
      return False
    location_index = locations.index(location)
    min_location_index = 999
    for _, person in PERSONS.items():
      person_name = person["name"]
      entity = f"input_select.{person_name}_location"
      if not self.entity_exists(entity):
        continue
      person_location = self.get_state(entity)
      person_location_index = locations.index(person_location)
      if person_location_index < min_location_index:
        min_location_index = person_location_index
    if min_location_index < location_index:
      return False
    return True


  def is_any_person_inside_location(self, location):
    locations = LOCATIONS[::-1]
    if location not in locations:
      return False
    location_index = locations.index(location)
    min_location_index = 999
    for _, person in PERSONS.items():
      person_name = person["name"]
      entity = f"input_select.{person_name}_location"
      if not self.entity_exists(entity):
        continue
      person_location = self.get_state(entity)
      person_location_index = locations.index(person_location)
      if person_location_index < min_location_index:
        min_location_index = person_location_index
    if min_location_index > location_index:
      return False
    return True


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
      entity = f"person.{person_name}"
      if self.entity_exists(entity) and self.get_state(entity) == "home":
        persons_at_home.append(person)
    return persons_at_home


  def get_admin_persons(self):
    admin_persons = []
    for _, person in PERSONS.items():
      if person["admin"]:
        admin_persons.append(person)
    return admin_persons


  def __get_proximity(self, person_name):
    entity = f"proximity.ha_{person_name}_home"
    if not self.entity_exists(entity):
      return None
    try:
      proximity = float(self.get_state(entity))
      return proximity
    except ValueError:
      return 0
