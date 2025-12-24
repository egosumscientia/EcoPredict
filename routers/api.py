from fastapi import APIRouter
import requests
import pandas as pd
from services.weather_service import fetch_weather_data
from services.model_service import train_and_predict

router = APIRouter()

geo_cache = {}

def get_cached_coords(city_norm):
    if city_norm in geo_cache:
        return geo_cache[city_norm]

    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_norm}&count=5&language=es"
    resp = requests.get(geo_url, timeout=10)
    resp.raise_for_status()
    data = resp.json().get("results", [])

    if not data:
        return None

    preferred = next((r for r in data if r.get("country") == "Colombia"), data[0])
    lat, lon = preferred["latitude"], preferred["longitude"]
    city = preferred["name"]

    geo_cache[city_norm] = (lat, lon, city)
    return lat, lon, city


# === ENDPOINT PRINCIPAL ===
@router.get("/predict")
async def predict(
    city: str = "",
    lat: float | None = None,
    lon: float | None = None,
    target: str = "temperature_2m"
):
    import unicodedata
    import requests
    import pandas as pd
    from services.weather_service import fetch_weather_data
    from services.model_service import train_and_predict

    # === CASO 1: Nombre de ciudad ===
    if city:
        try:
            # Normaliza (elimina tildes y espacios)
            city_norm = (
                unicodedata.normalize("NFD", city)
                .encode("ascii", "ignore")
                .decode("utf-8")
                .strip()
            )

            # Usa el caché de geocodificación
            result = get_cached_coords(city_norm)
            if not result:
                return {"error": f"La ciudad '{city}' no existe o está mal escrita."}

            lat, lon, city = result
            print(f"✅ Resolved city '{city}' -> ({lat}, {lon})")

        except Exception as e:
            return {"error": f"No se pudo validar la ciudad '{city}'. Error: {e}"}

    # === CASO 2: Coordenadas ===
    elif lat is not None and lon is not None:
        try:
            # Corrige coordenadas invertidas o con signo incorrecto
            if abs(lat) > 90 and abs(lon) < 90:
                lat, lon = lon, lat
            if lon > 0:
                lon = -lon

            # Reverse geocoding con fallback robusto
            geo_url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
            resp = requests.get(
                geo_url,
                headers={"User-Agent": "AI-EcoPredict"},
                timeout=10
            )

            if resp.ok:
                address = resp.json().get("address", {})
                city = (
                    address.get("city")
                    or address.get("town")
                    or address.get("village")
                    or address.get("municipality")
                    or address.get("county")
                    or f"Lat: {lat:.2f}, Lon: {lon:.2f}"
                )
            else:
                city = f"Lat: {lat:.2f}, Lon: {lon:.2f}"

        except Exception as e:
            print(f"⚠️ Error en reverse geocoding: {e}")
            city = f"Lat: {lat:.2f}, Lon: {lon:.2f}"

    else:
        return {"error": "Debes ingresar una ciudad o coordenadas válidas."}


    # === Obtiene datos y predicciones ===
    df = fetch_weather_data(lat, lon)
    preds = train_and_predict(df, target=target)

    actual = df[target].tolist()
    timestamps = df["time"].astype(str).tolist()[-len(preds):]
    mae = abs(df[target] - pd.Series(preds)).mean()

    return {
        "city": city,
        "target": target,
        "predictions": preds,
        "actual": actual,
        "timestamps": timestamps,
        "mae": mae,
    }
