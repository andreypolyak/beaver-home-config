from base import Base


class WelcomeAnnouncement(Base):

  def initialize(self):
    super().initialize()
    self.scene_change_ts = 0
    self.listen_state(self.on_scene_change, "input_select.living_scene", old="away")
    self.listen_state(self.on_door_open, "binary_sensor.entrance_door", new="on", old="off")


  def on_scene_change(self, entity, attribute, old, new, kwargs):
    self.scene_change_ts = self.get_now_ts()


  def on_door_open(self, entity, attribute, old, new, kwargs):
    if self.get_delta_ts(self.scene_change_ts) < 600 or self.get_living_scene() == "away":
      self.run_in(self.notify, 5)
      self.scene_change_ts = 0


  def notify(self, kwargs):
    washing_done = self.get_state("input_select.washing_machine_status") == "full"
    vacuum_state = self.get_state("input_select.vacuum_state")
    hour = int(self.datetime().strftime("%H"))
    minute = self.datetime().strftime("%M")
    text = ""
    if hour < 4:
      text += "Доброй ночи!"
    elif hour >= 4 and hour < 12:
      text += "Доброе утро!"
    elif hour >= 12 and hour < 18:
      text += "Добрый день!"
    elif hour >= 18:
      text += "Добрый вечер!"
    text += f" Сейчас {str(hour)}:{minute}."
    if washing_done and vacuum_state == "cleaning":
      text += " Пылесос до сих пор убирается. Не забудьте разобрать бельё в стиральной машине"
    elif washing_done and vacuum_state in ["done_charging", "done_waiting"]:
      text += " Не забудьте разобрать бельё в стиральной машине и очистить контейнер пылесоса."
    elif washing_done and vacuum_state == "error":
      text += " Не забудьте разобрать бельё в стиральной машине и проверить что с пылесосом."
    elif washing_done:
      text += " Не забудьте разобрать бельё в стиральной машине."
    elif vacuum_state == "cleaning":
      text += " Пылесос до сих пор убирается."
    elif vacuum_state in ["done_charging", "done_waiting"]:
      text += " Не забудьте очистить контейнер пылесоса."
    elif vacuum_state == "error":
      text += " Не забудьте проверить что с пылесосом."
    self.fire_event("yandex_speak_text", text=text, room="living_room")
