import appdaemon.plugins.hass.hassapi as hass


class Notifications(hass.Hass):

  def initialize(self):
    self.storage = self.get_app("persistent_storage")
    self.persons = self.get_app("persons")
    for person in self.persons.get_all_persons():
      person_name = person["name"]
      self.storage.init(f"notifications.{person_name}", {})
    self.storage.init(f"notifications.failed_notifications", {})
    self.last_mobile_app_error_ts = 0
    self.run_every(self.__process_failed_notifications, "now+60", 60)
    self.listen_event(self.__on_ha_log, "system_log_event")


  def send(self, to, message, category, sound="none", is_critical=False, min_delta=None,
           max_proximity=None, url=None, ios_category=None, actions=None):
    persons = self.__get_person_list(to, max_proximity)
    for person in persons:
      person_name = person["name"]
      if person["phone"] is None:
        continue
      if min_delta:
        delta = self.__get_notification_ts_delta(person_name, category)
        if (delta and delta < min_delta):
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


  def __process_failed_notifications(self, kwargs):
    failed_notifications = self.storage.read("notifications.failed_notifications", attribute="all")
    for attribute, params in failed_notifications.items():
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
      failed_notifications = self.storage.read("notifications.failed_notifications", attribute="all")
      try:
        del failed_notifications[attribute]
      except KeyError:
        pass
      self.storage.write("notifications.failed_notifications", failed_notifications, attribute="all")
      self.log(f"Succesfully sent notification with params: {params}")
    else:
      self.log(f"Failed to send notification with params: {params}")
      self.storage.write("notifications.failed_notifications", params, attribute=attribute)


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
      self.call_service("input_text/set_value", entity_id="input_text.last_notification", value="")
    self.call_service("input_text/set_value", entity_id="input_text.last_notification", value=sensor_message)
    self.storage.write(f"notifications.{person_name}", self.get_now_ts(), attribute=category)


  def __get_person_list(self, to, max_proximity):
    all_persons = self.persons.get_all_persons()
    persons = []
    if isinstance(to, list):
      for person_name in to:
        if person_name in all_persons:
          persons.append(all_persons[person_name])
    elif to == "admin":
      persons = self.persons.get_admin_persons()
    elif to == "home_or_all":
      persons_at_home = self.__get_persons_at_home()
      if len(persons_at_home) > 0:
        persons = persons_at_home
      else:
        persons = self.persons.get_all_persons()
    elif to == "home_or_none":
      persons_at_home = self.persons.get_persons_at_home()
      if len(persons_at_home) > 0:
        persons = persons_at_home
    elif to == "proximity" and max_proximity:
      persons = self.persons.get_persons_inside_proximity(max_proximity)
    elif isinstance(to, str):
      if to in all_persons:
        persons.append(all_persons[to])
    return persons


  def __get_notification_ts_delta(self, person_name, category):
    category_ts = self.storage.read(f"notifications.{person_name}", attribute=category)
    if category_ts:
      delta = self.get_now_ts() - category_ts
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
