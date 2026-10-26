# Kyndryl Weather Dashboard

A small Flask web app for looking up a city's current weather. It uses the Open-Meteo Geocoding and Forecast APIs, so no API key is required.

Welcome team
## Features

- Search for weather by city name.
- View current temperature, conditions, humidity, and wind speed.
- Uses Open-Meteo to look up locations and retrieve weather data.
- Responsive dashboard with loading and error states.

## Requirements

- Python 3.8 or later
- Internet access to reach the Open-Meteo APIs

## Run locally

From the project directory, create and activate a virtual environment, then install the dependencies:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.

Start the development server:

```sh
flask --app app run
```

Open <http://127.0.0.1:5000> and search for a city.

## Weather endpoint

The app fetches weather through `GET /weather` with a city query parameter:

```text
/weather?city=Copenhagen
```

Successful requests return JSON containing the matched city, current conditions, and forecast data. Invalid city input, an unknown city, or an unavailable provider returns an appropriate HTTP error and a JSON `error` message.

## Tests

Run the test suite with Python's built-in unittest runner:

```sh
python -m unittest discover -s tests
```


