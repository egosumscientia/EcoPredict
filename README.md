# AI-EcoPredict

Dashboard y API ligera con FastAPI que descarga datos horarios de Open-Meteo, entrena un modelo sencillo (Linear Regression + Random Forest) “en caliente” y grafica predicciones vs valores reales con Chart.js.

## Características
- Sin base de datos: stateless, caché en memoria (5 min por lat/lon/variable) para `/api/predict`.
- Datos: últimas 24h observadas/reanálisis (archive) + forecast futuro de Open-Meteo.
- Modelo: mezcla LR (escalada) + RandomForest con features de rezago según variable; precipitación usa log1p y métricas de lluvia (precisión/recall/F1).
- Robustez básica: timeouts y reintentos con backoff a Open-Meteo/Nominatim; errores claros en la UI.
- Frontend: Tailwind CSS compilado + Chart.js (CDN); dashboard muestra MAE de test y métricas de lluvia cuando aplica.

## Estructura
- `main.py`: monta estáticos/plantillas y registra routers.
- `routers/dashboard.py`: ruta `/` (dashboard).
- `routers/api.py`: `GET /api/predict` (geocoding + predicción) y `POST /api/update` (reentrenar rápido).
- `services/weather_service.py`: descarga y combina archivo + forecast (con reintentos).
- `services/model_service.py`: entrenamiento/predicción y métricas.
- `templates/` y `static/`: HTML base + dashboard, CSS compilado y favicon.

## Ejecutar local
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python server.py
```
App en `http://127.0.0.1:8000/`.

## API
`GET /api/predict`
- Params: `city` (opcional), `lat`, `lon` (opcionales), `target` en `{temperature_2m, relative_humidity_2m, pressure_msl, precipitation, wind_speed_10m}` (default `temperature_2m`).
- Devuelve: `city`, `target`, `predictions`, `actual` (forecast baseline), `timestamps`, `mae` (ventana de test futuro), `rain_metrics` (si target es precipitación), `observed_past` + `observed_timestamps` (últimas 24h).

`POST /api/update`
- Body: `{"lat": 4.61, "lon": -74.08, "target": "temperature_2m"}`
- Reentrena rápido y responde `{"status": "ok", ...}` o error HTTP.

## Dashboard
- Formulario para ciudad o coordenadas, selector de variable y botón Predict.
- Muestra MAE de test con etiqueta clara y, si corresponde, métricas de lluvia.
- Gráficos: próximas ~24h (predicción vs forecast baseline) y últimas 24h observadas.
- Manejo de errores visible: si la API falla o devuelve datos incompletos, se muestra mensaje en la UI.

## Notas
- Sin almacenamiento persistente; pensado como demo/MVP y pieza de portafolio.
- Revisa términos de Open-Meteo y Nominatim para uso público/comercial. Añade LICENSE (p.ej. MIT) si publicas el repo.

## Roadmap corto
- Caché persistente (Redis) y fallback de proveedor.
- Backtesting y reporte de métricas por ciudad/variable.
- Dockerfile/compose y CI básica (lint + tests).
