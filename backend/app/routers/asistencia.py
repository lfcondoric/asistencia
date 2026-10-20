import logging
from fastapi import APIRouter, status
from app.schemas import AsistenciaRequest, AsistenciaResponse, AsistenciaDetalle
from app.services.asistencia_service import AsistenciaService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Asistencia"])


@router.post(
    "/asistencia",
    response_model=AsistenciaResponse,
    status_code=status.HTTP_200_OK,
    summary="Registrar marcación de asistencia mediante DNI",
    description="Recibe el DNI, valida el formato, obtiene los datos (local o API externa) y ejecuta el procedimiento almacenado."
)
async def registrar_asistencia(payload: AsistenciaRequest):
    """
    Endpoint principal para registro de asistencia:
    1. Valida automáticamente el DNI de 8 dígitos mediante Pydantic.
    2. Consulta si existe en MySQL o llama a la API de RENIEC externa.
    3. Registra en la base de datos a través de `sp_registrar_asistencia`.
    4. Retorna el resultado con el nombre del asistente.
    """
    dni = payload.dni.strip()
    logger.info(f"Solicitud recibida para registrar asistencia del DNI: {dni}")

    resultado = await AsistenciaService.procesar_asistencia(dni)

    mensaje = (
        f"¡Bienvenido(a)! Se registró tu asistencia correctamente."
        if not resultado["es_nuevo_registro"]
        else f"¡Registro nuevo creado y asistencia registrada con éxito!"
    )

    return AsistenciaResponse(
        success=True,
        message=mensaje,
        data=AsistenciaDetalle(
            id_asistencia=resultado["id_asistencia"],
            dni=resultado["dni"],
            nombre_completo=resultado["nombre_completo"],
            fecha_hora=resultado["fecha_hora"],
            es_nuevo_registro=resultado["es_nuevo_registro"]
        )
    )
