#!/usr/bin/env python3
"""
Script para importar estudiantes desde Excel a la base de datos
Colegio Cristiano Macedonia
"""

import pandas as pd
import psycopg2
import sys
from pathlib import Path

# Configuración de conexión a la base de datos
DB_CONFIG = {
    'host': 'colegio-macedonia.cy3eq0cae7y7.us-east-1.rds.amazonaws.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'root',
    'password': 'sa1989.midgir'
}

def conectar_db():
    """Conectar a la base de datos PostgreSQL"""
    try:
        print("Conectando a la base de datos...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Conexión exitosa!")
        return conn
    except psycopg2.Error as e:
        print(f"❌ Error de conexión: {e}")
        return None

def obtener_grados_db(conn):
    """Obtener mapping de nombres de grados a IDs"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM grados;")
        grados = cursor.fetchall()
        cursor.close()
        
        # Crear diccionario {nombre_grado: id}
        grados_dict = {nombre: id_grado for id_grado, nombre in grados}
        
        print(f"📚 Grados encontrados en BD: {len(grados_dict)}")
        for nombre, id_grado in grados_dict.items():
            print(f"   {id_grado}: {nombre}")
        
        return grados_dict
    except psycopg2.Error as e:
        print(f"❌ Error obteniendo grados: {e}")
        return None

def leer_excel_estudiantes(archivo_excel):
    """Leer el archivo Excel de estudiantes"""
    try:
        print(f"📖 Leyendo archivo: {archivo_excel}")
        
        # Leer Excel - basado en el análisis que hicimos
        df = pd.read_excel(archivo_excel, header=None)
        
        # Asignar nombres a las columnas basado en el análisis
        df.columns = ['carnet', 'grado', 'seccion', 'cuota', 'nombre']
        
        print(f"📊 Registros leídos: {len(df)}")
        print("🔍 Primeros 5 registros:")
        print(df.head())
        
        return df
    except Exception as e:
        print(f"❌ Error leyendo Excel: {e}")
        return None

def limpiar_datos(df):
    """Limpiar y validar los datos del Excel"""
    print("🧹 Limpiando datos...")
    
    # Eliminar filas con datos faltantes críticos
    df_limpio = df.dropna(subset=['carnet', 'nombre', 'grado'])
    
    # Convertir carnet a entero
    df_limpio['carnet'] = pd.to_numeric(df_limpio['carnet'], errors='coerce')
    df_limpio = df_limpio.dropna(subset=['carnet'])
    df_limpio['carnet'] = df_limpio['carnet'].astype(int)
    
    # Convertir cuota a float
    df_limpio['cuota'] = pd.to_numeric(df_limpio['cuota'], errors='coerce')
    
    # Limpiar nombres (quitar espacios extra)
    df_limpio['nombre'] = df_limpio['nombre'].str.strip()
    df_limpio['grado'] = df_limpio['grado'].str.strip()
    
    # Limpiar sección si existe
    if 'seccion' in df_limpio.columns:
        df_limpio['seccion'] = df_limpio['seccion'].fillna('')
        df_limpio['seccion'] = df_limpio['seccion'].astype(str).str.strip()
    
    print(f"✅ Registros después de limpieza: {len(df_limpio)}")
    print(f"📋 Grados únicos encontrados: {sorted(df_limpio['grado'].unique())}")
    
    return df_limpio

def importar_estudiantes(conn, df, grados_dict):
    """Importar estudiantes a la base de datos"""
    cursor = conn.cursor()
    
    exitosos = 0
    errores = 0
    errores_detalle = []
    
    print("📥 Importando estudiantes...")
    
    for index, row in df.iterrows():
        try:
            carnet = int(row['carnet'])
            nombre = str(row['nombre'])
            grado_nombre = str(row['grado'])
            seccion = str(row.get('seccion', '')) if pd.notna(row.get('seccion')) else None
            cuota_personalizada = float(row['cuota']) if pd.notna(row['cuota']) else None
            
            # Buscar ID del grado
            grado_id = grados_dict.get(grado_nombre)
            if not grado_id:
                raise ValueError(f"Grado '{grado_nombre}' no encontrado en la base de datos")
            
            # Insertar estudiante
            sql = """
            INSERT INTO estudiantes (carnet, nombre, grado_id, seccion, cuota_personalizada)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (carnet) DO UPDATE SET
                nombre = EXCLUDED.nombre,
                grado_id = EXCLUDED.grado_id,
                seccion = EXCLUDED.seccion,
                cuota_personalizada = EXCLUDED.cuota_personalizada;
            """
            
            cursor.execute(sql, (carnet, nombre, grado_id, seccion, cuota_personalizada))
            exitosos += 1
            
            # Mostrar progreso cada 50 registros
            if exitosos % 50 == 0:
                print(f"   📝 Procesados: {exitosos}/{len(df)}")
                
        except Exception as e:
            errores += 1
            error_msg = f"Fila {index + 1}: {str(e)}"
            errores_detalle.append(error_msg)
            print(f"   ❌ {error_msg}")
    
    # Confirmar cambios
    try:
        conn.commit()
        print(f"\n✅ Importación completada:")
        print(f"   📊 Exitosos: {exitosos}")
        print(f"   ❌ Errores: {errores}")
        
        if errores_detalle:
            print(f"\n📋 Detalle de errores:")
            for error in errores_detalle[:10]:  # Mostrar solo los primeros 10
                print(f"   • {error}")
            if len(errores_detalle) > 10:
                print(f"   ... y {len(errores_detalle) - 10} errores más")
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"❌ Error al confirmar cambios: {e}")
    
    cursor.close()
    return exitosos, errores

def verificar_importacion(conn):
    """Verificar la importación de estudiantes"""
    try:
        cursor = conn.cursor()
        
        # Contar estudiantes por grado
        sql = """
        SELECT g.nombre as grado, COUNT(e.id) as cantidad_estudiantes
        FROM grados g
        LEFT JOIN estudiantes e ON g.id = e.grado_id AND e.activo = true
        GROUP BY g.id, g.nombre
        ORDER BY g.id;
        """
        
        cursor.execute(sql)
        resultados = cursor.fetchall()
        
        print("\n📊 ESTUDIANTES POR GRADO:")
        print("=" * 50)
        total_estudiantes = 0
        for grado, cantidad in resultados:
            print(f"{grado:<25} {cantidad:>3} estudiantes")
            total_estudiantes += cantidad
        
        print("=" * 50)
        print(f"{'TOTAL':<25} {total_estudiantes:>3} estudiantes")
        
        # Verificar algunos registros
        cursor.execute("""
        SELECT e.carnet, e.nombre, g.nombre as grado, e.seccion, e.cuota_personalizada
        FROM estudiantes e
        JOIN grados g ON e.grado_id = g.id
        WHERE e.activo = true
        ORDER BY e.carnet
        LIMIT 5;
        """)
        
        ejemplos = cursor.fetchall()
        print(f"\n📋 EJEMPLOS DE ESTUDIANTES IMPORTADOS:")
        print("-" * 80)
        print(f"{'Carnet':<8} {'Nombre':<30} {'Grado':<20} {'Sección':<8} {'Cuota':<8}")
        print("-" * 80)
        for carnet, nombre, grado, seccion, cuota in ejemplos:
            seccion_str = seccion or '-'
            cuota_str = f"Q{cuota:.2f}" if cuota else '-'
            print(f"{carnet:<8} {nombre[:29]:<30} {grado:<20} {seccion_str:<8} {cuota_str:<8}")
        
        cursor.close()
        return total_estudiantes
        
    except psycopg2.Error as e:
        print(f"❌ Error verificando importación: {e}")
        return 0

def main():
    """Función principal"""
    print("🏫 IMPORTADOR DE ESTUDIANTES - COLEGIO CRISTIANO MACEDONIA")
    print("=" * 60)
    
    # Verificar archivo Excel
    archivo_excel = "base de datos alumnos.xlsx"
    if not Path(archivo_excel).exists():
        print(f"❌ Archivo no encontrado: {archivo_excel}")
        print("💡 Asegúrate de que el archivo esté en la misma carpeta que este script")
        return
    
    # Conectar a la base de datos
    conn = conectar_db()
    if not conn:
        print("❌ No se pudo conectar a la base de datos")
        return
    
    try:
        # Obtener grados de la base de datos
        grados_dict = obtener_grados_db(conn)
        if not grados_dict:
            print("❌ No se pudieron obtener los grados")
            return
        
        # Leer archivo Excel
        df = leer_excel_estudiantes(archivo_excel)
        if df is None:
            print("❌ No se pudo leer el archivo Excel")
            return
        
        # Limpiar datos
        df_limpio = limpiar_datos(df)
        if len(df_limpio) == 0:
            print("❌ No hay datos válidos para importar")
            return
        
        # Confirmar importación
        print(f"\n⚠️  ¿Continuar con la importación de {len(df_limpio)} estudiantes? (s/n): ", end="")
        respuesta = input().lower().strip()
        if respuesta != 's':
            print("❌ Importación cancelada")
            return
        
        # Importar estudiantes
        exitosos, errores = importar_estudiantes(conn, df_limpio, grados_dict)
        
        # Verificar importación
        total_importados = verificar_importacion(conn)
        
        print(f"\n🎉 ¡IMPORTACIÓN COMPLETADA!")
        print(f"📊 Total estudiantes en sistema: {total_importados}")
        print(f"✅ Registros procesados exitosamente: {exitosos}")
        if errores > 0:
            print(f"⚠️  Registros con errores: {errores}")
        
        print(f"\n📝 PRÓXIMOS PASOS:")
        print(f"   1. Verificar datos importados en pgAdmin")
        print(f"   2. Crear aplicación web Flask")
        print(f"   3. Implementar sistema de carga de pagos")
        
    finally:
        conn.close()
        print("\n✅ Conexión cerrada")

if __name__ == "__main__":
    main()