# Triggers uvicorn reload
from typing import Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta, timezone
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import httpx
import os
import json
from pydantic import BaseModel

router = APIRouter()

class ForecastSlot(BaseModel):
    dt: int
    time: str
    temp: float
    pop: int
    condition: str
    icon: str
    precip_mm: Optional[float] = 0.0
    showers_mm: Optional[float] = 0.0
    wind_kmh: Optional[float] = 0.0
    wind_dir: Optional[int] = 0
    humidity_pct: Optional[int] = 0

class WeatherInsightsRequest(BaseModel):
    forecast: List[ForecastSlot]
    location: str

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

def _map_wmo_to_meteocons_icon(wmo_code: int, is_day: bool = True) -> str:
    """
    Maps WMO weather codes to Meteocons SVG filenames.
    """
    time_suffix = "day" if is_day else "night"
    
    mapping = {
        0: f"clear-{time_suffix}",
        1: f"partly-cloudy-{time_suffix}",
        2: f"partly-cloudy-{time_suffix}",
        3: f"partly-cloudy-{time_suffix}",
        45: "fog",
        48: "fog",
        51: f"partly-cloudy-{time_suffix}-drizzle",
        53: f"partly-cloudy-{time_suffix}-drizzle",
        55: f"partly-cloudy-{time_suffix}-drizzle",
        56: f"partly-cloudy-{time_suffix}-sleet",
        57: f"partly-cloudy-{time_suffix}-sleet",
        61: f"partly-cloudy-{time_suffix}-rain",
        63: f"partly-cloudy-{time_suffix}-rain",
        65: f"partly-cloudy-{time_suffix}-rain",
        66: f"partly-cloudy-{time_suffix}-sleet",
        67: f"partly-cloudy-{time_suffix}-sleet",
        71: f"partly-cloudy-{time_suffix}-snow",
        73: f"partly-cloudy-{time_suffix}-snow",
        75: f"partly-cloudy-{time_suffix}-snow",
        77: f"partly-cloudy-{time_suffix}-snow",
        80: f"partly-cloudy-{time_suffix}-rain",
        81: f"partly-cloudy-{time_suffix}-rain",
        82: f"partly-cloudy-{time_suffix}-rain",
        85: f"partly-cloudy-{time_suffix}-snow",
        86: f"partly-cloudy-{time_suffix}-snow",
        95: f"thunderstorms-{time_suffix}",
        96: f"thunderstorms-{time_suffix}-rain",
        99: f"thunderstorms-{time_suffix}-rain",
    }
    return mapping.get(wmo_code, "not-available")

def _map_wmo_to_condition(wmo_code: int) -> str:
    mapping = {
        0: "Clear",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Cloudy",
        45: "Fog",
        48: "Rime Fog",
        51: "Light Drizzle",
        53: "Drizzle",
        55: "Heavy Drizzle",
        56: "Freezing Drizzle",
        57: "Heavy Freezing Drizzle",
        61: "Light Rain",
        63: "Rain",
        65: "Heavy Rain",
        66: "Freezing Rain",
        67: "Heavy Freezing Rain",
        71: "Light Snow",
        73: "Snow",
        75: "Heavy Snow",
        77: "Snow Grains",
        80: "Light Showers",
        81: "Showers",
        82: "Heavy Showers",
        85: "Snow Showers",
        86: "Heavy Snow Showers",
        95: "Thunderstorm",
        96: "Thunderstorm with Hail",
        99: "Thunderstorm with Heavy Hail",
    }
    return mapping.get(wmo_code, "Unknown")


