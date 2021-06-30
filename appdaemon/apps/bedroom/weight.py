import appdaemon.plugins.hass.hassapi as hass


class Weight(hass.Hass):

  def initialize(self):
    self.storage = self.get_app("persistent_storage")
    self.persons = self.get_app("persons")
    self.notifications = self.get_app("notifications")
    default = {
      "current_weight": 0,
      "current_weight_ts": 0,
      "prev_weight": 0,
      "prev_weight_ts": 0
    }
    for person in self.persons.get_all_persons():
      person_name = person["name"]
      self.storage.init(f"weight.{person_name}", default)
    self.listen_state(self.on_scales_change, "sensor.scales")
    self.listen_state(self.on_scales_change, "sensor.scales_theo")
    self.listen_state(self.on_weight_change, "input_number.weight")


  def on_scales_change(self, entity, attribute, old, new, kwargs):
    try:
      weight = float(new)
    except ValueError:
      return
    self.call_service("input_number/set_value", entity_id="input_number.weight", value=weight)


  def on_weight_change(self, entity, attribute, old, new, kwargs):
    if new in ["unavailable", "unknown", "None"] or old in ["unavailable", "unknown", "None"]:
      return
    try:
      weight = float(new)
    except ValueError:
      return
    if weight < 10:
      return
    person = self.identify_person(weight)
    person_name = person["name"]
    person_phone = person["phone"]
    self.call_service("input_number/set_value", entity_id=f"input_number.{person_name}_weight", value=weight)
    (voice_message, message) = self.build_messages(person, weight)
    if person_phone:
      weight = str(weight).replace(".", ",")
      url = f"shortcuts://run-shortcut?name=Weight&input={weight}"
      self.notifications.send(person_name, message, "weight", sound="Calypso.caf", url=url)
    if self.get_state("input_select.sleeping_scene") != "night":
      self.fire_event("yandex_speak_text", text=voice_message, room="bedroom")


  def identify_person(self, weight):
    weight_delta = 9999
    selected_person = None
    for person in self.persons.get_all_persons():
      person_name = person["name"]
      person_weight = float(self.get_state(f"input_number.{person_name}_weight"))
      if abs(person_weight - weight) < weight_delta:
        weight_delta = abs(person_weight - weight)
        selected_person = person
    return selected_person


  def build_messages(self, person, weight):
    person_name = person["name"]
    person_name_ru = person["ru_name"]
    person_state = self.storage.read(f"weight.{person_name}", attribute="all")
    if (self.get_now_ts() - person_state["current_weight_ts"]) > 600:
      person_state = {
        "current_weight": weight,
        "current_weight_ts": self.get_now_ts(),
        "prev_weight": person_state["current_weight"],
        "prev_weight_ts": person_state["current_weight_ts"]
      }
    else:
      person_state = {
        "current_weight": weight,
        "current_weight_ts": self.get_now_ts(),
        "prev_weight": person_state["prev_weight"],
        "prev_weight_ts": person_state["prev_weight_ts"]
      }
    self.storage.write(f"weight.{person_name}", person_state, attribute="all")
    weight_change = (person_state["current_weight"] - person_state["prev_weight"]) * 1000
    weight_change = int(5 * round(weight_change / 5))
    weight_ts_change = person_state["current_weight_ts"] - person_state["prev_weight_ts"]
    voice_message = f"{person_name_ru} весит {weight} килограмм. Вы "
    message = f"⚖️ Weight: {weight} kg. ("
    if weight_change < 0:
      voice_message += f"похудели на {abs(weight_change)} грамм "
      message += f"-{abs(weight_change)} g. "
    elif weight_change > 0:
      voice_message += f"поправились на {abs(weight_change)} грамм "
      message += f"+{abs(weight_change)} g. "
    else:
      voice_message += "не изменились в весе "
      message += "+0 g. "
    voice_message += "с момента последнего взвешивания "
    message += "vs. "
    if weight_ts_change > 86400:
      days = round(weight_ts_change / 86400)
      days_text_ru = self.morph_periods(days, "day", "ru")
      days_text_en = self.morph_periods(days, "day", "en")
      voice_message += f"{days} {days_text_ru} назад"
      message += f"{days} {days_text_en} ago"
    elif weight_ts_change > 3600:
      hours = round(weight_ts_change / 3600)
      hours_text_ru = self.morph_periods(hours, "hour", "ru")
      hours_text_en = self.morph_periods(hours, "hour", "en")
      voice_message += f"{hours} {hours_text_ru} назад"
      message += f"{hours} {hours_text_en} ago"
    else:
      minutes = round(weight_ts_change / 60)
      minutes_text_ru = self.morph_periods(minutes, "minute", "ru")
      minutes_text_en = self.morph_periods(minutes, "minute", "en")
      voice_message += f"{minutes} {minutes_text_ru} назад"
      message += f"{minutes} {minutes_text_en} ago"
    if person["phone"]:
      voice_message += ". Не забудьте нажать на уведомление, чтобы сохранить вес в Apple Health"
      message += "). Click to save in Apple Health"
    return (voice_message, message)


  def morph_periods(self, period, period_type, language):
    if language == "ru":
      if period >= 10 and period <= 14:
        if period_type == "day":
          return "дней"
        elif period_type == "hour":
          return "часов"
        elif period_type == "minute":
          return "минут"
      elif period % 10 == 1:
        if period_type == "day":
          return "день"
        elif period_type == "hour":
          return "час"
        elif period_type == "minute":
          return "минуту"
      elif period % 10 >= 2 and period % 10 <= 4:
        if period_type == "day":
          return "дня"
        elif period_type == "hour":
          return "часа"
        elif period_type == "minute":
          return "минуты"
      if period_type == "day":
        return "дней"
      elif period_type == "hour":
        return "часов"
      elif period_type == "minute":
        return "минут"
    elif language == "en":
      if period == 1:
        if period_type == "day":
          return "day"
        elif period_type == "hour":
          return "hour"
        elif period_type == "minute":
          return "minute"
      else:
        if period_type == "day":
          return "days"
        elif period_type == "hour":
          return "hours"
        elif period_type == "minute":
          return "minutes"
    return None
