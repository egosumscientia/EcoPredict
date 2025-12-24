from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers import dashboard, api

app = FastAPI(title="EcoPredict")

# Archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Rutas
app.include_router(dashboard.router, tags=["Dashboard"])
# 👈 Este es el punto clave
app.include_router(api.router, prefix="/api", tags=["API"])
