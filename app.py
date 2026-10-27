import logging

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = (3.05, 10)

WEATHER_CODES = {
	0: "Clear sky",
	1: "Mainly clear",
	2: "Partly cloudy",
	3: "Overcast",
	45: "Fog",
	48: "Depositing rime fog",
	51: "Light drizzle",
	53: "Moderate drizzle",
	55: "Dense drizzle",
	56: "Light freezing drizzle",
	57: "Dense freezing drizzle",
	61: "Slight rain",
	63: "Moderate rain",
	65: "Heavy rain",
	66: "Light freezing rain",
	67: "Heavy freezing rain",
	71: "Slight snowfall",
	73: "Moderate snowfall",
	75: "Heavy snowfall",
	77: "Snow grains",
	80: "Slight rain showers",
	81: "Moderate rain showers",
	82: "Violent rain showers",
	85: "Slight snow showers",
	86: "Heavy snow showers",
	95: "Thunderstorm",
	96: "Thunderstorm with slight hail",
	99: "Thunderstorm with heavy hail",
}


def fetch_json(url, params):
	response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
	response.raise_for_status()
	return response.json()


def describe_weather(code):
	return WEATHER_CODES.get(code, "Unknown conditions")


@app.get("/")
def index():
	return render_template("index.html")


@app.get("/health")
def health():
	return jsonify(status="ok")


@app.get("/ping")
def ping():
	return jsonify(status="ok")


@app.get("/version")
def version():
	return jsonify(version="1.0")


@app.get("/weather")
def weather():
	city = request.args.get("city", "").strip()
	if not city:
		return jsonify(error="Enter a city name."), 400
	if len(city) > 100:
		return jsonify(error="City name must be 100 characters or fewer."), 400

	try:
		geocoding = fetch_json(
			GEOCODING_URL,
			{"name": city, "count": 1, "language": "en", "format": "json"},
		)
		locations = geocoding.get("results") or []
		if not locations:
			return jsonify(error=f"No matching city found for '{city}'."), 404

		location = locations[0]
		forecast = fetch_json(
			FORECAST_URL,
			{
				"latitude": location["latitude"],
				"longitude": location["longitude"],
				"current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m",
				"hourly": "temperature_2m,precipitation_probability,weather_code",
				"daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset",
				"forecast_days": 7,
				"timezone": "auto",
			},
		)

		current = forecast.get("current") or {}
		if not current:
			return jsonify(error="The weather provider returned no current conditions."), 502

		current_units = forecast.get("current_units") or {}
		hourly_units = forecast.get("hourly_units") or {}
		daily_units = forecast.get("daily_units") or {}
		hourly = forecast.get("hourly") or {}
		daily = forecast.get("daily") or {}

		hourly_times = hourly.get("time") or []
		current_time = current.get("time")
		start_index = next(
			(index for index, timestamp in enumerate(hourly_times) if timestamp >= current_time),
			0,
		) if current_time else 0

		hourly_forecast = []
		for index in range(start_index, min(start_index + 24, len(hourly_times))):
			code = (hourly.get("weather_code") or [None] * len(hourly_times))[index]
			hourly_forecast.append(
				{
					"time": hourly_times[index],
					"temperature": (hourly.get("temperature_2m") or [None] * len(hourly_times))[index],
					"precipitation_probability": (hourly.get("precipitation_probability") or [None] * len(hourly_times))[index],
					"condition": describe_weather(code),
				}
			)

		daily_times = daily.get("time") or []
		daily_forecast = []
		for index, date in enumerate(daily_times[:7]):
			code = (daily.get("weather_code") or [None] * len(daily_times))[index]
			daily_forecast.append(
				{
					"date": date,
					"temperature_min": (daily.get("temperature_2m_min") or [None] * len(daily_times))[index],
					"temperature_max": (daily.get("temperature_2m_max") or [None] * len(daily_times))[index],
					"precipitation_probability": (daily.get("precipitation_probability_max") or [None] * len(daily_times))[index],
					"condition": describe_weather(code),
					"sunrise": (daily.get("sunrise") or [None] * len(daily_times))[index],
					"sunset": (daily.get("sunset") or [None] * len(daily_times))[index],
				}
			)

		return jsonify(
			city=location.get("name", city),
			country=location.get("country"),
			location={
				"name": location.get("name", city),
				"country": location.get("country"),
				"latitude": location["latitude"],
				"longitude": location["longitude"],
			},
			timezone=forecast.get("timezone"),
			current={
				"time": current.get("time"),
				"temperature": current.get("temperature_2m"),
				"temperature_unit": current_units.get("temperature_2m", "°C"),
				"apparent_temperature": current.get("apparent_temperature"),
				"humidity": current.get("relative_humidity_2m"),
				"precipitation": current.get("precipitation"),
				"condition": describe_weather(current.get("weather_code")),
				"is_day": current.get("is_day"),
				"wind_speed": current.get("wind_speed_10m"),
				"wind_speed_unit": current_units.get("wind_speed_10m"),
			},
			hourly=hourly_forecast,
			hourly_units={
				"temperature": hourly_units.get("temperature_2m"),
				"precipitation_probability": hourly_units.get("precipitation_probability"),
			},
			daily=daily_forecast,
			daily_units={
				"temperature": daily_units.get("temperature_2m_max"),
				"precipitation_probability": daily_units.get("precipitation_probability_max"),
			},
		)
	except (requests.RequestException, ValueError, KeyError, TypeError, IndexError):
		logging.exception("Weather provider request failed")
		return jsonify(error="Weather data is temporarily unavailable. Please try again."), 502


if __name__ == "__main__":
	app.run(debug=True)
