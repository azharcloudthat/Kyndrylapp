
import os
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 10


@app.route("/")
def index():
    """Render the Kyndryl Weather dashboard UI."""
    return render_template("index.html")


@app.route("/weather", methods=["GET"])
@app.route("/api/weather", methods=["GET"])
def get_weather():
    """Fetch and return normalized weather data for the requested city."""
    city = request.args.get("city", "").strip()

    if not city:
        return jsonify({"error": "City name is required."}), 400

    if len(city) > 100:
        return jsonify({"error": "City name is too long."}), 400

    try:
        # Step 1: Geocoding lookup to convert city name to coordinates
        geo_params = {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        geo_response = requests.get(GEOCODING_URL, params=geo_params, timeout=REQUEST_TIMEOUT_SECONDS)

        if geo_response.status_code != 200:
            return jsonify({"error": "Failed to reach geocoding service."}), 502

        geo_data = geo_response.json()
        results = geo_data.get("results")

        if not results:
            return jsonify({"error": f"City '{city}' not found."}), 404

        location_info = results[0]
        latitude = location_info.get("latitude")
        longitude = location_info.get("longitude")
        location_name = location_info.get("name", city)
        country = location_info.get("country", "")
        admin1 = location_info.get("admin1", "")

        country_display = f"{admin1}, {country}".strip(", ") if admin1 else country

        # Step 2: Fetch current conditions and 5-day forecast
        forecast_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset",
            "forecast_days": 5,
            "timezone": "auto"
        }
        forecast_response = requests.get(FORECAST_URL, params=forecast_params, timeout=REQUEST_TIMEOUT_SECONDS)

        if forecast_response.status_code != 200:
            return jsonify({"error": "Failed to fetch forecast data."}), 502

        forecast_data = forecast_response.json()
        current_data = forecast_data.get("current", {})
        daily_data = forecast_data.get("daily", {})

        # Step 3: Format daily forecast entries
        forecast_list = []
        dates = daily_data.get("time", [])
        weather_codes = daily_data.get("weather_code", [])
        temp_maxs = daily_data.get("temperature_2m_max", [])
        temp_mins = daily_data.get("temperature_2m_min", [])
        sunrises = daily_data.get("sunrise", [])
        sunsets = daily_data.get("sunset", [])

        for idx, date_str in enumerate(dates):
            forecast_list.append({
                "date": date_str,
                "weather_code": weather_codes[idx] if idx < len(weather_codes) else None,
                "temperature_max": temp_maxs[idx] if idx < len(temp_maxs) else None,
                "temperature_min": temp_mins[idx] if idx < len(temp_mins) else None,
                "sunrise": sunrises[idx] if idx < len(sunrises) else None,
                "sunset": sunsets[idx] if idx < len(sunsets) else None,
            })

        # Step 4: Construct standardized JSON payload for frontend
        payload = {
            "location": {
                "name": location_name,
                "country": country_display,
                "timezone": forecast_data.get("timezone", "UTC"),
                "latitude": latitude,
                "longitude": longitude
            },
            "current": {
                "temperature": current_data.get("temperature_2m"),
                "feels_like": current_data.get("apparent_temperature"),
                "humidity": current_data.get("relative_humidity_2m"),
                "wind_speed": current_data.get("wind_speed_10m"),
                "weather_code": current_data.get("weather_code"),
                "updated_at": current_data.get("time")
            },
            "forecast": forecast_list
        }

        return jsonify(payload), 200

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out while contacting weather service."}), 504
    except requests.exceptions.RequestException:
        return jsonify({"error": "Network error while fetching weather data."}), 502
    except Exception:
        return jsonify({"error": "An unexpected server error occurred."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True, use_reloader=False)
