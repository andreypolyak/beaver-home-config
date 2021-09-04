from base import Base


class Forecast(Base):

  def initialize(self):
    super().initialize()


  def get_forecast(self, current_time=False):
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
    if current_time:
      text += f" Сейчас {hour}:{minute}."
    weather = self.get_state("weather.home_hourly", attribute="all")
    current_temp = round(weather["attributes"]["temperature"])
    current_temp_degrees = self.__morph_degrees(current_temp)
    text += f" За окном {current_temp} {current_temp_degrees}."
    min_temp = 9999
    max_temp = -9999
    will_rain = False
    will_snow = False
    will_sun = False
    for forecast in weather["attributes"]["forecast"][:12]:
      if forecast["temperature"] < min_temp:
        min_temp = round(forecast["temperature"])
      if forecast["temperature"] > max_temp:
        max_temp = round(forecast["temperature"])
      if "rainy" in forecast["condition"]:
        will_rain = True
      if "snowy" in forecast["condition"]:
        will_snow = True
      if "sunny" in forecast["condition"]:
        will_sun = True
    if min_temp != max_temp:
      max_temp_degrees = self.__morph_degrees_range(max_temp)
      text += f" Сегодня будет от {min_temp} до {max_temp} {max_temp_degrees}."
    else:
      min_temp_degrees = self.__morph_degrees(min_temp)
      text += f" Сегодня будет {min_temp} {min_temp_degrees}."
    if will_snow:
      text += " Возможен снег"
      emoji = "🌨️"
    elif will_rain:
      text += " Возможен дождь"
      emoji = "🌧️"
    elif will_sun:
      text += " Осадки не ожидаются"
      emoji = "☀️"
    else:
      text += " Осадки не ожидаются"
      emoji = "☁️"
    return (text, emoji)


  def __morph_degrees(self, temp):
    abs_temp = abs(temp)
    if abs_temp >= 10 and abs_temp <= 14:
      return "градусов"
    elif abs_temp % 10 == 1:
      return "градус"
    elif abs_temp % 10 >= 2 and abs_temp % 10 <= 4:
      return "градуса"
    return "градусов"


  def __morph_degrees_range(self, temp):
    abs_temp = abs(temp)
    if abs_temp % 10 == 1:
      return "градуса"
    return "градусов"
