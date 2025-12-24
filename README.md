# EcoPredict

API y dashboard de prediccion climatica a corto plazo (~24 h) que combina datos horarios publicos de Open-Meteo con modelos sencillos (Linear Regression + Random Forest) para mostrar prediccion vs forecast base y metricas visibles.

## Alcance y objetivo
- Prediccion local por ciudad o coordenadas (stateless, sin base de datos).
- Horizonte corto (~24 h) con comparacion explicita frente al forecast numerico base.
- Demo tecnica / MVP de portafolio; no orientado a operacion productiva.

## Stack tecnico
- Backend/API: FastAPI + Uvicorn
- ML: scikit-learn (Linear Regression + RandomForest), pandas, numpy
- Datos: Open-Meteo (archive + forecast), Nominatim (geocoding)
- Frontend: Tailwind CSS precompilado + Chart.js (CDN)
- Estado: cache en memoria (TTL 5 min), sin persistencia

## Caracteristicas
- Sin base de datos: cache en memoria por `(lat, lon, variable)` para `/api/predict`.
- Datos climaticos: ultimas 24 h observadas/reanalisis (archive) + forecast horario futuro.
- Modelado: mezcla LR (escalada) + RandomForest; features de rezago por variable; precipitacion usa log1p y metricas de lluvia (precision/recall/F1 con umbral).
- Evaluacion: MAE calculado sobre la ventana futura inmediata; metricas de lluvia solo cuando el target es precipitacion.
- Robustez basica: timeouts y reintentos con backoff en llamadas externas; manejo de errores propagado a la UI.
- Visualizacion: prediccion ML vs forecast baseline, ultimas 24 h observadas, metricas visibles en el dashboard.

## Estructura del proyecto
- `main.py`: inicializa FastAPI, estaticos, plantillas y routers.
- `routers/dashboard.py`: ruta `/` para el dashboard.
- `routers/api.py`: `GET /api/predict` (geocoding + prediccion) y `POST /api/update` (reentrenar rapido).
- `services/weather_service.py`: descarga y combinacion de datos archive + forecast con reintentos.
- `services/model_service.py`: features, entrenamiento, prediccion y metricas.
- `templates/` y `static/`: HTML base, dashboard, CSS compilado y favicon.

## Ejecucion local
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python server.py
```
Aplicacion disponible en: http://127.0.0.1:8000/

## API
- `GET /api/predict`: params `city` (opcional), `lat`, `lon` (opcionales), `target` en `{temperature_2m, relative_humidity_2m, pressure_msl, precipitation, wind_speed_10m}` (default `temperature_2m`). Responde `city`, `target`, `predictions`, `actual` (forecast baseline), `timestamps`, `mae`, `rain_metrics` (si target es precipitacion), `observed_past` y `observed_timestamps`.
- `POST /api/update`: body `{"lat": 4.61, "lon": -74.08, "target": "temperature_2m"}`; reentrena rapido y responde estado u error HTTP.

## Notas y siguiente paso
- Sin almacenamiento persistente; orientado a demo/MVP.
- Revisar terminos de Open-Meteo y Nominatim para uso publico/comercial.
- Roadmap corto: cache persistente (Redis), fallback de proveedor, backtesting/reportes, Docker/compose y CI basica.
