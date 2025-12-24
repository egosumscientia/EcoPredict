# AI-EcoPredict

Dashboard y API ligera con FastAPI que obtiene datos horarios de Open-Meteo, entrena modelos sencillos (Linear Regression + Random Forest) en caliente y grafica predicciones vs valores reales con Chart.js.

## Stack rápido
- Backend: FastAPI, Uvicorn, Jinja2.
- ML: scikit-learn, pandas, numpy.
- Frontend: HTML con Tailwind CSS precompilado y Chart.js (CDN).
- Cache en memoria para `/api/predict` por lat/lon/variable (5 minutos) para reducir llamadas a Open-Meteo.
- Histórico + forecast: se consulta Open-Meteo con archivo (`archive-api`) para obtener las últimas 24h observadas/reanálisis y el forecast para el horizonte futuro.
- El UI muestra las próximas horas (UTC) como horizonte de predicción y grafica predicción vs valores del forecast disponibles.

## Estructura
- `main.py` monta estáticos/plantillas y registra routers.
- `routers/dashboard.py` sirve el dashboard (`/`).
- `routers/api.py` expone `GET /api/predict` (geocoding + predicción).
- `services/weather_service.py` descarga series horarias de Open-Meteo.
- `services/model_service.py` entrena y mezcla LR + RandomForest (demo).
- `templates/` base y dashboard con lógica JS inline.
- `static/css/styles.css` Tailwind compilado; `static/favicon.ico`.
- `tailwind.config.js` y `postcss.config.js` para recompilar CSS si se desea.

## Puesta en marcha
1) Crear entorno y dependencias Python:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
2) Ejecutar servidor:
```bash
python server.py
```
Servidor local en `http://127.0.0.1:8000/`.

## API
`GET /api/predict` — parámetros:
- `city` (opcional): nombre de ciudad (se normaliza y se geocodifica via Open-Meteo).
- `lat`, `lon` (opcionales): coordenadas numéricas; se invierten si vienen en orden incorrecto y se hace reverse geocoding de cortesía.
- `target` (opcional): variable a predecir. Valores soportados: `temperature_2m`, `relative_humidity_2m`, `pressure_msl`, `precipitation`, `wind_speed_10m`. Default `temperature_2m`.

Respuesta (JSON):
```json
{
  "city": "Bogotá",
  "target": "temperature_2m",
  "predictions": [ ... últimas de test ... ],
  "actual": [ ... reales de test ... ],
  "timestamps": [ ... de test ... ],
  "mae": 0.42,  // MAE calculado sobre la ventana de test
  "rain_metrics": {
    "threshold": 0.05,
    "precision": 0.8,
    "recall": 0.75,
    "f1": 0.77
  } // solo para target precipitation
}
```
Errores comunes: ciudad inexistente, sin ciudad ni coordenadas, o target inválido.

`POST /api/update` — reentrena rápido usando coordenadas (JSON) y target opcional:
```json
{ "lat": 4.61, "lon": -74.08, "target": "temperature_2m" }
```
Responde `{"status": "ok", ...}` o `{"status": "error", "error": "..."}`. El botón “Update Model” en la barra superior lo usa con Bogotá por defecto.

## Dashboard
- Ruta `/`: formulario para ciudad o coordenadas, selector de variable y gráfico de líneas comparando predicciones vs valores reales.
- Usa Chart.js desde CDN y el CSS ya compilado en `static/css/styles.css`.
- El botón “Update Model” en la barra superior dispara `/api/update` para refrescar el modelo demo.
- Muestra el MAE de test (ventana deslizante) debajo del formulario.
- Para precipitación muestra métricas de lluvia (precisión/recall/F1) con umbral configurado.
- Se grafican dos paneles: arriba predicción vs forecast baseline para las próximas 24h; abajo las últimas 24h observadas (archivo).

## Notas sobre datos/modelo
- Los datos se descargan al vuelo de Open-Meteo; no hay caché ni almacenamiento persistente.
- El modelo mezcla LR (escalada con StandardScaler) + RandomForest con rezagos del target (dependen de la variable, p.ej. humedad/presión usan 1,2,3,6; viento 1,2). Para precipitación aplica log1p al target, recorta predicciones a no-negativas y usa un umbral de lluvia (0.05 mm) para métricas de clasificación (precisión/recall/F1). Entrena con las filas hasta “ahora” y predice el horizonte futuro (próximas 24h o filas disponibles); calcula el MAE contra el forecast futuro.

## Roadmap
- Implementar `/api/update` o eliminar el botón hasta que exista.
- Añadir caché de respuestas de pronóstico y manejo de fallos de red.
- Separar train/test, validar targets faltantes y cubrir con tests automatizados.
- Configurar variables de entorno para claves, timeouts y URLs de servicios externos.
- Empaquetar Docker/compose y agregar CI básica (lint + tests).
