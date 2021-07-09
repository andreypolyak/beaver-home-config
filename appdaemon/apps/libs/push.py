from base import Base


class Push(Base):

  def initialize(self):
    super().initialize()
    for person in self.get_all_persons(with_phone=True):
      person_name = person["name"]
      self.init_storage("push", person_name, {})
    self.init_storage("push", "failed", {})
    self.last_mobile_app_error_ts = 0
    self.run_every(self.__process_failed, "now+60", 60)
    self.listen_event(self.__on_ha_log, "system_log_event")


  def send(self, to, message, category, sound="none", is_critical=False, min_delta=None,
           url=None, ios_category=None, actions=None):
    persons = self.__get_person_list(to)
    for person in persons:
      person_name = person["name"]
      if min_delta:
        delta = self.__get_notification_ts_delta(person_name, category)
        if delta and delta < min_delta:
          continue
      if ios_category:
        category = ios_category
      params = {
        "person_name": person_name,
        "person_phone": person["phone"],
        "message": message,
        "category": category,
        "sound": sound,
        "is_critical": is_critical,
        "url": url,
        "actions": actions
      }
      self.__process_notification(params)


  def __on_ha_log(self, event_name, data, kwargs):
    if (
      "name" in data
      and data["name"] == "homeassistant.components.mobile_app.notify"
      and "level" in data
      and data["level"] == "ERROR"
    ):
      self.last_mobile_app_error_ts = self.get_now_ts()


  def __process_failed(self, kwargs):
    failed = self.read_storage("failed", attribute="all")
    for attribute, params in failed.items():
      self.log(f"Trying to resend notification with params: {params}")
      self.__process_notification(params)


  def __process_notification(self, params):
    person_name = params["person_name"]
    category = params["category"]
    attribute = f"{category}_{person_name}"
    res = self.__send_push_notification(params)
    if res:
      self.__send_telegram_notification(params)
      self.__update_ha_sensor(params)
      failed = self.read_storage("failed", attribute="all")
      try:
        del failed[attribute]
      except KeyError:
        pass
      self.log(f"Succesfully sent notification with params: {params}")
      self.write_storage("failed", failed, attribute="all")
    else:
      self.log(f"Failed to send notification with params: {params}")
      self.write_storage("failed", params, attribute=attribute)


  def __send_push_notification(self, params):
    ha_notification_properties = self.__build_push_notification_properties(params)
    person_phone = params["person_phone"]
    message = params["message"]
    tries = 2
    for i in range(tries):
      start_ts = self.get_now_ts()
      is_error = False
      try:
        self.call_service(f"notify/mobile_app_{person_phone}", message=message, data=ha_notification_properties)
      except:
        is_error = True
      finish_ts = self.get_now_ts()
      if is_error or (finish_ts - start_ts) > 10 or (finish_ts > self.last_mobile_app_error_ts > start_ts):
        if i < tries - 1:
          continue
        else:
          self.log(f"Failed to send notification with params: {params}")
          return False
      return True


  def __send_telegram_notification(self, params):
    person_name = params["person_name"]
    message = params["message"]
    telegram_name = person_name.capitalize()
    telegram_message = f"{telegram_name} → {message}"
    try:
      self.call_service("telegram_bot/send_message", message=telegram_message, target=self.args["chat_id"])
    except:
      pass


  def __update_ha_sensor(self, params):
    person_name = params["person_name"]
    message = params["message"]
    category = params["category"]
    sensor_name = person_name.capitalize()[0]
    sensor_message = f"\"{sensor_name}→{message}\""[:99]
    if self.get_state("input_text.last_notification") == sensor_message:
      self.set_value("input_text.last_notification", "")
    self.set_value("input_text.last_notification", sensor_message)
    self.write_storage(person_name, self.get_now_ts(), attribute=category)


  def __get_person_list(self, to):
    all_persons = self.get_all_persons(with_location=True)
    persons = []
    if isinstance(to, list):
      for person_name in to:
        if person_name in all_persons:
          persons.append(all_persons[person_name])
    elif to == "admin":
      persons = self.get_admin_persons()
    elif to == "home_or_all":
      persons_at_home = self.get_all_person_names_with_location("home")
      if len(persons_at_home) > 0:
        persons = persons_at_home
      else:
        persons = self.get_all_persons(with_location=True)
    elif to == "home_or_none":
      persons_at_home = self.get_all_person_names_with_location("home")
      if len(persons_at_home) > 0:
        persons = persons_at_home
    elif isinstance(to, str):
      for person in all_persons:
        if to == person["name"]:
          persons.append(person)
    return persons


  def __get_notification_ts_delta(self, person_name, category):
    category_ts = self.read_storage(person_name, attribute=category)
    if category_ts:
      delta = self.get_delta_ts(category_ts)
      return delta
    return


  def __build_push_notification_properties(self, params):
    properties = {
      "action_data": {"person_name": params["person_name"]},
      "apns_headers": {"apns-collapse-id": params["category"]},
      "push": {"sound": params["sound"]}
    }
    if params["is_critical"]:
      properties["push"]["sound"] = {"name": "default", "critical": 1, "volume": 1.0}
    for param in ["url", "actions"]:
      if params[param]:
        properties[param] = params[param]
    return properties
