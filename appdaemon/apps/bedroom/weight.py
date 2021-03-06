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
    last = self.read_storage("last", attribute="all")
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
    old_person_state = self.read_storage(person_name, attribute="all")
    if old_person_state["current_weight"] == weight and self.get_delta_ts(old_person_state["last_reported_ts"]) < 1200:
      return
    self.set_value(f"input_number.{person_name}_weight", weight)
    new_person_state = self.build_person_state(person_name, weight)
    self.write_storage(person_name, new_person_state, attribute="all")
    (voice_message, message) = self.build_messages(person, new_person_state)
    if person["phone"]:
      self.send_push(person_name, message, "weight", sound="Calypso.caf", url=self.build_url(weight))
    if self.sleeping_scene != "night":
      self.fire_event("yandex_speak_text", text=voice_message, room="bedroom")


  def build_person_state(self, person_name, weight):
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
    return person_state


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


  def build_messages(self, person, person_state):
    weight = person_state["current_weight"]
    prev_weight = person_state["prev_weight"]
    weight_change = (person_state["current_weight"] - person_state["prev_weight"]) * 1000
    weight_change = int(5 * round(weight_change / 5))
    weight_ts_change = person_state["current_weight_ts"] - person_state["prev_weight_ts"]
    person_ru_name = person["ru_name"]
    voice_message = f"{person_ru_name} ?????????? {weight} ??????????????????"
    message = f"?????? Weight: {weight} kg"
    if prev_weight:
      voice_message += ". ???? "
      message += ". ("
      if weight_change < 0:
        voice_message += f"???????????????? ???? {abs(weight_change)} ?????????? "
        message += f"-{abs(weight_change)} g. "
      elif weight_change > 0:
        voice_message += f"?????????????????????? ???? {abs(weight_change)} ?????????? "
        message += f"+{abs(weight_change)} g. "
      else:
        voice_message += "???? ???????????????????? ?? ???????? "
        message += "+0 g. "
      voice_message += "?? ?????????????? ???????????????????? ?????????????????????? "
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
      voice_message += f"{periods} {text_ru} ??????????"
      message += f"{periods} {text_en} ago)"
    if person["phone"]:
      voice_message += ". ???? ???????????????? ???????????? ???? ??????????????????????, ?????????? ?????????????????? ?????? ?? Apple Health"
      message += ". Click to save in Apple Health"
    return (voice_message, message)


  def morph_periods(self, period, period_type, language):
    if language == "ru":
      if period >= 10 and period <= 14:
        if period_type == "day":
          return "????????"
        elif period_type == "hour":
          return "??????????"
        elif period_type == "minute":
          return "??????????"
      elif period % 10 == 1:
        if period_type == "day":
          return "????????"
        elif period_type == "hour":
          return "??????"
        elif period_type == "minute":
          return "????????????"
      elif period % 10 >= 2 and period % 10 <= 4:
        if period_type == "day":
          return "??????"
        elif period_type == "hour":
          return "????????"
        elif period_type == "minute":
          return "????????????"
      if period_type == "day":
        return "????????"
      elif period_type == "hour":
        return "??????????"
      elif period_type == "minute":
        return "??????????"
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
