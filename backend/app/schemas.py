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
    fecha_nacimiento: Optional[str] = Field(
        None,
        description="Fecha de nacimiento en formato AAAA-MM-DD (opcional)",
        examples=["1998-05-15"]
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

    @field_validator("fecha_nacimiento")
    @classmethod
    def validar_fecha_nacimiento(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        v = value.strip()
        if not v:
            return None
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("La fecha de nacimiento debe tener el formato AAAA-MM-DD.")
        try:
            from datetime import date
            f = datetime.strptime(v, "%Y-%m-%d").date()
            if f > date.today():
                raise ValueError("La fecha de nacimiento no puede ser una fecha futura.")
            if f.year < 1900:
                raise ValueError("El año de nacimiento debe ser mayor o igual a 1900.")
        except ValueError as err:
            if "fecha futura" in str(err) or "1900" in str(err):
                raise err
            raise ValueError("La fecha de nacimiento ingresada no es válida.")
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
    fecha_nacimiento: Optional[str] = None
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