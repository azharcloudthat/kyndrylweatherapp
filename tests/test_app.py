import unittest
from unittest.mock import patch

import app as weather_app


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class WeatherRouteTests(unittest.TestCase):
    def setUp(self):
        weather_app.app.config["TESTING"] = True
        self.client = weather_app.app.test_client()

    def test_missing_city_returns_bad_request(self):
        response = self.client.get("/weather")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"error": "Enter a city name."})

    @patch("app.requests.get")
    def test_unknown_city_returns_not_found(self, mock_get):
        mock_get.return_value = FakeResponse({"results": None})

        response = self.client.get("/weather?city=Nowhere")

        self.assertEqual(response.status_code, 404)
        self.assertIn("No matching city", response.get_json()["error"])
        mock_get.assert_called_once()

    @patch("app.requests.get")
    def test_city_returns_normalized_weather_json(self, mock_get):
        mock_get.side_effect = [
            FakeResponse(
                {
                    "results": [
                        {
                            "name": "Oslo",
                            "country": "Norway",
                            "latitude": 59.91,
                            "longitude": 10.75,
                        }
                    ]
                }
            ),
            FakeResponse(
                {
                    "timezone": "Europe/Oslo",
                    "current": {
                        "time": "2026-10-13T12:00",
                        "temperature_2m": 12.4,
                        "relative_humidity_2m": 68,
                        "apparent_temperature": 10.1,
                        "is_day": 1,
                        "precipitation": 0,
                        "weather_code": 2,
                        "wind_speed_10m": 9.2,
                    },
                    "current_units": {
                        "temperature_2m": "°C",
                        "wind_speed_10m": "km/h",
                    },
                    "hourly": {
                        "time": ["2026-10-13T12:00", "2026-10-13T13:00"],
                        "temperature_2m": [12.4, 13.0],
                        "precipitation_probability": [10, 5],
                        "weather_code": [2, 1],
                    },
                    "hourly_units": {"temperature_2m": "°C"},
                    "daily": {
                        "time": ["2026-10-13"],
                        "temperature_2m_min": [7.1],
                        "temperature_2m_max": [14.3],
                        "precipitation_probability_max": [20],
                        "weather_code": [2],
                        "sunrise": ["2026-10-13T07:32"],
                        "sunset": ["2026-10-13T18:04"],
                    },
                    "daily_units": {"temperature_2m_max": "°C"},
                }
            ),
        ]

        response = self.client.get("/weather?city=Oslo")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["city"], "Oslo")
        self.assertEqual(payload["current"]["temperature"], 12.4)
        self.assertEqual(payload["current"]["condition"], "Partly cloudy")
        self.assertEqual(len(payload["hourly"]), 2)
        self.assertEqual(payload["daily"][0]["temperature_max"], 14.3)
        self.assertEqual(mock_get.call_count, 2)


if __name__ == "__main__":
    unittest.main()