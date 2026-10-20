import logging
from typing import Dict, Any
import httpx
from fastapi import HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)


class ReniecService:
    @staticmethod
    async def consultar_dni(dni: str) -> Dict[str, str]:
        """
        Consulta la información de nombres y apellidos del DNI en APISPeru.
        Concatena la ruta '/api/v1/dni/' a la URL base configurada.
        """
        # Se agrega la ruta fija de APISPeru /api/v1/dni/ antes del número de DNI
        base_url = settings.DNI_API_BASE_URL.rstrip("/")
        url = f"{base_url}/api/v1/dni/{dni}"

        headers = {}
        if settings.DNI_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.DNI_API_TOKEN}"

        # Simulación automática para pruebas locales
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
                if response.status_code == status.HTTP_404_NOT_FOUND:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"El DNI {dni} no fue encontrado en el registro nacional."
                    )

                # Si el token es inválido o expiró
                if response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
                    logger.error("Token de APISPeru inválido o no autorizado.")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Error de autenticación con el servicio externo de verificación de DNI."
                    )

                if response.status_code != status.HTTP_200_OK:
                    logger.error(f"API externa retornó código HTTP {response.status_code}: {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="El servicio externo de verificación de DNI no se encuentra disponible."
                    )

                try:
                    data: Dict[str, Any] = response.json()
                except ValueError:
                    logger.error("La respuesta de APISPeru no es un JSON válido.")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Respuesta inválida recibida del servicio externo de DNI."
                    )

                # Manejo del flag "success": false que devuelve APISPeru cuando falla la búsqueda
                if isinstance(data, dict) and data.get("success") is False:
                    mensaje_error = data.get("message", f"El DNI {dni} no fue encontrado.")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=mensaje_error
                    )

                # Mapeo de campos devueltos por APISPeru
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
            logger.error(f"Timeout al consultar APISPeru para el DNI: {dni}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Tiempo de espera agotado al consultar el servicio externo de verificación de DNI."
            )
        except httpx.RequestError as exc:
            logger.error(f"Error de conexión con APISPeru: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="No fue posible conectar con el servicio externo de verificación de DNI."
            )