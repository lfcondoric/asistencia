-- =============================================================================
-- SISTEMA DE CONTROL DE ASISTENCIA
-- Definición de Base de Datos y Tablas (100% compatible con MariaDB / MySQL)
-- =============================================================================

-- 1. Base de Datos
CREATE DATABASE IF NOT EXISTS db_asistencia
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE db_asistencia;

-- 2. Tabla: Asistente
CREATE TABLE IF NOT EXISTS Asistente (
    DNI CHAR(8) NOT NULL,
    Nombres VARCHAR(100) NOT NULL,
    Apellido_Paterno VARCHAR(100) NOT NULL,
    Apellido_Materno VARCHAR(100) NOT NULL,
    celular VARCHAR(9) NULL,
    Fecha_Registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (DNI)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 3. Tabla: Registro_Asistencia
CREATE TABLE IF NOT EXISTS Registro_Asistencia (
    ID_Asistencia INT NOT NULL AUTO_INCREMENT,
    DNI_Asistente CHAR(8) NOT NULL,
    Fecha_Hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ID_Asistencia),
    CONSTRAINT FK_Registro_Asistente FOREIGN KEY (DNI_Asistente)
        REFERENCES Asistente(DNI)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 4. Índices para reportes y búsquedas
CREATE INDEX IF NOT EXISTS IDX_Registro_DNI ON Registro_Asistencia(DNI_Asistente);
CREATE INDEX IF NOT EXISTS IDX_Registro_Fecha ON Registro_Asistencia(Fecha_Hora);