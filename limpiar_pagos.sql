-- ============================================================================
-- Script para limpiar pagos de la base de datos
-- Colegio Cristiano Macedonia
-- ============================================================================

-- OPCIÓN 1: Ver estadísticas antes de eliminar
-- ============================================================================
SELECT 'ESTADÍSTICAS DE PAGOS' as info;

SELECT
    'Total de pagos:' as descripcion,
    COUNT(*) as cantidad
FROM pagos;

SELECT
    'Pagos por mes:' as descripcion,
    mes,
    anio,
    COUNT(*) as cantidad
FROM pagos
GROUP BY mes, anio
ORDER BY anio DESC, mes DESC;

SELECT
    'Total de cargas:' as descripcion,
    COUNT(*) as cantidad
FROM cargas_archivo;

SELECT
    'Total de errores:' as descripcion,
    COUNT(*) as cantidad
FROM errores_procesamiento;


-- OPCIÓN 2: ELIMINAR TODOS LOS PAGOS Y CARGAS
-- ============================================================================
-- ADVERTENCIA: Esto eliminará TODOS los pagos, cargas y errores
-- Descomenta las líneas siguientes para ejecutar:

/*
BEGIN;

DELETE FROM errores_procesamiento;
DELETE FROM cargas_archivo;
DELETE FROM pagos;

COMMIT;

SELECT 'TODOS LOS PAGOS HAN SIDO ELIMINADOS' as resultado;
*/


-- OPCIÓN 3: ELIMINAR PAGOS DE UN MES ESPECÍFICO
-- ============================================================================
-- Ejemplo: Eliminar pagos de Octubre 2025
-- Cambia 'October' y 2025 según necesites

/*
BEGIN;

DELETE FROM pagos
WHERE mes = 'October' AND anio = 2025;

COMMIT;

SELECT 'Pagos eliminados' as resultado, ROW_COUNT() as cantidad;
*/


-- OPCIÓN 4: ELIMINAR PAGOS DE UN AÑO ESPECÍFICO
-- ============================================================================
-- Ejemplo: Eliminar pagos del año 2025

/*
BEGIN;

DELETE FROM pagos
WHERE anio = 2025;

COMMIT;

SELECT 'Pagos eliminados' as resultado, ROW_COUNT() as cantidad;
*/


-- OPCIÓN 5: ELIMINAR SOLO PAGOS DUPLICADOS (ÚLTIMO REGISTRO)
-- ============================================================================
-- Esto elimina pagos duplicados manteniendo el más antiguo

/*
BEGIN;

DELETE FROM pagos
WHERE id IN (
    SELECT id FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY estudiante_id, mes, anio
                   ORDER BY fecha_procesamiento DESC
               ) as rn
        FROM pagos
    ) duplicados
    WHERE rn > 1
);

COMMIT;

SELECT 'Pagos duplicados eliminados' as resultado;
*/


-- OPCIÓN 6: VER PAGOS ANTES DE ELIMINAR
-- ============================================================================
-- Verifica qué se va a eliminar antes de hacerlo

SELECT
    p.id,
    e.carnet,
    e.nombre,
    p.mes,
    p.anio,
    p.total_pagado,
    p.fecha_procesamiento
FROM pagos p
JOIN estudiantes e ON p.estudiante_id = e.id
WHERE p.mes = 'October' AND p.anio = 2025  -- Cambia según necesites
ORDER BY p.fecha_procesamiento DESC
LIMIT 100;


-- OPCIÓN 7: RESETEAR SECUENCIAS (IDs) DESPUÉS DE ELIMINAR TODO
-- ============================================================================
-- Esto reinicia los IDs a 1 después de eliminar todos los datos

/*
BEGIN;

DELETE FROM errores_procesamiento;
DELETE FROM cargas_archivo;
DELETE FROM pagos;

-- Reiniciar secuencias
ALTER SEQUENCE pagos_id_seq RESTART WITH 1;
ALTER SEQUENCE cargas_archivo_id_seq RESTART WITH 1;
ALTER SEQUENCE errores_procesamiento_id_seq RESTART WITH 1;

COMMIT;

SELECT 'Base de datos limpia y secuencias reiniciadas' as resultado;
*/


-- INSTRUCCIONES DE USO:
-- ============================================================================
-- 1. Primero ejecuta la OPCIÓN 1 para ver las estadísticas
-- 2. Elige la opción que necesites (2, 3, 4, 5, 6 o 7)
-- 3. Descomenta las líneas entre /* */ de la opción elegida
-- 4. Ejecuta el script en pgAdmin o en psql
-- 5. Verifica el resultado con la OPCIÓN 1 nuevamente
-- ============================================================================
