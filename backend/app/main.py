import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.routers import asistencia

# Configuración de logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sistema_asistencia")

app = FastAPI(
    title="Sistema de Asistencia por DNI",
    version="1.0.0",
    description="API REST para registro de asistencia de personal/estudiantes con validación y consulta RENIEC.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración de CORS para el Frontend (React o Vanilla JS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if "*" not in settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manejo personalizado de errores de validación (ej. DNI no tiene 8 dígitos)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    detalles = exc.errors()
    mensaje_error = "Formato de DNI inválido. Debe contener exactamente 8 dígitos numéricos."
    if detalles and "msg" in detalles[0]:
        mensaje_error = detalles[0]["msg"].replace("Value error, ", "")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "message": mensaje_error,
            "detail": str(detalles)
        }
    )


# Manejo global de excepciones no controladas
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Error no controlado en la petición: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Ocurrió un error interno en el servidor al procesar la asistencia.",
            "detail": str(exc) if settings.ENVIRONMENT == "development" else None
        }
    )


# Endpoint de Health Check
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "asistencia-backend", "version": "1.0.0"}


# Registrar el router de asistencia
app.include_router(asistencia.router)

# Montar archivos estáticos del Frontend si el directorio existe
import os
from fastapi.staticfiles import StaticFiles

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
