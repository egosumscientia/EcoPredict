# AI-EcoPredict

AI-EcoPredict es una **API y dashboard de predicción climática a corto plazo (~24 h)** que utiliza
machine learning clásico entrenado *on-demand* sobre datos horarios públicos de Open-Meteo.

El sistema compara explícitamente la predicción ML contra el **forecast numérico base**, mostrando
métricas cuantitativas visibles para cada ubicación y variable.

---

## Alcance y objetivo

- Predicción local por ciudad o coordenadas.
- Horizonte corto (próximas ~24 h).
- Evaluar si modelos simples con features de rezago pueden **ajustar o suavizar** el forecast base.
- Proyecto orientado a **demo técnica / MVP de portafolio**, no a operación productiva.

---

## Stack técnico

- **Backend / API**: FastAPI + Uvicorn  
- **ML**: scikit-learn (Linear Regression + Random Forest)  
- **Datos**: Open-Meteo (archive + forecast), Nominatim (geocoding)  
- **Frontend**: Tailwind CSS (precompilado) + Chart.js (CDN)  
- **Estado**: stateless, caché en memoria (TTL 5 min)

---

## Características

- **Sin base de datos**  
  Arquitectura stateless con caché en memoria por `(lat, lon, variable)` para `/api/predict`.

- **Datos climáticos**
  - Últimas 24 h observadas / reanálisis (archive).
  - Forecast futuro horario de Open-Meteo.

- **Modelado**
  - Mezcla de Linear Regression (escalada) + Random Forest.
  - Features de rezago específicos por variable.
  - Precipitación: transformación `log1p` + métricas de clasificación (precision / recall / F1).

- **Evaluación**
  - MAE calculado sobre ventana futura inmediata.
  - Métricas de lluvia solo cuando el target es precipitación.

- **Robustez básica**
  - Timeouts y reintentos con *exponential backoff* a Open-Meteo y Nominatim.
  - Manejo explícito de errores hacia la UI.

- **Visualización**
  - Predicción ML vs forecast baseline.
  - Últimas 24 h observadas en tiempo local.
  - Métricas visibles en el dashboard.

---

## Estructura del proyecto

- `main.py`  
  Inicialización de FastAPI, estáticos, plantillas y routers.

- `routers/dashboard.py`  
  Ruta `/` para el dashboard.

- `routers/api.py`  
  - `GET /api/predict`: geocoding, descarga de datos, entrenamiento y predicción.  
  - `POST /api/update`: reentrenamiento rápido on-demand.

- `services/weather_service.py`  
  Descarga y combinación de datos archive + forecast con reintentos.

- `services/model_service.py`  
  Feature engineering, entrenamiento, predicción y métricas.

- `templates/` / `static/`  
  HTML base, dashboard, CSS compilado y recursos estáticos.

---

## Ejecución local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python server.py

Aplicación disponible en:
http://127.0.0.1:8000/