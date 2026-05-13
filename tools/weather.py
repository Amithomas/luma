# tools/weather.py

import requests
from config import OPENWEATHER_API_KEY


def get_weather(city):
    print(f"🌤️ Getting weather for: {city}")

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        city_name = data["name"]

        return (
            f"Weather in {city_name}:\n"
            f"Condition: {weather}\n"
            f"Temperature: {temp}°C (feels like {feels_like}°C)\n"
            f"Humidity: {humidity}%"
        )

    except Exception as e:
        return f"Could not get weather: {str(e)}"