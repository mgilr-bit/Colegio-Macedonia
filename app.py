"""
Aplicación principal Flask - Colegio Cristiano Macedonia
Sistema de gestión de pagos estudiantiles
"""

import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_required, current_user
from config import config
from models import db, Usuario, init_db, crear_usuario_admin, obtener_resumen_pagos

def create_app(config_name=None):
    """Factory para crear la aplicación Flask"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones
    init_db(app)
    
    # Configurar Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        # Corregir warning de SQLAlchemy 2.0
        return db.session.get(Usuario, int(user_id))
    
    # Crear tablas y usuario admin si no existen
    with app.app_context():
        try:
            db.create_all()
            crear_usuario_admin()
        except Exception as e:
            print(f"⚠️ Error inicializando BD: {e}")
    
    # Registrar Blueprints (rutas)
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.estudiantes import estudiantes_bp
    from routes.pagos import pagos_bp
    from routes.reportes import reportes_bp
    from routes.usuarios import usuarios_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(estudiantes_bp)
    app.register_blueprint(pagos_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(usuarios_bp)
    
    # Rutas principales
    @app.route('/')
    def index():
        """Página principal - redirigir al dashboard o login"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.panel'))
        else:
            return redirect(url_for('auth.login'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Dashboard principal - obtener resumen"""
        try:
            resumen = obtener_resumen_pagos()
            return render_template('dashboard.html', 
                                 resumen=resumen,
                                 titulo="Panel Principal")
        except Exception as e:
            flash(f'Error cargando dashboard: {str(e)}', 'error')
            return render_template('dashboard.html', 
                                 resumen={},
                                 titulo="Panel Principal")
    
    @app.route('/favicon.ico')
    def favicon():
        """Favicon del sitio"""
        return '', 204
    
    # Manejadores de errores
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', 
                             error_code=404,
                             error_message="Página no encontrada"), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('error.html',
                             error_code=500,
                             error_message="Error interno del servidor"), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('error.html',
                             error_code=403,
                             error_message="No tienes permisos para acceder a esta página"), 403
    
    # Context processors (variables disponibles en todos los templates)
    @app.context_processor
    def inject_globals():
        """Inyectar variables globales en templates"""
        return {
            'app_name': 'Colegio Cristiano Macedonia',
            'current_user': current_user
        }
    
    # Filtros personalizados para templates
    @app.template_filter('currency')
    def currency_filter(amount):
        """Formatear cantidad como moneda"""
        if amount is None:
            return "Q0.00"
        return f"Q{float(amount):,.2f}"

    @app.template_filter('percentage')
    def percentage_filter(value):
        """Formatear como porcentaje"""
        if value is None:
            return "0%"
        return f"{float(value):.1f}%"

    @app.template_filter('mes_es')
    def mes_es_filter(mes):
        """Traducir mes de inglés a español"""
        from utils.meses import traducir_mes
        if mes is None:
            return ""
        return traducir_mes(mes, a_espanol=True)

    return app

def crear_archivos_blueprints():
    """Crear archivos de blueprints si no existen"""
    
    blueprints = {
        'routes/auth.py': '''"""
Rutas de autenticación - Login/Logout
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user
from models import Usuario, db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.panel'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Por favor completa todos los campos', 'error')
            return render_template('login.html')
        
        usuario = Usuario.query.filter_by(username=username, activo=True).first()
        
        if usuario and usuario.check_password(password):
            login_user(usuario)
            flash(f'¡Bienvenido {usuario.nombre}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.panel'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('auth.login'))
''',
        
        'routes/dashboard.py': '''"""
Dashboard principal del sistema
"""
from flask import Blueprint, render_template
from flask_login import login_required
from models import obtener_resumen_pagos

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def panel():
    """Panel principal del dashboard"""
    resumen = obtener_resumen_pagos()
    return render_template('dashboard.html', resumen=resumen)
''',
        
        'routes/estudiantes.py': '''"""
Gestión de estudiantes
"""
from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from models import Estudiante, Grado, db

estudiantes_bp = Blueprint('estudiantes', __name__, url_prefix='/estudiantes')

@estudiantes_bp.route('/')
@login_required
def lista():
    """Lista de estudiantes"""
    grado_id = request.args.get('grado_id', type=int)
    busqueda = request.args.get('busqueda', '')
    
    query = Estudiante.query.filter_by(activo=True)
    
    if grado_id:
        query = query.filter_by(grado_id=grado_id)
    
    if busqueda:
        query = query.filter(
            db.or_(
                Estudiante.nombre.ilike(f'%{busqueda}%'),
                Estudiante.carnet.like(f'%{busqueda}%')
            )
        )
    
    estudiantes = query.order_by(Estudiante.nombre).all()
    grados = Grado.query.filter_by(activo=True).order_by(Grado.nombre).all()
    
    return render_template('estudiantes/lista.html', 
                         estudiantes=estudiantes, 
                         grados=grados,
                         grado_seleccionado=grado_id,
                         busqueda=busqueda)
''',
        
        'routes/pagos.py': '''"""
Procesamiento de pagos
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user

pagos_bp = Blueprint('pagos', __name__, url_prefix='/pagos')

@pagos_bp.route('/subir')
@login_required
def subir():
    """Página para subir archivo del banco"""
    if not current_user.puede_cargar_archivos():
        flash('No tienes permisos para cargar archivos', 'error')
        return redirect(url_for('dashboard.panel'))
    
    return render_template('pagos/subir.html')
''',
        
        'routes/reportes.py': '''"""
Generación de reportes
"""
from flask import Blueprint, render_template
from flask_login import login_required

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')

@reportes_bp.route('/')
@login_required
def index():
    """Índice de reportes"""
    return render_template('reportes/index.html')
'''
    }
    
    for archivo, contenido in blueprints.items():
        if not os.path.exists(archivo):
            os.makedirs(os.path.dirname(archivo), exist_ok=True)
            with open(archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)
            print(f"✅ Creado: {archivo}")

# Crear aplicación
if __name__ == '__main__':
    # Crear archivos de blueprints si no existen
    crear_archivos_blueprints()
    
    print("🏫 COLEGIO CRISTIANO MACEDONIA - SISTEMA DE PAGOS")
    print("=" * 50)
    print("🌐 Servidor iniciando en: http://localhost:5000")
    print("👤 Usuario admin: admin / admin123")
    print("📊 Dashboard: http://localhost:5000/dashboard")
    print("=" * 50)
    
    # CORRECCIÓN: Crear la app correctamente
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)