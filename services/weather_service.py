import requests
import pandas as pd

def fetch_weather_data(lat: float, lon: float):
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,relative_humidity_2m,pressure_msl,precipitation,wind_speed_10m"
    )
    res = requests.get(url)
    res.raise_for_status()
    data = res.json()["hourly"]
    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"])
    return df
