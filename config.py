"""
Configuración del proyecto Flask - Colegio Cristiano Macedonia
"""

import os
from datetime import timedelta

class Config:
    """Configuración para desarrollo"""
    
    # Configuración Flask
    SECRET_KEY = 'colegio-macedonia-secret-key-2025'
    DEBUG = True
    
    # Configuración de base de datos PostgreSQL
    DB_HOST = 'colegio-macedonia.cy3eq0cae7y7.us-east-1.rds.amazonaws.com'
    DB_PORT = 5432
    DB_NAME = 'postgres'
    DB_USER = 'root'
    DB_PASSWORD = 'sa1989.midgir'
    
    # URI de SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'connect_timeout': 10
        }
    }
    
    # Configuración de sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    
    # Configuración de archivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB máximo
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    
    # Configuración de reportes
    REPORTS_FOLDER = 'static/reports'

# Para simplificar el desarrollo
config = {
    'development': Config,
    'default': Config
}