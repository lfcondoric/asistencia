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
        Paso 1: Consulta directa con SELECT en la tabla Asistente para verificar si el DNI existe.
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    SELECT DNI, Nombres, Apellido_Paterno, Apellido_Materno 
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
    async def procesar_asistencia(cls, dni: str) -> Dict[str, Any]:
        """
        Orquesta el registro de asistencia mediante consultas SQL directas:
        1. SELECT en 'Asistente' para verificar si el DNI ya existe.
        2. Si no existe: consulta API externa e INSERT en 'Asistente'.
        3. INSERT en 'Registro_Asistencia' con el DNI y timestamp.
        4. Retorna el resultado estructurado para la respuesta JSON.
        """
        # 1. Verificar si el asistente existe en la tabla Asistente
        asistente = cls.buscar_asistente_local(dni)
        es_nuevo_registro = False

        try:
            with get_db_cursor() as cursor:
                # 2. Si no existe, consultar API externa e insertar en Asistente
                if not asistente:
                    logger.info(f"DNI {dni} no existe en la base de datos. Consultando API externa...")
                    datos_externos = await ReniecService.consultar_dni(dni)
                    
                    nombres = datos_externos["nombres"].strip()
                    apellido_paterno = datos_externos["apellido_paterno"].strip()
                    apellido_materno = datos_externos["apellido_materno"].strip()

                    query_insert_asistente = """
                        INSERT INTO Asistente (DNI, Nombres, Apellido_Paterno, Apellido_Materno)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(
                        query_insert_asistente,
                        (dni, nombres, apellido_paterno, apellido_materno)
                    )
                    es_nuevo_registro = True
                    logger.info(f"Nuevo asistente insertado con éxito: {dni} - {nombres} {apellido_paterno}")
                else:
                    nombres = asistente["Nombres"]
                    apellido_paterno = asistente["Apellido_Paterno"]
                    apellido_materno = asistente["Apellido_Materno"]
                    logger.info(f"Asistente existente encontrado en BD local: {dni} - {nombres} {apellido_paterno}")

                # 3. Registrar asistencia en la tabla Registro_Asistencia
                fecha_hora_actual = datetime.now()
                query_insert_asistencia = """
                    INSERT INTO Registro_Asistencia (DNI_Asistente, Fecha_Hora)
                    VALUES (%s, %s)
                """
                cursor.execute(query_insert_asistencia, (dni, fecha_hora_actual))
                id_asistencia = cursor.lastrowid

            nombre_completo = f"{nombres} {apellido_paterno} {apellido_materno}".strip()

            # 4. Retornar datos listos para el JSON
            return {
                "id_asistencia": id_asistencia,
                "dni": dni,
                "nombre_completo": nombre_completo,
                "fecha_hora": fecha_hora_actual.strftime("%Y-%m-%d %H:%M:%S"),
                "es_nuevo_registro": es_nuevo_registro
            }

        except pymysql.MySQLError as e:
            logger.error(f"Error al registrar la asistencia en MySQL para DNI {dni}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Fallo al registrar la asistencia en la base de datos: {str(e)}"
            )
