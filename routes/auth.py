"""
Rutas de autenticación - Login/Logout
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
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
        
        print(f"🔍 Intento de login - Usuario: {username}")
        
        if not username or not password:
            flash('Por favor completa todos los campos', 'error')
            return render_template('login.html')
        
        try:
            # Buscar usuario
            usuario = Usuario.query.filter_by(username=username).first()
            print(f"🔍 Usuario encontrado: {usuario}")
            
            if usuario:
                print(f"🔍 Usuario activo: {usuario.activo}")
                print(f"🔍 Rol: {usuario.rol}")
                
                # Verificar contraseña
                password_ok = usuario.check_password(password)
                print(f"🔍 Contraseña correcta: {password_ok}")
                
                if password_ok and usuario.activo:
                    login_user(usuario)
                    flash(f'¡Bienvenido {usuario.nombre}!', 'success')
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('dashboard.panel'))
                else:
                    flash('Usuario o contraseña incorrectos', 'error')
            else:
                flash('Usuario no encontrado', 'error')
                
        except Exception as e:
            print(f"❌ Error en login: {e}")
            flash('Error interno del sistema', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('auth.login'))