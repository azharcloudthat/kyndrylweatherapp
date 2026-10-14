const searchForm = document.querySelector(".search-panel");
const cityInput = document.getElementById("city-search");
const results = document.getElementById("weather-results");
const submitButton = searchForm.querySelector("button[type='submit']");
const submitLabel = submitButton.querySelector("span");

async function fetchWeatherByCity(cityName) {
  const query = new URLSearchParams({ city: cityName.trim() });
  const response = await fetch(`/weather?${query}`, {
    headers: { Accept: "application/json" },
  });

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("The weather service returned an invalid response.");
  }

  if (!response.ok) {
    throw new Error(data?.error || data?.message || `Weather request failed (${response.status}).`);
  }

  if (!data || typeof data !== "object") {
    throw new Error("The weather service returned no weather data.");
  }

  return data;
}

function showMessage(titleText, messageText, isError = false) {
  const title = document.createElement("h2");
  const message = document.createElement("p");

  title.textContent = titleText;
  message.textContent = messageText;
  results.replaceChildren(title, message);
  results.classList.remove("empty-state", "weather-loaded");
  results.classList.toggle("weather-error", isError);
  if (isError) delete document.body.dataset.theme;
}

function themeFor(text, code) {
  const t = String(text || "").toLowerCase();
  if (/thunder|storm/.test(t) || [95, 96, 99].includes(code)) return "storm";
  if (/snow|sleet|ice|blizzard/.test(t) || (code >= 71 && code <= 77) || code === 85 || code === 86) return "snow";
  if (/rain|drizzle|shower/.test(t) || (code >= 51 && code <= 67) || (code >= 80 && code <= 82)) return "rain";
  if (/fog|mist|haze/.test(t) || code === 45 || code === 48) return "fog";
  if (/cloud|overcast/.test(t) || code === 1 || code === 2 || code === 3) return "cloudy";
  if (/clear|sun/.test(t) || code === 0) return "clear";
  return null;
}

function applyTheme(current, conditionText) {
  const code = Number(current.weather_code ?? current.weathercode ?? current.code);
  let theme = themeFor(conditionText, Number.isNaN(code) ? undefined : code);
  if ((current.is_day === 0 || current.is_day === false) && (theme === "clear" || theme === "cloudy")) {
    theme = "night";
  }
  if (theme) {
    document.body.dataset.theme = theme;
  } else {
    delete document.body.dataset.theme;
  }
}

function renderWeather(data, requestedCity) {
  const current = data.current || data.current_weather || data;
  const location = typeof data.location === "string" ? data.location : data.location?.name;
  const cityName = data.city || location || requestedCity;
  const title = document.createElement("h2");
  const condition = document.createElement("p");
  const metrics = document.createElement("dl");

  title.textContent = cityName;
  condition.className = "weather-condition";
  condition.textContent = current.condition || current.conditions || current.description || "Current conditions";
  metrics.className = "weather-metrics";
  applyTheme(current, condition.textContent);

  const temperature = current.temperature ?? current.temperature_2m ?? current.temp_c ?? current.temp;
  const temperatureUnit = current.temperature_unit || data.units?.temperature || "";
  const metricValues = [
    ["Temperature", temperature === undefined ? undefined : `${temperature}${temperatureUnit ? ` ${temperatureUnit}` : ""}`],
    ["Humidity", current.humidity === undefined ? undefined : `${current.humidity}%`],
    ["Wind", current.wind_speed ?? current.windspeed],
  ].filter(([, value]) => value !== undefined && value !== null);

  for (const [labelText, valueText] of metricValues) {
    const item = document.createElement("div");
    const label = document.createElement("dt");
    const value = document.createElement("dd");
    label.textContent = labelText;
    value.textContent = valueText;
    item.append(label, value);
    metrics.append(item);
  }

  results.replaceChildren(title, condition);
  if (metricValues.length > 0) {
    results.append(metrics);
  } else {
    const details = document.createElement("pre");
    details.textContent = JSON.stringify(data, null, 2);
    results.append(details);
  }
  results.classList.remove("empty-state", "weather-error");
  results.classList.add("weather-loaded");
}

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const cityName = cityInput.value.trim();

  if (!cityName) {
    cityInput.focus();
    return;
  }

  submitButton.disabled = true;
  submitLabel.textContent = "Loading...";
  showMessage("Loading forecast", `Getting the latest weather for ${cityName}.`);

  try {
    const weather = await fetchWeatherByCity(cityName);
    renderWeather(weather, cityName);
  } catch (error) {
    showMessage("Weather unavailable", error.message, true);
  } finally {
    submitButton.disabled = false;
    submitLabel.textContent = "Get weather";
  }
});
