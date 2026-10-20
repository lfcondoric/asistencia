import logging
from typing import Dict, Any, Optional
import httpx
from fastapi import HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)


class ReniecService:
    @staticmethod
    async def consultar_dni(dni: str) -> Dict[str, str]:
        """
        Consulta la información de nombres y apellidos del DNI en la API externa.
        Maneja timeouts, errores de conexión y respuestas no exitosas.
        """
        url = f"{settings.DNI_API_BASE_URL}{dni}"
        headers = {}
        if settings.DNI_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.DNI_API_TOKEN}"

        # Simulación automática para pruebas locales si la URL es un mock/ejemplo
        if "api.ejemplo.com" in settings.DNI_API_BASE_URL or settings.DNI_API_TOKEN == "demo_token_secret":
            logger.info(f"[Modo Mock/Demo Activo] Simulando respuesta exitosa de RENIEC para DNI {dni}")
            return {
                "nombres": "JUAN CARLOS",
                "apellido_paterno": "PÉREZ",
                "apellido_materno": "GARCÍA"
            }

        try:
            async with httpx.AsyncClient(timeout=settings.DNI_API_TIMEOUT_SECONDS) as client:
                response = await client.get(url, headers=headers)

                # Si el DNI no existe en el registro civil o la API responde 404
                if response.status_code == status.HTTP_404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"El DNI {dni} no fue encontrado en el registro nacional."
                    )

                # Si el token es inválido o no autorizado
                if response.status_code in (status.HTTP_401, status.HTTP_403):
                    logger.error("Token de la API externa de DNI inválido o no autorizado.")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Error de autenticación con el servicio externo de verificación de DNI."
                    )

                if response.status_code != status.HTTP_200:
                    logger.error(f"API externa retornó código HTTP {response.status_code}: {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="El servicio externo de verificación de DNI no se encuentra disponible."
                    )

                data: Dict[str, Any] = response.json()

                # Normalización de campos comunes en APIs de DNI peruanas
                nombres = (
                    data.get("nombres")
                    or data.get("first_name")
                    or data.get("nombre")
                    or ""
                ).strip()

                apellido_paterno = (
                    data.get("apellidoPaterno")
                    or data.get("apellido_paterno")
                    or data.get("last_name")
                    or ""
                ).strip()

                apellido_materno = (
                    data.get("apellidoMaterno")
                    or data.get("apellido_materno")
                    or ""
                ).strip()

                if not nombres or not apellido_paterno:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="La API externa no retornó datos válidos para este DNI."
                    )

                return {
                    "nombres": nombres,
                    "apellido_paterno": apellido_paterno,
                    "apellido_materno": apellido_materno
                }

        except httpx.TimeoutException:
            logger.error(f"Timeout al consultar la API externa de DNI para: {dni}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Tiempo de espera agotado al consultar el servicio externo de verificación de DNI."
            )
        except httpx.RequestError as exc:
            logger.error(f"Error de conexión con la API externa de DNI: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="No fue posible conectar con el servicio externo de verificación de DNI."
            )
