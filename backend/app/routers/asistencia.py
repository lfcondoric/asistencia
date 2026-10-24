import logging
from fastapi import APIRouter, status
from app.schemas import (
    AsistenciaRequest, 
    AsistenciaResponse, 
    AsistenciaDetalle,
    ActualizarCelularRequest
)
from app.services.asistencia_service import AsistenciaService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Asistencia"])


@router.post(
    "/asistencia",
    response_model=AsistenciaResponse,
    status_code=status.HTTP_200_OK,
    summary="Registrar marcación de asistencia mediante DNI, celular y fecha de nacimiento opcionales",
    description="Recibe el DNI, celular (opcional) y fecha de nacimiento (opcional), valida formatos, obtiene datos (local o RENIEC) y procesa el registro."
)
async def registrar_asistencia(payload: AsistenciaRequest):
    """
    Endpoint principal para registro de asistencia:
    1. Valida automáticamente el DNI (8 dígitos), el celular opcional (9 dígitos) y la fecha de nacimiento opcional mediante Pydantic.
    2. Consulta si la persona existe en la BD o llama a la API de RENIEC.
    3. Guarda/actualiza la persona incluyendo el celular y la fecha de nacimiento ingresados.
    4. Registra en la base de datos la marcación de asistencia.
    5. Retorna el resultado con los datos completos del asistente.
    """
    dni = payload.dni.strip()
    celular = payload.celular.strip() if payload.celular else None
    fecha_nacimiento = payload.fecha_nacimiento.strip() if payload.fecha_nacimiento else None

    logger.info(f"Solicitud recibida para registrar asistencia del DNI: {dni} (Celular: {celular or 'No enviado'}, F. Nacimiento: {fecha_nacimiento or 'No enviado'})")

    # Envía dni, celular y fecha de nacimiento al servicio de asistencia
    resultado = await AsistenciaService.procesar_asistencia(
        dni=dni, 
        celular=celular,
        fecha_nacimiento=fecha_nacimiento
    )

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
            celular=resultado.get("celular"),
            fecha_nacimiento=resultado.get("fecha_nacimiento"),
            fecha_hora=resultado["fecha_hora"],
            es_nuevo_registro=resultado["es_nuevo_registro"]
        )
    )


@router.patch(
    "/asistencia/celular/{dni}",
    response_model=AsistenciaResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar celular manualmente por DNI",
    description="Permite registrar o modificar únicamente el número de celular de un usuario mediante su DNI."
)
async def actualizar_celular(dni: str, payload: ActualizarCelularRequest):
    """
    Endpoint secundario para ingresar o modificar manualmente el celular de una persona registrada.
    """
    dni_limpio = dni.strip()
    logger.info(f"Solicitud de actualización manual de celular para el DNI: {dni_limpio}")

    resultado = await AsistenciaService.actualizar_celular(dni=dni_limpio, celular=payload.celular)

    return AsistenciaResponse(
        success=True,
        message="Número de celular actualizado correctamente.",
        data=AsistenciaDetalle(
            id_asistencia=resultado.get("id_asistencia", 0),
            dni=resultado["dni"],
            nombre_completo=resultado["nombre_completo"],
            celular=resultado.get("celular"),
            fecha_hora=resultado.get("fecha_hora", ""),
            es_nuevo_registro=False
        )
    )