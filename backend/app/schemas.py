import re
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class AsistenciaRequest(BaseModel):
    dni: str = Field(
        ...,
        description="Documento Nacional de Identidad peruano (8 dígitos numéricos)",
        examples=["12345678"]
    )

    @field_validator("dni")
    @classmethod
    def validar_dni(cls, value: str) -> str:
        v = value.strip()
        if not re.match(r"^\d{8}$", v):
            raise ValueError("El DNI debe contener exactamente 8 dígitos numéricos.")
        return v


class AsistenciaDetalle(BaseModel):
    id_asistencia: int
    dni: str
    nombre_completo: str
    fecha_hora: str
    es_nuevo_registro: bool


class AsistenciaResponse(BaseModel):
    success: bool = True
    message: str
    data: AsistenciaDetalle


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    detail: Optional[str] = None