@router.get("/current")
async def get_current_weather(
    lat: float = Query(14.5731, description="Latitude, defaults to Pasig City"),
    lon: float = Query(121.0594, description="Longitude, defaults to Pasig City"),
) -> Any:
    """
    Fetch current weather from Open-Meteo API using the forecast for the current hour
    to ensure the current weather perfectly matches the first hour of the forecast chart.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "apparent_temperature", "weather_code", "is_day", "precipitation", "showers", "wind_speed_10m", "relative_humidity_2m", "wind_direction_10m"],
        "forecast_hours": 2
    }
    
    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_apparent_temperature = hourly.Variables(1).ValuesAsNumpy()
        hourly_weather_code = hourly.Variables(2).ValuesAsNumpy()
        hourly_is_day = hourly.Variables(3).ValuesAsNumpy()
        hourly_precipitation = hourly.Variables(4).ValuesAsNumpy()
        hourly_showers = hourly.Variables(5).ValuesAsNumpy()
        hourly_wind_speed = hourly.Variables(6).ValuesAsNumpy()
        hourly_humidity = hourly.Variables(7).ValuesAsNumpy()
        hourly_wind_direction = hourly.Variables(8).ValuesAsNumpy()

        hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )}
        
        hourly_data["temperature_2m"] = hourly_temperature_2m
        hourly_data["apparent_temperature"] = hourly_apparent_temperature
        hourly_data["weather_code"] = hourly_weather_code
        hourly_data["is_day"] = hourly_is_day
        hourly_data["precipitation"] = hourly_precipitation
        hourly_data["showers"] = hourly_showers
        hourly_data["wind_speed"] = hourly_wind_speed
        hourly_data["wind_direction"] = hourly_wind_direction
        hourly_data["humidity"] = hourly_humidity

        df = pd.DataFrame(data = hourly_data)
        
        # Filter to include the current hour
        current_time = pd.Timestamp.now(tz='UTC').floor('h')
        df = df[df['date'] >= current_time].head(1)
        
        if df.empty:
            raise Exception("No current hour data found")
            
        row = df.iloc[0]
        weather_code = int(row["weather_code"])
        is_day = bool(row["is_day"])
        
        parsed_data = {
            "temp": round(float(row["temperature_2m"]), 1),
            "feels_like": round(float(row["apparent_temperature"]), 1),
            "condition": _map_wmo_to_condition(weather_code),
            "icon": _map_wmo_to_meteocons_icon(weather_code, is_day),
            "precip_mm": round(float(row["precipitation"]), 2),
            "showers_mm": round(float(row["showers"]), 2),
            "wind_kmh": round(float(row["wind_speed"]), 1),
            "wind_dir": int(row["wind_direction"]),
            "humidity_pct": int(row["humidity"]),
            "location": "Pasig City" # Fallback since Open-Meteo doesn't return geocoding data in weather endpoint
        }
        return parsed_data
        
    except Exception as e:
        import traceback
        return {
            "temp": "--",
            "feels_like": "--",
            "condition": "Unavailable",
            "icon": "not-available",
            "location": str(e)
        }

@router.get("/forecast")
async def get_forecast(
    lat: float = Query(14.5731, description="Latitude, defaults to Pasig City"),
    lon: float = Query(121.0594, description="Longitude, defaults to Pasig City"),
    count: int = Query(24, description="Number of hourly slots to return (max 72)"),
) -> Any:
    """
    Fetch hourly forecast from Open-Meteo API.
    Returns the next N hourly forecast slots with temperature,
    rain probability, weather condition, and icons.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "precipitation_probability", "weather_code", "is_day", "precipitation", "showers", "wind_speed_10m", "relative_humidity_2m", "wind_direction_10m"],
        "forecast_hours": count + 1 # Add 1 because we might skip the current hour if it's already past
    }

    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
        hourly_weather_code = hourly.Variables(2).ValuesAsNumpy()
        hourly_is_day = hourly.Variables(3).ValuesAsNumpy()
        hourly_precipitation = hourly.Variables(4).ValuesAsNumpy()
        hourly_showers = hourly.Variables(5).ValuesAsNumpy()
        hourly_wind_speed = hourly.Variables(6).ValuesAsNumpy()
        hourly_humidity = hourly.Variables(7).ValuesAsNumpy()
        hourly_wind_direction = hourly.Variables(8).ValuesAsNumpy()

        hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )}
        
        hourly_data["temperature_2m"] = hourly_temperature_2m
        hourly_data["precipitation_probability"] = hourly_precipitation_probability
        hourly_data["weather_code"] = hourly_weather_code
        hourly_data["is_day"] = hourly_is_day
        hourly_data["precipitation"] = hourly_precipitation
        hourly_data["showers"] = hourly_showers
        hourly_data["wind_speed"] = hourly_wind_speed
        hourly_data["wind_direction"] = hourly_wind_direction
        hourly_data["humidity"] = hourly_humidity

        df = pd.DataFrame(data = hourly_data)
        
        # Filter to include the current hour and future times
        current_time = pd.Timestamp.now(tz='UTC').floor('h')
        df = df[df['date'] >= current_time].head(count)
        
        slots: List[dict[str, Any]] = []
        for index, row in df.iterrows():
            weather_code = int(row["weather_code"])
            is_day = bool(row["is_day"])
            slots.append({
                "dt": int(row["date"].timestamp()),
                "time": row["date"].strftime('%Y-%m-%d %H:%M:%S'),
                "temp": round(row["temperature_2m"], 1),
                "pop": int(row["precipitation_probability"]), # percentage
                "condition": _map_wmo_to_condition(weather_code),
                "icon": _map_wmo_to_meteocons_icon(weather_code, is_day),
                "precip_mm": round(row["precipitation"], 2),
                "showers_mm": round(row["showers"], 2),
                "wind_kmh": round(row["wind_speed"], 1),
                "wind_dir": int(row["wind_direction"]),
                "humidity_pct": int(row["humidity"])
            })
            
        return {
            "forecast": slots,
            "location": "Pasig City"
        }

    except Exception as e:
        return {"forecast": [], "location": "Unknown"}

