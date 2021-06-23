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
    self.listen_state(self.on_weight_change, "sensor.scales")


  def on_weight_change(self, entity, attribute, old, new, kwargs):
    if new in ["unavailable", "unknown", "None"] or old in ["unavailable", "unknown", "None"]:
      return
    try:
      weight = float(new)
    except ValueError:
      return
    if weight < 10:
      return
    weight_delta = 9999
    selected_person = None
    for person in self.persons.get_all_persons():
      person_name = person["name"]
      person_weight = float(self.get_state(f"input_number.{person_name}_weight"))
      if abs(person_weight - weight) < weight_delta:
        weight_delta = abs(person_weight - weight)
        selected_person = person
    person_name = selected_person["name"]
    person_name_ru = selected_person["ru_name"]
    self.call_service("input_number/set_value", entity_id=f"input_number.{person_name}_weight", value=weight)
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
    voice_text = f"{person_name_ru} весит {weight} килограмм. Вы "
    push_text = f"⚖️ Weight: {weight} kg. ("
    if weight_change < 0:
      voice_text += f"похудели на {abs(weight_change)} грамм "
      push_text += f"-{abs(weight_change)} g. "
    elif weight_change > 0:
      voice_text += f"поправились на {abs(weight_change)} грамм "
      push_text += f"+{abs(weight_change)} g. "
    else:
      voice_text += "не изменились в весе "
      push_text += "+0 g. "
    voice_text += "с момента последнего взвешивания "
    push_text += "vs. "
    if weight_ts_change > 86400:
      days = round(weight_ts_change / 86400)
      days_text_ru = self.morph_periods(days, "day", "ru")
      days_text_en = self.morph_periods(days, "day", "en")
      voice_text += f"{days} {days_text_ru} назад"
      push_text += f"{days} {days_text_en} ago"
    elif weight_ts_change > 3600:
      hours = round(weight_ts_change / 3600)
      hours_text_ru = self.morph_periods(hours, "hour", "ru")
      hours_text_en = self.morph_periods(hours, "hour", "en")
      voice_text += f"{hours} {hours_text_ru} назад"
      push_text += f"{hours} {hours_text_en} ago"
    else:
      minutes = round(weight_ts_change / 60)
      minutes_text_ru = self.morph_periods(minutes, "minute", "ru")
      minutes_text_en = self.morph_periods(minutes, "minute", "en")
      voice_text += f"{minutes} {minutes_text_ru} назад"
      push_text += f"{minutes} {minutes_text_en} ago"
    if selected_person["phone"]:
      voice_text += ". Не забудьте нажать на уведомление, чтобы сохранить вес в Apple Health"
      push_text += "). Click to save in Apple Health"
      weight = str(weight).replace(".", ",")
      url = f"shortcuts://run-shortcut?name=Weight&input={weight}"
      self.notifications.send(person_name, push_text, "weight", url=url)
    if self.get_state("input_select.sleeping_scene") != "night":
      self.fire_event("yandex_speak_text", text=voice_text, room="bedroom")


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
