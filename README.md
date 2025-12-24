# AI-EcoPredict

Dashboard y API ligera con FastAPI que obtiene datos horarios de Open-Meteo, entrena modelos sencillos (Linear Regression + Random Forest) en caliente y grafica predicciones vs valores reales con Chart.js.

## Stack rápido
- Backend: FastAPI, Uvicorn, Jinja2.
- ML: scikit-learn, pandas, numpy.
- Frontend: HTML con Tailwind CSS precompilado y Chart.js (CDN).

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
  "predictions": [ ... últimas 24 ... ],
  "actual": [ ... serie completa ... ],
  "timestamps": [ ... ],
  "mae": 0.42
}
```
Errores comunes: ciudad inexistente, sin ciudad ni coordenadas, o target inválido.

## Dashboard
- Ruta `/`: formulario para ciudad o coordenadas, selector de variable y gráfico de líneas comparando predicciones vs valores reales.
- Usa Chart.js desde CDN y el CSS ya compilado en `static/css/styles.css`.
- El botón “Update Model” en la barra superior apunta a `/api/update`, pero ese endpoint aún no existe (sin efecto).

## Notas sobre datos/modelo
- Los datos se descargan al vuelo de Open-Meteo; no hay caché ni almacenamiento persistente.
- El modelo se entrena con los mismos datos usados para predecir (modo demo) y mezcla LR + RandomForest; no hay split train/test ni serialización.

## Roadmap
- Implementar `/api/update` o eliminar el botón hasta que exista.
- Añadir caché de respuestas de pronóstico y manejo de fallos de red.
- Separar train/test, validar targets faltantes y cubrir con tests automatizados.
- Configurar variables de entorno para claves, timeouts y URLs de servicios externos.
- Empaquetar Docker/compose y agregar CI básica (lint + tests).
