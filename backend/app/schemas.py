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
    celular: Optional[str] = Field(
        None,
        description="Número de celular peruano (9 dígitos que empieza con 9, opcional)",
        examples=["987654321"]
    )

    @field_validator("dni")
    @classmethod
    def validar_dni(cls, value: str) -> str:
        v = value.strip()
        if not re.match(r"^\d{8}$", v):
            raise ValueError("El DNI debe contener exactamente 8 dígitos numéricos.")
        return v

    @field_validator("celular")
    @classmethod
    def validar_celular(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        v = value.strip()
        if not v:
            return None
        if not re.match(r"^9\d{8}$", v):
            raise ValueError("El celular debe tener exactamente 9 dígitos y empezar con el número 9.")
        return v


class ActualizarCelularRequest(BaseModel):
    celular: str = Field(
        ...,
        description="Número de celular peruano (9 dígitos que empieza con 9)",
        examples=["987654321"]
    )

    @field_validator("celular")
    @classmethod
    def validar_celular(cls, value: str) -> str:
        v = value.strip()
        if not re.match(r"^9\d{8}$", v):
            raise ValueError("El celular debe tener exactamente 9 dígitos y empezar con el número 9.")
        return v


class AsistenciaDetalle(BaseModel):
    id_asistencia: int
    dni: str
    nombre_completo: str
    celular: Optional[str] = None
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