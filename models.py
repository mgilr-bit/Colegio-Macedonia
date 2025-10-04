"""
Modelos de base de datos para Colegio Cristiano Macedonia
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    """Modelo para usuarios del sistema"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # coordinador, secretaria, director
    nombre = db.Column(db.String(100), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    cargas_realizadas = db.relationship('CargaArchivo', backref='usuario', lazy=True)
    pagos_procesados = db.relationship('Pago', backref='procesado_por_usuario', lazy=True)
    
    def set_password(self, password):
        """Establecer contraseña con hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verificar contraseña"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def es_coordinador(self):
        return self.rol == 'coordinador'
    
    @property
    def es_secretaria(self):
        return self.rol == 'secretaria'
    
    @property
    def es_director(self):
        return self.rol == 'director'
    
    def puede_cargar_archivos(self):
        """Verificar si puede cargar archivos de pagos"""
        return self.rol in ['coordinador', 'secretaria']
    
    def puede_gestionar_usuarios(self):
        """Verificar si puede gestionar usuarios"""
        return self.rol == 'coordinador'
    
    def puede_editar_estudiantes(self):
        """Verificar si puede editar información de estudiantes"""
        return self.rol in ['coordinador', 'secretaria']
    
    def __repr__(self):
        return f'<Usuario {self.username} - {self.rol}>'

class Grado(db.Model):
    """Modelo para grados académicos"""
    __tablename__ = 'grados'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    nivel = db.Column(db.String(20), nullable=False)  # preprimaria, primaria, basico, diversificado
    cuota_mensual = db.Column(db.Numeric(8, 2), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    estudiantes = db.relationship('Estudiante', backref='grado', lazy=True)
    
    @property
    def total_estudiantes(self):
        """Total de estudiantes activos en este grado"""
        return Estudiante.query.filter_by(grado_id=self.id, activo=True).count()
    
    @property
    def estudiantes_al_dia(self):
        """Estudiantes al día en pagos este mes"""
        mes_actual = datetime.now().strftime('%B %Y')
        return db.session.query(Estudiante).join(Pago).filter(
            Estudiante.grado_id == self.id,
            Estudiante.activo == True,
            Pago.mes == mes_actual
        ).count()
    
    def __repr__(self):
        return f'<Grado {self.nombre}>'

class Estudiante(db.Model):
    """Modelo para estudiantes"""
    __tablename__ = 'estudiantes'
    
    id = db.Column(db.Integer, primary_key=True)
    carnet = db.Column(db.Integer, unique=True, nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    grado_id = db.Column(db.Integer, db.ForeignKey('grados.id'), nullable=False)
    seccion = db.Column(db.String(10))
    cuota_personalizada = db.Column(db.Numeric(8, 2))
    activo = db.Column(db.Boolean, default=True)
    fecha_ingreso = db.Column(db.Date, default=datetime.utcnow)
    observaciones = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    pagos = db.relationship('Pago', backref='estudiante', lazy=True, cascade='all, delete-orphan')
    
    @property
    def cuota_aplicable(self):
        """Cuota que aplica al estudiante (personalizada o del grado)"""
        return self.cuota_personalizada or self.grado.cuota_mensual
    
    def esta_al_dia(self, mes=None, anio=None):
        """Verificar si está al día en pagos"""
        if not mes:
            mes = datetime.now().strftime('%B')
        if not anio:
            anio = datetime.now().year
            
        pago = Pago.query.filter_by(
            estudiante_id=self.id,
            mes=mes,
            anio=anio
        ).first()
        
        return pago is not None
    
    def obtener_pago_mes(self, mes, anio):
        """Obtener pago de un mes específico"""
        return Pago.query.filter_by(
            estudiante_id=self.id,
            mes=f'{mes} {anio}'
        ).first()
    
    def historial_pagos(self, limite=12):
        """Obtener historial de pagos"""
        return Pago.query.filter_by(estudiante_id=self.id)\
                         .order_by(Pago.fecha_procesamiento.desc())\
                         .limit(limite).all()
    
    def __repr__(self):
        return f'<Estudiante {self.carnet} - {self.nombre}>'

class Pago(db.Model):
    """Modelo para pagos procesados"""
    __tablename__ = 'pagos'
    
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    mes = db.Column(db.String(20), nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    fecha_pago = db.Column(db.Date)
    boleta = db.Column(db.String(50))
    
    # Conceptos de pago
    inscripcion = db.Column(db.Numeric(8, 2), default=0)
    cuota = db.Column(db.Numeric(8, 2), default=0)
    utiles = db.Column(db.Numeric(8, 2), default=0)
    bus = db.Column(db.Numeric(8, 2), default=0)
    examenes = db.Column(db.Numeric(8, 2), default=0)
    bono = db.Column(db.Numeric(8, 2), default=0)
    seguro = db.Column(db.Numeric(8, 2), default=0)
    cursos = db.Column(db.Numeric(8, 2), default=0)
    otros = db.Column(db.Numeric(8, 2), default=0)
    mora = db.Column(db.Numeric(8, 2), default=0)
    
    total_pagado = db.Column(db.Numeric(8, 2), nullable=False)
    
    # Métodos de pago
    efectivo = db.Column(db.Numeric(8, 2), default=0)
    cheque_propios = db.Column(db.Numeric(8, 2), default=0)
    cheque_locales = db.Column(db.Numeric(8, 2), default=0)
    agencia_pago = db.Column(db.String(100))
    
    # Control y auditoría
    fecha_procesamiento = db.Column(db.DateTime, default=datetime.utcnow)
    procesado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    # Constraint para evitar duplicados
    __table_args__ = (db.UniqueConstraint('estudiante_id', 'mes', 'anio', name='_estudiante_mes_anio_uc'),)
    
    @property
    def mes_anio(self):
        """Formato legible del mes y año"""
        return f"{self.mes} {self.anio}"
    
    def __repr__(self):
        return f'<Pago {self.estudiante.carnet} - {self.mes} {self.anio} - Q{self.total_pagado}>'

class CargaArchivo(db.Model):
    """Modelo para auditoría de carga de archivos"""
    __tablename__ = 'cargas_archivo'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    fecha_carga = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    registros_procesados = db.Column(db.Integer, default=0)
    registros_exitosos = db.Column(db.Integer, default=0)
    registros_fallidos = db.Column(db.Integer, default=0)
    observaciones = db.Column(db.Text)
    
    # Relaciones
    errores = db.relationship('ErrorProcesamiento', backref='carga', lazy=True, cascade='all, delete-orphan')
    
    @property
    def porcentaje_exito(self):
        """Porcentaje de éxito en el procesamiento"""
        if self.registros_procesados == 0:
            return 0
        return round((self.registros_exitosos / self.registros_procesados) * 100, 2)
    
    def __repr__(self):
        return f'<CargaArchivo {self.nombre_archivo} - {self.fecha_carga}>'

class ErrorProcesamiento(db.Model):
    """Modelo para errores en procesamiento de archivos"""
    __tablename__ = 'errores_procesamiento'
    
    id = db.Column(db.Integer, primary_key=True)
    carga_id = db.Column(db.Integer, db.ForeignKey('cargas_archivo.id'), nullable=False)
    fila_excel = db.Column(db.Integer)
    carnet_estudiante = db.Column(db.Integer)
    error_descripcion = db.Column(db.Text)
    datos_fila = db.Column(db.JSON)
    fecha_error = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ErrorProcesamiento Fila {self.fila_excel} - {self.error_descripcion[:50]}>'

# Funciones utilitarias

def init_db(app):
    """Inicializar la base de datos con la aplicación Flask"""
    db.init_app(app)

def crear_usuario_admin():
    """Crear usuario administrador por defecto si no existe"""
    admin = Usuario.query.filter_by(username='admin').first()
    if not admin:
        admin = Usuario(
            username='admin',
            rol='coordinador',
            nombre='Administrador del Sistema'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuario administrador creado: admin/admin123")
    return admin

def obtener_resumen_pagos():
    """Obtener resumen general de pagos"""
    from datetime import datetime
    from utils.meses import traducir_mes

    # Obtener mes y año actual
    ahora = datetime.now()
    mes_actual_en = ahora.strftime('%B')  # 'January', 'February', etc.
    mes_actual_es = traducir_mes(mes_actual_en, a_espanol=True)
    anio_actual = ahora.year

    # Total de estudiantes activos
    total_estudiantes = Estudiante.query.filter_by(activo=True).count()

    # Estudiantes con pagos del mes actual
    estudiantes_al_dia = db.session.query(Estudiante.id).join(Pago).filter(
        Estudiante.activo == True,
        Pago.mes == mes_actual_en,
        Pago.anio == anio_actual
    ).distinct().count()

    # Estudiantes morosos (sin pago del mes actual)
    estudiantes_morosos = total_estudiantes - estudiantes_al_dia

    # Calcular porcentaje
    porcentaje_al_dia = round((estudiantes_al_dia / total_estudiantes) * 100, 2) if total_estudiantes > 0 else 0

    # Calcular recaudación estimada (estudiantes al día * cuota promedio)
    cuota_promedio = db.session.query(db.func.avg(Grado.cuota_mensual)).scalar() or 250
    recaudacion_estimada = estudiantes_al_dia * cuota_promedio

    print(f"🔍 Debug resumen pagos:")
    print(f"   Mes actual: {mes_actual_es} {anio_actual}")
    print(f"   Total estudiantes: {total_estudiantes}")
    print(f"   Al día: {estudiantes_al_dia}")
    print(f"   Morosos: {estudiantes_morosos}")

    return {
        'total_estudiantes': total_estudiantes,
        'estudiantes_al_dia': estudiantes_al_dia,
        'estudiantes_morosos': estudiantes_morosos,
        'porcentaje_al_dia': porcentaje_al_dia,
        'recaudacion_estimada': recaudacion_estimada,
        'mes_actual': f"{mes_actual_es} {anio_actual}"
    }