import appdaemon.plugins.hass.hassapi as hass

ROOMS = ["bedroom", "living_room"]
ACTIVATION_COMMAND = "Скажи Афоне арбуз"


class YandexDialog(hass.Hass):

  def dialog_init(self):
    self.run_ts = 0
    self.step = None
    self.set_inactive_dialog()
    self.room = None
    self.listen_event(self.on_yandex_intent, self.dialog_name)


  def start_dialog(self, step, room=None):
    if self.get_now_ts() - self.run_ts <= 5:
      return
    else:
      self.run_ts = self.get_now_ts()
    self.step = step
    if room:
      self.call_service("input_select/select_option", entity_id="input_select.last_active_yandex_station", option=room)
      self.room = room
    else:
      self.room = self.get_state("input_select.last_active_yandex_station")
    self.set_active_dialog()
    data = {
      "media_entity_id": f"media_player.{self.room}_yandex_station",
      "media_content_id": ACTIVATION_COMMAND,
      "media_content_type": "command"
    }
    self.call_service("script/turn_on", entity_id="script.yandex_play_media", variables=data)


  def continue_dialog(self, text, step):
    self.fire_event("yandex_intent_response", text=text, end_session=False)
    self.step = step


  def finish_dialog(self, text):
    self.fire_event("yandex_intent_response", text=text, end_session=True)
    self.set_inactive_dialog()
    self.step = None
    self.room = None


  def cancel_dialog(self):
    self.log("Cancelling dialog")
    self.fire_event("yandex_intent_response", text="", end_session=True)
    self.call_service("media_player/turn_off", entity_id=f"media_player.{self.room}_yandex_station")
    self.set_inactive_dialog()
    self.step = None
    self.room = None


  def set_active_dialog(self):
    self.call_service("input_text/set_value", entity_id="input_text.active_dialog", value=self.dialog_name)


  def set_inactive_dialog(self):
    self.call_service("input_text/set_value", entity_id="input_text.active_dialog", value="")
