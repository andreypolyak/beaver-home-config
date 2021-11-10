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


  def get_persons(self, person_name=None, except_person_name=None, entity=None, admin=False, location=None,
                  with_phone=False, with_alarm=False, with_location=False):
    persons = []
    if person_name is not None:
      persons.append(PERSONS[person_name])
    elif except_person_name is not None:
      for current_person_name, current_person in PERSONS.items():
        if current_person_name != except_person_name:
          persons.append(current_person)
    elif entity is not None:
      for current_person_name, current_person in PERSONS.items():
        if current_person_name in entity:
          persons.append(current_person)
    elif admin:
      for current_person_name, current_person in PERSONS.items():
        if current_person["admin"]:
          persons.append(current_person)
    elif location is not None:
      if isinstance(location, str):
        location_list = [location]
      else:
        location_list = location
      for current_person_name, current_person in PERSONS.items():
        entity = f"input_select.{current_person_name}_location"
        for specific_location in location_list:
          if self.entity_exists(entity) and self.get_state(entity) == specific_location:
            persons.append(current_person)
    else:
      for current_person_name, current_person in PERSONS.items():
        persons.append(current_person)
    filtered_persons = []
    for person in persons:
      person_name = person["name"]
      if with_phone and person["phone"] is None:
        continue
      if with_alarm and not self.entity_exists(f"input_boolean.alarm_{person_name}"):
        continue
      if with_location and not self.entity_exists(f"input_select.{person_name}_location"):
        continue
      filtered_persons.append(person)
    return filtered_persons


  def get_person_names(self, except_person_name=None, entity=None, admin=False, location=None,
                       with_phone=False, with_alarm=False, with_location=False):
    persons = self.get_persons(person_name=None, except_person_name=except_person_name, entity=entity, admin=admin,
                               location=location, with_phone=with_phone, with_alarm=with_alarm,
                               with_location=with_location)
    person_names = []
    for person in persons:
      person_names.append(person["name"])
    return person_names


  def get_person_locations(self):
    location_entities = []
    for person_name in self.get_person_names(with_location=True):
      location_entities.append(f"input_select.{person_name}_location")
    return location_entities
