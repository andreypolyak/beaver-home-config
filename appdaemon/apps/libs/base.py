import appdaemon.plugins.hass.hassapi as hass


class Base(hass.Hass):

  def initialize(self):
    self.storage = self.get_app("storage")
    self.persons = self.get_app("persons")
    self.push = self.get_app("push")
    self.storage_namespace = ""


  def convert_entity_to_name(self, entity: str, lower: bool = False):
    name = entity.split(".")[1].replace("_", " ")
    if not lower:
      name = name.title()
    return name


  def convert_name_to_entity(self, entity: str):
    return entity.replace(" ", "_").lower()


  def get_int_state(self, entity: str, attribute=None):
    try:
      if self.entity_exists(entity):
        if attribute is None:
          state = int(float(self.get_state(entity)))
        else:
          state = int(float(self.get_state(entity, attribute=attribute)))
      else:
        state = int(float(entity))
    except (ValueError, TypeError):
      return None
    return state


  def get_float_state(self, entity: str, attribute=None):
    try:
      if self.entity_exists(entity):
        if attribute is None:
          state = float(self.get_state(entity))
        else:
          state = float(self.get_state(entity, attribute=attribute))
      else:
        state = float(entity)
    except (ValueError, TypeError):
      return None
    return state


  def is_entity_on(self, entity: str):
    if self.get_state(entity) == "on":
      return True
    return False


  def is_entity_off(self, entity: str):
    if self.get_state(entity) != "on":
      return True
    return False


  def set_scene(self, zone, scene):
    self.call_service("input_select/select_option", entity_id=f"input_select.{zone}_scene", option=scene)


  def set_living_scene(self, scene):
    self.call_service("input_select/select_option", entity_id="input_select.living_scene", option=scene)


  def set_sleeping_scene(self, scene):
    self.call_service("input_select/select_option", entity_id="input_select.sleeping_scene", option=scene)


  def get_scene(self, zone):
    return self.get_state(f"input_select.{zone}_scene")


  def get_living_scene(self):
    return self.get_state("input_select.living_scene")


  def get_sleeping_scene(self):
    return self.get_state("input_select.sleeping_scene")


  def set_value(self, entity, value):
    domain = entity.split(".")[0]
    self.call_service(f"{domain}/set_value", entity_id=entity, value=value)


  def turn_on_entity(self, entity: str, **kwargs):
    domain = entity.split(".")[0]
    self.call_service(f"{domain}/turn_on", entity_id=entity, **kwargs)


  def turn_off_entity(self, entity, **kwargs):
    domain = entity.split(".")[0]
    self.call_service(f"{domain}/turn_off", entity_id=entity, **kwargs)


  def set_current_datetime(self, entity):
    self.call_service("input_datetime/set_datetime", entity_id=entity, timestamp=self.get_now_ts())


  def set_time(self, entity, time):
    self.call_service("input_datetime/set_datetime", entity_id=entity, time=time)


  def select_option(self, entity, option):
    if "input_select." not in entity:
      entity = f"input_select.{entity}"
    self.call_service("input_select/select_option", entity_id=entity, option=option)


  def set_options(self, entity, options):
    if "input_select." not in entity:
      entity = f"input_select.{entity}"
    self.call_service("input_select/set_options", entity_id=entity, options=options)


  def cancel_handle(self, handle):
    if self.timer_running(handle):
      self.cancel_timer(handle)


  def get_delta_ts(self, ts):
    return self.get_now_ts() - ts


  def get_nearest_person_location(self):
    return self.get_state("input_select.nearest_person_location")


  def timer_start(self, entity, duration):
    if "timer." not in entity:
      entity = f"timer.{entity}"
    self.call_service("timer/start", entity_id=entity, duration=duration)


  def timer_cancel(self, entity):
    if "timer." not in entity:
      entity = f"timer.{entity}"
    self.call_service("timer/cancel", entity_id=entity)


  def is_timer_active(self, entity):
    if "timer." not in entity:
      entity = f"timer.{entity}"
    if self.get_state(entity) == "active":
      return True
    return False


  def media_pause(self, entity):
    if "media_player." not in entity and entity != "all":
      entity = f"media_player.{entity}"
    self.call_service("media_player/media_pause", entity_id=entity)


  def select_source(self, entity, source):
    if "media_player." not in entity and entity != "all":
      entity = f"media_player.{entity}"
    self.call_service("media_player/select_source", entity_id=entity, source=source)


  def repeat_set(self, entity, repeat):
    if "media_player." not in entity and entity != "all":
      entity = f"media_player.{entity}"
    self.call_service("media_player/repeat_set", entity_id=entity, repeat=repeat)


  def volume_set(self, entity, volume_level):
    if "media_player." not in entity and entity != "all":
      entity = f"media_player.{entity}"
    self.call_service("media_player/volume_set", entity_id=entity, volume_level=volume_level)


  def volume_unmute(self, entity):
    if "media_player." not in entity and entity != "all":
      entity = f"media_player.{entity}"
    self.call_service("media_player/volume_mute", entity_id=entity, is_volume_muted=False)


  def set_shuffle(self, entity):
    if "media_player." not in entity and entity != "all":
      entity = f"media_player.{entity}"
    self.call_service("media_player/shuffle_set", entity_id=entity, shuffle=True)


  def play_media(self, entity, media_content_id, media_content_type, **kwargs):
    if "media_player." not in entity and entity != "all":
      entity = f"media_player.{entity}"
    self.call_service("media_player/play_media", entity_id=entity, media_content_type=media_content_type,
                      media_content_id=media_content_id, **kwargs)


  def sonos_unjoin(self, entity):
    if "media_player." not in entity and entity != "all":
      entity = f"media_player.{entity}"
    self.call_service("sonos/unjoin", entity_id=entity)


  def sonos_snapshot(self, entity):
    if "media_player." not in entity and entity != "all":
      entity = f"media_player.{entity}"
    self.call_service("sonos/snapshot", entity_id=entity)


  def sonos_restore(self, entity):
    if "media_player." not in entity and entity != "all":
      entity = f"media_player.{entity}"
    self.call_service("sonos/restore", entity_id=entity)


  def init_storage(self, namespace, entity, default):
    self.storage_namespace = namespace
    entity = f"{namespace}.{entity}"
    self.storage.init(entity, default)


  def read_storage(self, entity, attribute=None):
    entity = f"{self.storage_namespace}.{entity}"
    return self.storage.read(entity, attribute=attribute)


  def write_storage(self, entity, value, attribute=None):
    entity = f"{self.storage_namespace}.{entity}"
    self.storage.write(entity, value, attribute=attribute)


  def send_push(self, *args, **kwargs):
    self.push.send(*args, **kwargs)


  def set_cover_position(self, entity, position):
    if "cover." not in entity:
      entity = f"cover.{entity}"
    self.call_service("cover/set_cover_position", entity_id=entity, position=position)


  def open_cover(self, entity):
    if "cover." not in entity:
      entity = f"cover.{entity}"
    self.call_service("cover/open_cover", entity_id=entity)


  def close_cover(self, entity):
    if "cover." not in entity:
      entity = f"cover.{entity}"
    self.call_service("cover/close_cover", entity_id=entity)


  def stop_cover(self, entity):
    if "cover." not in entity:
      entity = f"cover.{entity}"
    self.call_service("cover/stop_cover", entity_id=entity)


  def is_bad(self, value):
    if value in ["unavailable", "unknown", "None"]:
      return True
    return False
