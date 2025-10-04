#!/usr/bin/env python3
"""
Script para verificar login directamente en base de datos
"""

import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

# Configuración de conexión
DB_CONFIG = {
    'host': 'colegio-macedonia.cy3eq0cae7y7.us-east-1.rds.amazonaws.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'root',
    'password': 'sa1989.midgir'
}

def verificar_y_arreglar_usuario():
    """Verificar y arreglar el usuario admin"""
    try:
        print("🔍 VERIFICANDO USUARIO ADMIN")
        print("=" * 40)
        
        # Conectar a la base de datos
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Verificar si existe la tabla usuarios
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'usuarios'
            );
        """)
        tabla_existe = cursor.fetchone()[0]
        
        if not tabla_existe:
            print("❌ La tabla 'usuarios' no existe")
            return
        
        print("✅ Tabla usuarios existe")
        
        # Buscar usuario admin
        cursor.execute("SELECT id, username, password_hash, rol, nombre, activo FROM usuarios WHERE username = 'admin';")
        usuario = cursor.fetchone()
        
        if usuario:
            print(f"✅ Usuario admin encontrado:")
            print(f"   ID: {usuario[0]}")
            print(f"   Username: {usuario[1]}")
            print(f"   Password Hash: {usuario[2][:50]}...")
            print(f"   Rol: {usuario[3]}")
            print(f"   Nombre: {usuario[4]}")
            print(f"   Activo: {usuario[5]}")
            
            # Verificar si la contraseña funciona
            password_correcto = check_password_hash(usuario[2], 'admin123')
            print(f"   Contraseña 'admin123' funciona: {password_correcto}")
            
            if not password_correcto:
                print("\n🔧 ARREGLANDO CONTRASEÑA...")
                nuevo_hash = generate_password_hash('admin123')
                cursor.execute("""
                    UPDATE usuarios 
                    SET password_hash = %s, activo = true 
                    WHERE username = 'admin';
                """, (nuevo_hash,))
                conn.commit()
                print("✅ Contraseña actualizada correctamente")
                
                # Verificar de nuevo
                password_correcto = check_password_hash(nuevo_hash, 'admin123')
                print(f"✅ Verificación final: {password_correcto}")
        else:
            print("❌ Usuario admin no encontrado")
            print("\n🔧 CREANDO USUARIO ADMIN...")
            
            nuevo_hash = generate_password_hash('admin123')
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, rol, nombre, activo) 
                VALUES (%s, %s, %s, %s, %s);
            """, ('admin', nuevo_hash, 'coordinador', 'Administrador del Sistema', True))
            conn.commit()
            
            print("✅ Usuario admin creado exitosamente")
        
        # Verificar que todo está bien
        cursor.execute("SELECT id, username, rol, activo FROM usuarios WHERE username = 'admin';")
        usuario_final = cursor.fetchone()
        
        print(f"\n📋 ESTADO FINAL:")
        print(f"   Usuario: admin")
        print(f"   Contraseña: admin123")
        print(f"   ID: {usuario_final[0]}")
        print(f"   Rol: {usuario_final[2]}")
        print(f"   Activo: {usuario_final[3]}")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ LISTO PARA USAR")
        print(f"Ve a: http://localhost:5000")
        print(f"Usuario: admin")
        print(f"Contraseña: admin123")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_hash_directamente():
    """Test del hash directamente"""
    print("\n🧪 TEST DE HASH:")
    password = 'admin123'
    hash1 = generate_password_hash(password)
    hash2 = generate_password_hash(password)
    
    print(f"Password: {password}")
    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Check 1: {check_password_hash(hash1, password)}")
    print(f"Check 2: {check_password_hash(hash2, password)}")

if __name__ == "__main__":
    test_hash_directamente()
    verificar_y_arreglar_usuario()