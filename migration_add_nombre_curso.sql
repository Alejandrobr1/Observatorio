-- =====================================================
-- Migración: Agregar columna NOMBRE_CURSO a Persona_Nivel_MCER
-- =====================================================
-- Esta migración añade la columna NOMBRE_CURSO a la tabla Persona_Nivel_MCER
-- para permitir filtros por tipo de curso (e.g., intensificación)

-- 1. Verificar si la columna ya existe antes de crearla
ALTER TABLE Persona_Nivel_MCER ADD COLUMN NOMBRE_CURSO VARCHAR(200) NULL;

-- 2. Verificar resultados
SELECT 'Migración completada exitosamente.' as mensaje;
SELECT COUNT(*) as total_registros FROM Persona_Nivel_MCER;
SELECT COUNT(NOMBRE_CURSO) as registros_con_nombre_curso FROM Persona_Nivel_MCER WHERE NOMBRE_CURSO IS NOT NULL;
