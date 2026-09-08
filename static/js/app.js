const WEATHER_ENDPOINT = "/weather";

let activeRequest;

const weatherDescriptions = {
    0: { label: "Clear sky", icon: "☀", theme: "clear" },
    1: { label: "Mainly clear", icon: "🌤", theme: "clear" },
    2: { label: "Partly cloudy", icon: "⛅", theme: "cloudy" },
    3: { label: "Overcast", icon: "☁", theme: "cloudy" },
    45: { label: "Foggy", icon: "🌫", theme: "cloudy" },
    48: { label: "Rime fog", icon: "🌫", theme: "cloudy" },
    51: { label: "Light drizzle", icon: "🌦", theme: "rain" },
    53: { label: "Drizzle", icon: "🌦", theme: "rain" },
    55: { label: "Heavy drizzle", icon: "🌧", theme: "rain" },
    61: { label: "Light rain", icon: "🌦", theme: "rain" },
    63: { label: "Rain", icon: "🌧", theme: "rain" },
    65: { label: "Heavy rain", icon: "🌧", theme: "rain" },
    71: { label: "Light snow", icon: "🌨", theme: "snow" },
    73: { label: "Snow", icon: "❄", theme: "snow" },
    75: { label: "Heavy snow", icon: "❄", theme: "snow" },
    80: { label: "Rain showers", icon: "🌦", theme: "rain" },
    81: { label: "Showers", icon: "🌧", theme: "rain" },
    82: { label: "Heavy showers", icon: "🌧", theme: "rain" },
    95: { label: "Thunderstorm", icon: "⛈", theme: "rain" },
    96: { label: "Thunderstorm with hail", icon: "⛈", theme: "rain" },
    99: { label: "Thunderstorm with heavy hail", icon: "⛈", theme: "rain" }
};

function getWeatherDescription(code) {
    return weatherDescriptions[code] || {
        label: "Conditions unavailable",
        icon: "?",
        theme: "cloudy"
    };
}

async function fetchWeather(cityName) {
    const city = cityName.trim();
    if (!city) {
        throw new Error("Enter a city name.");
    }

    if (activeRequest) {
        activeRequest.abort();
    }

    const controller = new AbortController();
    activeRequest = controller;
    const query = new URLSearchParams({ city });

    try {
        const response = await fetch(`${WEATHER_ENDPOINT}?${query}`, {
            signal: controller.signal,
            headers: { Accept: "application/json" }
        });
        const payload = await response.json();

        if (!response.ok) {
            throw new Error(payload.error || "Unable to load weather data.");
        }

        return payload;
    } finally {
        if (activeRequest === controller) {
            activeRequest = null;
        }
    }
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value ?? "--";
    }
}

function formatTime(value) {
    if (!value) {
        return "--";
    }

    const time = value.includes("T") ? value.split("T")[1] : value;
    return time.slice(0, 5);
}

function formatDate(value) {
    if (!value) {
        return "--";
    }

    return new Intl.DateTimeFormat(undefined, {
        weekday: "short",
        month: "short",
        day: "numeric"
    }).format(new Date(`${value}T12:00:00`));
}

function renderForecast(days) {
    const forecastList = document.getElementById("forecast-list");
    if (!forecastList) {
        return;
    }

    forecastList.replaceChildren();

    days.forEach((day) => {
        const description = getWeatherDescription(day.weather_code);
        const card = document.createElement("article");
        card.className = "forecast-card";

        const date = document.createElement("h3");
        date.textContent = formatDate(day.date);

        const icon = document.createElement("span");
        icon.className = "forecast-icon";
        icon.setAttribute("aria-hidden", "true");
        icon.textContent = description.icon;

        const condition = document.createElement("p");
        condition.className = "forecast-condition";
        condition.textContent = description.label;

        const temperatures = document.createElement("p");
        temperatures.className = "forecast-temperatures";
        temperatures.textContent = `${day.temperature_max}° `;

        const minimum = document.createElement("span");
        minimum.textContent = `/ ${day.temperature_min}°`;
        temperatures.append(minimum);

        card.append(date, icon, condition, temperatures);
        forecastList.append(card);
    });
}

function renderWeather(data) {
    const current = data.current;
    const location = data.location;
    const description = getWeatherDescription(current.weather_code);

    document.body.dataset.weather = description.theme;
    setText("location-name", location.name);
    setText("location-details", location.country);
    setText("updated-time", current.updated_at ? `Updated ${formatTime(current.updated_at)}` : "");
    setText("current-weather-icon", description.icon);
    setText("current-condition", description.label);
    setText("current-temperature", current.temperature);
    setText("feels-like", current.feels_like);
    setText("humidity", current.humidity);
    setText("wind-speed", current.wind_speed);
    setText("timezone", location.timezone);

    const firstDay = data.forecast[0];
    setText("sunrise", formatTime(firstDay?.sunrise));
    setText("sunset", formatTime(firstDay?.sunset));
    renderForecast(data.forecast);

    document.getElementById("weather-results")?.removeAttribute("hidden");
    document.getElementById("empty-state")?.setAttribute("hidden", "hidden");
}

function setLoading(isLoading) {
    const button = document.getElementById("get-weather-button");
    const status = document.getElementById("status-message");

    if (button) {
        button.disabled = isLoading;
        button.setAttribute("aria-busy", String(isLoading));
    }

    if (status) {
        status.textContent = isLoading ? "Preparing your Kyndryl weather briefing..." : "";
    }
}

const weatherForm = document.getElementById("weather-form");
const cityInput = document.getElementById("city-input");
const errorMessage = document.getElementById("error-message");

weatherForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorMessage?.setAttribute("hidden", "hidden");
    setLoading(true);

    try {
        const data = await fetchWeather(cityInput.value);
        renderWeather(data);
    } catch (error) {
        if (error.name !== "AbortError" && errorMessage) {
            errorMessage.textContent = error.message;
            errorMessage.removeAttribute("hidden");
        }
    } finally {
        setLoading(false);
    }
});