@router.post("/insights")
async def get_weather_insights(request: WeatherInsightsRequest):
    """
    Generate dynamic weather insights using OpenRouter's free models.
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenRouter API key is not configured")

    # Limit to the first 4 slots for immediate insights
    forecast_subset = request.forecast[:4]
    
    forecast_data_str = json.dumps([s.dict() for s in forecast_subset], indent=2)

    system_prompt = (
        "You are an expert meteorologist and teacher. Your job is to look at the next 4 hours of weather data and explain to the user exactly what the numbers mean so they can understand the chart.\n\n"
        "Meteorology Rules:\n"
        "1. For Storm Risk, mention the exact PoP (%) and Volume (mm/h) from the data, and explain what they mean. (e.g., 'The chart shows a 40% chance of rain, meaning a 4 in 10 chance rain falls exactly here. The 1.5 mm/h volume indicates it would only be a light drizzle.').\n"
        "2. For Environment, mention the Temp, Humidity, and Wind, and explain how they combine to feel. (e.g., 'With 95% humidity, the 25°C temperature will feel much warmer and stickier.').\n"
        "3. Explicitly mention you are analyzing the next 4 hours.\n\n"
        "Strict Output Constraints (JSON FORMAT):\n"
        "You must respond with a JSON object containing exactly two keys:\n"
        "- \"storm_risk\": A 2-sentence explanation teaching the user what the current Rain % and mm/h numbers mean.\n"
        "- \"environment\": A 2-sentence explanation teaching the user what the current Temp, Humidity, and Wind numbers mean.\n"
        "Return ONLY valid JSON."
    )

    user_prompt = f"Location: {request.location}\nHere is the upcoming weather data:\n{forecast_data_str}\n\nPlease generate the JSON summary."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:3000", # Required by OpenRouter
        "X-Title": "LANES Weather", # Required by OpenRouter
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openrouter/free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20.0)
            response.raise_for_status()
            data = response.json()
            
            message_content = data["choices"][0]["message"]["content"]
            model_used = data.get("model", "openrouter/free")
            
            try:
                # Some free models might wrap in markdown ```json even when requested not to
                clean_content = message_content.replace('```json', '').replace('```', '').strip()
                parsed_json = json.loads(clean_content)
            except json.JSONDecodeError:
                # Fallback if the model failed to output valid JSON
                parsed_json = {
                    "storm_risk": "Could not generate storm risk insights at this time.",
                    "environment": "Could not generate environmental insights at this time."
                }
                
            return {
                "insights": parsed_json,
                "model": model_used
            }
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="The AI service is currently overloaded and took too long to respond. Please try again in a moment.")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"OpenRouter API error: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Failed to connect to the AI service: {type(e).__name__}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Internal error: {type(e).__name__} - {str(e)}")
