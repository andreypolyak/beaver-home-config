from base import Base


class Weight(Base):

  def initialize(self):
    super().initialize()
    default = {
      "current_weight": 0,
      "current_weight_ts": 0,
      "prev_weight": 0,
      "prev_weight_ts": 0,
      "last_reported_ts": 0
    }
    for person_name in self.get_person_names():
      self.init_storage("weight", person_name, default)
    default = {
      "changed_ts": 0,
      "weight": 0
    }
    self.init_storage("weight", "last", default)
    self.listen_event(self.on_scales_change, "esphome.weight")


  def on_scales_change(self, event_name, data, kwargs):
    last = person_state = self.read_storage("last", attribute="all")
    weight = round(float(data["weight"]), 2)
    if weight < 10:
      return
    if last["weight"] == weight and self.get_delta_ts(last["changed_ts"]) > 1200:
      return
    last = {
      "changed_ts": self.get_now_ts(),
      "weight": weight
    }
    self.write_storage("last", last, attribute="all")
    person = self.identify_person(weight)
    person_name = person["name"]
    person_phone = person["phone"]
    person_state = self.read_storage(person_name, attribute="all")
    if person_state["current_weight"] == weight and self.get_delta_ts(person_state["last_reported_ts"]) < 1200:
      return
    self.set_value(f"input_number.{person_name}_weight", weight)
    (voice_message, message) = self.build_messages(person, weight)
    if person_phone:
      self.send_push(person_name, message, "weight", sound="Calypso.caf", url=self.build_url(weight))
    if self.sleeping_scene != "night":
      self.fire_event("yandex_speak_text", text=voice_message, room="bedroom")


  def identify_person(self, weight):
    weight_delta = 9999
    selected_person = None
    for person in self.get_persons():
      person_name = person["name"]
      person_weight = self.get_float_state(f"input_number.{person_name}_weight")
      if abs(person_weight - weight) < weight_delta:
        weight_delta = abs(person_weight - weight)
        selected_person = person
    return selected_person


  def build_messages(self, person, weight):
    person_name = person["name"]
    person_name_ru = person["ru_name"]
    person_state = self.read_storage(person_name, attribute="all")
    if self.get_delta_ts(person_state["current_weight_ts"]) > 600 or person_state["prev_weight"] == 0:
      person_state = {
        "current_weight": weight,
        "current_weight_ts": self.get_now_ts(),
        "prev_weight": person_state["current_weight"],
        "prev_weight_ts": person_state["current_weight_ts"],
        "last_reported_ts": self.get_now_ts()
      }
    else:
      person_state = {
        "current_weight": weight,
        "current_weight_ts": self.get_now_ts(),
        "prev_weight": person_state["prev_weight"],
        "prev_weight_ts": person_state["prev_weight_ts"],
        "last_reported_ts": self.get_now_ts()
      }
    self.write_storage(person_name, person_state, attribute="all")
    weight_change = (person_state["current_weight"] - person_state["prev_weight"]) * 1000
    weight_change = int(5 * round(weight_change / 5))
    weight_ts_change = person_state["current_weight_ts"] - person_state["prev_weight_ts"]
    voice_message = f"{person_name_ru} весит {weight} килограмм"
    message = f"⚖️ Weight: {weight} kg"
    if person_state["prev_weight"] != 0:
      voice_message += ". Вы "
      message += ". ("
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
        periods = round(weight_ts_change / 86400)
        text_ru = self.morph_periods(periods, "day", "ru")
        text_en = self.morph_periods(periods, "day", "en")
      elif weight_ts_change > 3600:
        periods = round(weight_ts_change / 3600)
        text_ru = self.morph_periods(periods, "hour", "ru")
        text_en = self.morph_periods(periods, "hour", "en")
      else:
        periods = round(weight_ts_change / 60)
        text_ru = self.morph_periods(periods, "minute", "ru")
        text_en = self.morph_periods(periods, "minute", "en")
      voice_message += f"{periods} {text_ru} назад"
      message += f"{periods} {text_en} ago)"
    if person["phone"]:
      voice_message += ". Не забудьте нажать на уведомление, чтобы сохранить вес в Apple Health"
      message += ". Click to save in Apple Health"
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


  def build_url(self, weight):
    weight = str(weight).replace(".", ",")
    url = f"shortcuts://run-shortcut?name=Weight&input={weight}"
    return url
