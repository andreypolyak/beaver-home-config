from base import Base

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
    "ru_name": "Теодор",
    "phone": None,
    "admin": False,
    "emoji": "👦"
  }
}


class Persons(Base):

  def initialize(self):
    super().initialize()


  def get_all_persons(self, with_phone=False, with_alarm=False, with_location=False, location=None):
    persons = []
    for _, person in PERSONS.items():
      person_name = person["name"]
      if with_phone and person["phone"] is None:
        continue
      if with_alarm and not self.entity_exists(f"input_boolean.alarm_{person_name}"):
        continue
      if with_location and not self.entity_exists(f"input_select.{person_name}_location"):
        continue
      persons.append(person)
    return persons


  def get_all_person_names(self, with_phone=False, with_alarm=False, with_location=False):
    person_names = []
    for _, person in PERSONS.items():
      person_name = person["name"]
      if with_phone and person["phone"] is None:
        continue
      if with_alarm and not self.entity_exists(f"input_boolean.alarm_{person_name}"):
        continue
      if with_location and not self.entity_exists(f"input_select.{person_name}_location"):
        continue
      person_names.append(person_name)
    return person_names


  def get_all_person_location_entities(self):
    location_entities = []
    for person_name in self.get_all_person_names(with_location=True):
      location_entities.append(f"input_select.{person_name}_location")
    return location_entities


  def get_all_person_names_except_provided(self, person_name, with_phone=False, with_alarm=False, with_location=False):
    provided_person_name = person_name
    person_names = []
    for _, person in PERSONS.items():
      person_name = person["name"]
      if person_name != provided_person_name:
        if with_phone and person["phone"] is None:
          continue
        if with_alarm and not self.entity_exists(f"input_boolean.alarm_{person_name}"):
          continue
        if with_location and not self.entity_exists(f"input_select.{person_name}_location"):
          continue
        person_names.append(person_name)
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


  def get_all_person_names_with_location(self, location):
    person_names = []
    for _, person in PERSONS.items():
      person_name = person["name"]
      entity = f"input_select.{person_name}_location"
      if self.entity_exists(entity) and self.get_state(entity) == location:
        person_names.append(person["name"])
    return person_names


  def get_admin_persons(self):
    admin_persons = []
    for _, person in PERSONS.items():
      if person["admin"]:
        admin_persons.append(person)
    return admin_persons
