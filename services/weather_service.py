import requests
import pandas as pd
from datetime import datetime, timedelta

def fetch_weather_data(lat: float, lon: float):
    hourly_params = "temperature_2m,relative_humidity_2m,pressure_msl,precipitation,wind_speed_10m"

    # Observed/reanalysis pasado (últimas 24h) desde archivo
    end_date = datetime.utcnow().date()
    start_date = (datetime.utcnow() - timedelta(hours=24)).date()
    archive_url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&hourly={hourly_params}"
        "&timezone=UTC"
    )
    archive_res = requests.get(archive_url, timeout=15)
    archive_res.raise_for_status()
    archive_data = archive_res.json().get("hourly", {})
    df_archive = pd.DataFrame(archive_data) if archive_data else pd.DataFrame()

    # Forecast futuro (siguiente 7 días; luego se recorta a 24h en el modelo)
    forecast_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&hourly={hourly_params}"
        "&timezone=UTC"
    )
    forecast_res = requests.get(forecast_url, timeout=15)
    forecast_res.raise_for_status()
    forecast_data = forecast_res.json().get("hourly", {})
    df_forecast = pd.DataFrame(forecast_data) if forecast_data else pd.DataFrame()

    df_all = pd.concat([df_archive, df_forecast], ignore_index=True)
    if df_all.empty:
        raise ValueError("No se pudieron obtener datos de archivo ni forecast.")

    df_all["time"] = pd.to_datetime(df_all["time"])
    df_all = df_all.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
    return df_all
