from fastapi import APIRouter, Body, HTTPException
import time
import requests
from services.weather_service import fetch_weather_data
from services.model_service import train_and_predict

router = APIRouter()

geo_cache = {}
predict_cache: dict = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


def _cache_key(lat: float, lon: float, target: str):
    # Redondea para evitar claves diferentes por ruido decimal
    return (round(lat, 4), round(lon, 4), target)


def _get_cached_prediction(lat: float, lon: float, target: str):
    key = _cache_key(lat, lon, target)
    entry = predict_cache.get(key)
    now = time.time()
    if not entry:
        return None
    if entry["expires_at"] < now:
        predict_cache.pop(key, None)
        return None
    return entry["value"]


def _set_cached_prediction(lat: float, lon: float, target: str, value: dict):
    key = _cache_key(lat, lon, target)
    predict_cache[key] = {"value": value, "expires_at": time.time() + CACHE_TTL_SECONDS}


def _get_json_with_retries(url: str, *, timeout: int = 10, attempts: int = 3, backoff: float = 1.5, headers=None):
    """GET with retries + backoff; raises last exception on failure."""
    last_err = None
    for attempt in range(attempts):
        try:
            resp = requests.get(url, timeout=timeout, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as err:
            last_err = err
            if attempt == attempts - 1:
                raise
            time.sleep(backoff ** attempt)
    if last_err:
        raise last_err
    raise RuntimeError("Unexpected error fetching remote data")


def get_cached_coords(city_norm: str):
    if city_norm in geo_cache:
        return geo_cache[city_norm]

    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_norm}&count=5&language=es"
    geo_json = _get_json_with_retries(geo_url, timeout=10)
    data = geo_json.get("results", []) if geo_json else []

    if not data:
        return None

    preferred = next((r for r in data if r.get("country") == "Colombia"), data[0])
    lat, lon = preferred["latitude"], preferred["longitude"]
    city = preferred["name"]

    geo_cache[city_norm] = (lat, lon, city)
    return lat, lon, city


@router.get("/predict")
async def predict(
    city: str = "",
    lat: float | None = None,
    lon: float | None = None,
    target: str = "temperature_2m"
):
    import unicodedata

    # Caso 1: nombre de ciudad
    if city:
        try:
            city_norm = (
                unicodedata.normalize("NFD", city)
                .encode("ascii", "ignore")
                .decode("utf-8")
                .strip()
            )

            result = get_cached_coords(city_norm)
            if not result:
                raise HTTPException(status_code=404, detail=f"La ciudad '{city}' no existe o esta mal escrita.")

            lat, lon, city = result
            print(f"? Resolved city '{city}' -> ({lat}, {lon})")

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"No se pudo validar la ciudad '{city}'. Error: {e}")

    # Caso 2: coordenadas
    elif lat is not None and lon is not None:
        try:
            if abs(lat) > 90 and abs(lon) < 90:
                lat, lon = lon, lat
            if lon > 0:
                lon = -lon

            geo_url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
            resp_json = _get_json_with_retries(
                geo_url,
                headers={"User-Agent": "AI-EcoPredict"},
                timeout=10,
            )

            address = resp_json.get("address", {}) if resp_json else {}
            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
                or address.get("county")
                or f"Lat: {lat:.2f}, Lon: {lon:.2f}"
            )

        except Exception as e:
            print(f"?? Error en reverse geocoding: {e}")
            city = f"Lat: {lat:.2f}, Lon: {lon:.2f}"

    else:
        raise HTTPException(status_code=400, detail="Debes ingresar una ciudad o coordenadas validas.")

    # Cache de prediccion
    cached = _get_cached_prediction(lat, lon, target)
    if cached:
        return cached

    # Obtiene datos y predicciones
    try:
        df = fetch_weather_data(lat, lon)
    except requests.HTTPError as http_err:
        status = http_err.response.status_code if http_err.response is not None else 502
        raise HTTPException(status_code=status, detail="Error al obtener datos meteorologicos.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo obtener datos meteorologicos: {e}")

    result = train_and_predict(df, target=target)

    response = {
        "city": city,
        "target": target,
        "predictions": result.get("predictions", []),
        "actual": result.get("actual", []),
        "timestamps": result.get("timestamps", []),
        "mae": result.get("mae"),
        "rain_metrics": result.get("rain_metrics"),
        "observed_past": result.get("observed_past", []),
        "observed_timestamps": result.get("observed_timestamps", []),
    }

    _set_cached_prediction(lat, lon, target, response)

    return response


@router.post("/update")
async def update_model(payload: dict = Body(default={})):
    """
    Reentrena el modelo rapido usando coordenadas dadas (o Bogota por defecto).
    Pensado para el boton "Update Model" del navbar.
    """
    lat = payload.get("lat", 4.61)
    lon = payload.get("lon", -74.08)
    target = payload.get("target", "temperature_2m")

    try:
        if lon > 0:
            lon = -lon

        df = fetch_weather_data(lat, lon)
        train_and_predict(df, target=target, retrain=True)

        return {
            "status": "ok",
            "message": f"Modelo actualizado para lat={lat}, lon={lon}, target={target}",
        }
    except requests.HTTPError as http_err:
        status = http_err.response.status_code if http_err.response is not None else 502
        raise HTTPException(
            status_code=status,
            detail="Error al obtener datos meteorologicos para actualizar el modelo.",
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo actualizar el modelo: {e}")
