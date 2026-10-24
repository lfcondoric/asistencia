import logging
from datetime import datetime
from typing import Dict, Any, Optional
import pymysql
from fastapi import HTTPException, status
from app.database import get_db_cursor
from app.services.reniec_service import ReniecService

logger = logging.getLogger(__name__)


class AsistenciaService:
    @staticmethod
    def buscar_asistente_local(dni: str) -> Optional[Dict[str, Any]]:
        """
        Consulta directa con SELECT en la tabla Asistente para verificar si el DNI existe.
        Retorna el registro completo (incluyendo celular y fecha de nacimiento) o None si no existe.
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    SELECT DNI, Nombres, Apellido_Paterno, Apellido_Materno, celular, Fecha_Nacimiento
                    FROM Asistente
                    WHERE DNI = %s
                """
                cursor.execute(query, (dni,))
                return cursor.fetchone()
        except pymysql.MySQLError as e:
            logger.error(f"Error al consultar el DNI {dni} en la tabla Asistente: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al consultar la base de datos: {str(e)}"
            )

    @classmethod
    async def procesar_asistencia(
        cls, 
        dni: str, 
        celular: Optional[str] = None, 
        fecha_nacimiento: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orquesta el registro de asistencia mediante consultas SQL directas:
        1. SELECT en 'Asistente' para verificar si el DNI ya existe.
        2. Si no existe: consulta RENIEC e INSERT en 'Asistente' con celular y fecha de nacimiento opcionales.
        3. Si ya existe y se envió celular o fecha de nacimiento distinta, los actualiza con UPDATE.
        4. INSERT en 'Registro_Asistencia' con el DNI y timestamp.
        5. Retorna el resultado estructurado para la respuesta JSON.
        """
        asistente = cls.buscar_asistente_local(dni)
        es_nuevo_registro = False

        try:
            with get_db_cursor() as cursor:
                if not asistente:
                    # ── DNI nuevo: consultar RENIEC e insertar en BD ─────────────────
                    logger.info(f"DNI {dni} no existe en la BD. Consultando RENIEC...")
                    datos_externos = await ReniecService.consultar_dni(dni)

                    nombres = datos_externos["nombres"].strip()
                    apellido_paterno = datos_externos["apellido_paterno"].strip()
                    apellido_materno = datos_externos["apellido_materno"].strip()

                    cursor.execute(
                        """
                        INSERT INTO Asistente (DNI, Nombres, Apellido_Paterno, Apellido_Materno, celular, Fecha_Nacimiento)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (dni, nombres, apellido_paterno, apellido_materno, celular, fecha_nacimiento)
                    )
                    es_nuevo_registro = True
                    celular_guardado = celular
                    fecha_nacimiento_guardada = fecha_nacimiento
                    logger.info(f"Nuevo asistente insertado: {dni} - {nombres} {apellido_paterno}")

                else:
                    # ── DNI existente: recuperar datos y actualizar celular/fecha si vienen nuevos ─
                    nombres = asistente["Nombres"]
                    apellido_paterno = asistente["Apellido_Paterno"]
                    apellido_materno = asistente["Apellido_Materno"]
                    celular_guardado = asistente.get("celular")
                    fn_actual = asistente.get("Fecha_Nacimiento")
                    fecha_nacimiento_guardada = str(fn_actual) if fn_actual else None

                    updates = []
                    params = []

                    # Actualizar celular si se envió uno y es distinto
                    if celular and celular != celular_guardado:
                        updates.append("celular = %s")
                        params.append(celular)
                        celular_guardado = celular

                    # Actualizar fecha de nacimiento si se envió una y es distinta
                    if fecha_nacimiento and fecha_nacimiento != fecha_nacimiento_guardada:
                        updates.append("Fecha_Nacimiento = %s")
                        params.append(fecha_nacimiento)
                        fecha_nacimiento_guardada = fecha_nacimiento

                    if updates:
                        params.append(dni)
                        sql_update = f"UPDATE Asistente SET {', '.join(updates)} WHERE DNI = %s"
                        cursor.execute(sql_update, tuple(params))
                        logger.info(f"Datos actualizados para DNI {dni}: celular={celular_guardado}, fecha_nacimiento={fecha_nacimiento_guardada}")
                    else:
                        logger.info(f"Asistente existente en BD: {dni} - {nombres} {apellido_paterno}")

                # ── Registrar asistencia ─────────────────────────────────────────────
                fecha_hora_actual = datetime.now()
                cursor.execute(
                    "INSERT INTO Registro_Asistencia (DNI_Asistente, Fecha_Hora) VALUES (%s, %s)",
                    (dni, fecha_hora_actual)
                )
                id_asistencia = cursor.lastrowid

            nombre_completo = f"{nombres} {apellido_paterno} {apellido_materno}".strip()

            return {
                "id_asistencia": id_asistencia,
                "dni": dni,
                "nombre_completo": nombre_completo,
                "celular": celular_guardado,
                "fecha_nacimiento": str(fecha_nacimiento_guardada) if fecha_nacimiento_guardada else None,
                "fecha_hora": fecha_hora_actual.strftime("%Y-%m-%d %H:%M:%S"),
                "es_nuevo_registro": es_nuevo_registro,
            }

        except pymysql.MySQLError as e:
            logger.error(f"Error al registrar la asistencia en MySQL para DNI {dni}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Fallo al registrar la asistencia en la base de datos: {str(e)}"
            )

    @staticmethod
    async def actualizar_celular(dni: str, celular: str) -> Dict[str, Any]:
        """
        Actualiza manualmente el número de celular de un asistente ya registrado.
        - Lanza 404 si el DNI no existe en la BD.
        - Ejecuta UPDATE Asistente SET celular = %s WHERE DNI = %s.
        - Retorna los datos actualizados del asistente.
        """
        try:
            with get_db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT DNI, Nombres, Apellido_Paterno, Apellido_Materno
                    FROM Asistente
                    WHERE DNI = %s
                    """,
                    (dni,)
                )
                asistente = cursor.fetchone()

                if not asistente:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=(
                            f"El DNI {dni} no está registrado en el sistema. "
                            f"El usuario debe marcar asistencia primero."
                        )
                    )

                cursor.execute(
                    "UPDATE Asistente SET celular = %s WHERE DNI = %s",
                    (celular, dni)
                )
                logger.info(f"Celular actualizado manualmente para DNI {dni}: {celular}")

                nombre_completo = (
                    f"{asistente['Nombres']} "
                    f"{asistente['Apellido_Paterno']} "
                    f"{asistente['Apellido_Materno']}"
                ).strip()

                return {
                    "dni": dni,
                    "nombre_completo": nombre_completo,
                    "celular": celular,
                }

        except HTTPException:
            raise
        except pymysql.MySQLError as e:
            logger.error(f"Error al actualizar el celular para DNI {dni}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Fallo al actualizar el celular en la base de datos: {str(e)}"
            )
