"""
Gestión de usuarios del sistema
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, Usuario
from functools import wraps

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

def coordinador_required(f):
    """Decorator para verificar que el usuario es coordinador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.puede_gestionar_usuarios():
            flash('No tienes permisos para gestionar usuarios', 'error')
            return redirect(url_for('dashboard.panel'))
        return f(*args, **kwargs)
    return decorated_function

@usuarios_bp.route('/')
@login_required
@coordinador_required
def lista():
    """Lista de usuarios del sistema"""
    usuarios = Usuario.query.order_by(Usuario.fecha_creacion.desc()).all()
    return render_template('usuarios/lista.html', usuarios=usuarios)

@usuarios_bp.route('/crear', methods=['GET', 'POST'])
@login_required
@coordinador_required
def crear():
    """Crear nuevo usuario"""
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            nombre = request.form.get('nombre', '').strip()
            password = request.form.get('password', '').strip()
            password_confirm = request.form.get('password_confirm', '').strip()
            rol = request.form.get('rol', '').strip()

            # Validaciones
            if not username or not nombre or not password or not rol:
                flash('Todos los campos son requeridos', 'error')
                return render_template('usuarios/crear.html')

            if password != password_confirm:
                flash('Las contraseñas no coinciden', 'error')
                return render_template('usuarios/crear.html')

            if len(password) < 6:
                flash('La contraseña debe tener al menos 6 caracteres', 'error')
                return render_template('usuarios/crear.html')

            if rol not in ['coordinador', 'secretaria', 'director']:
                flash('Rol inválido', 'error')
                return render_template('usuarios/crear.html')

            # Verificar que el username no exista
            if Usuario.query.filter_by(username=username).first():
                flash(f'El usuario "{username}" ya existe', 'error')
                return render_template('usuarios/crear.html')

            # Crear usuario
            nuevo_usuario = Usuario(
                username=username,
                nombre=nombre,
                rol=rol,
                activo=True
            )
            nuevo_usuario.set_password(password)

            db.session.add(nuevo_usuario)
            db.session.commit()

            flash(f'Usuario {username} creado exitosamente', 'success')
            return redirect(url_for('usuarios.lista'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creando usuario: {str(e)}', 'error')
            return render_template('usuarios/crear.html')

    return render_template('usuarios/crear.html')

@usuarios_bp.route('/<int:user_id>/editar', methods=['GET', 'POST'])
@login_required
@coordinador_required
def editar(user_id):
    """Editar usuario existente"""
    usuario = Usuario.query.get_or_404(user_id)

    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre', '').strip()
            rol = request.form.get('rol', '').strip()
            activo = request.form.get('activo') == 'on'
            cambiar_password = request.form.get('cambiar_password') == 'on'

            # Validaciones
            if not nombre or not rol:
                flash('Nombre y rol son requeridos', 'error')
                return render_template('usuarios/editar.html', usuario=usuario)

            if rol not in ['coordinador', 'secretaria', 'director']:
                flash('Rol inválido', 'error')
                return render_template('usuarios/editar.html', usuario=usuario)

            # No permitir desactivarse a sí mismo
            if usuario.id == current_user.id and not activo:
                flash('No puedes desactivarte a ti mismo', 'error')
                return render_template('usuarios/editar.html', usuario=usuario)

            # Actualizar datos
            usuario.nombre = nombre
            usuario.rol = rol
            usuario.activo = activo

            # Cambiar contraseña si se solicitó
            if cambiar_password:
                password = request.form.get('password', '').strip()
                password_confirm = request.form.get('password_confirm', '').strip()

                if not password:
                    flash('Debes ingresar una nueva contraseña', 'error')
                    return render_template('usuarios/editar.html', usuario=usuario)

                if password != password_confirm:
                    flash('Las contraseñas no coinciden', 'error')
                    return render_template('usuarios/editar.html', usuario=usuario)

                if len(password) < 6:
                    flash('La contraseña debe tener al menos 6 caracteres', 'error')
                    return render_template('usuarios/editar.html', usuario=usuario)

                usuario.set_password(password)

            db.session.commit()
            flash(f'Usuario {usuario.username} actualizado exitosamente', 'success')
            return redirect(url_for('usuarios.lista'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error actualizando usuario: {str(e)}', 'error')

    return render_template('usuarios/editar.html', usuario=usuario)

@usuarios_bp.route('/<int:user_id>/eliminar', methods=['POST'])
@login_required
@coordinador_required
def eliminar(user_id):
    """Eliminar (desactivar) usuario"""
    usuario = Usuario.query.get_or_404(user_id)

    # No permitir eliminarse a sí mismo
    if usuario.id == current_user.id:
        flash('No puedes eliminarte a ti mismo', 'error')
        return redirect(url_for('usuarios.lista'))

    try:
        # Solo desactivar, no eliminar
        usuario.activo = False
        db.session.commit()
        flash(f'Usuario {usuario.username} desactivado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error desactivando usuario: {str(e)}', 'error')

    return redirect(url_for('usuarios.lista'))

@usuarios_bp.route('/api/estadisticas')
@login_required
@coordinador_required
def api_estadisticas():
    """API para estadísticas de usuarios"""
    total = Usuario.query.count()
    activos = Usuario.query.filter_by(activo=True).count()
    inactivos = total - activos

    # Por rol
    coordinadores = Usuario.query.filter_by(rol='coordinador', activo=True).count()
    secretarias = Usuario.query.filter_by(rol='secretaria', activo=True).count()
    directores = Usuario.query.filter_by(rol='director', activo=True).count()

    return jsonify({
        'success': True,
        'total': total,
        'activos': activos,
        'inactivos': inactivos,
        'por_rol': {
            'coordinadores': coordinadores,
            'secretarias': secretarias,
            'directores': directores
        }
    })

@usuarios_bp.route('/perfil')
@login_required
def perfil():
    """Ver perfil del usuario actual"""
    # Obtener estadísticas del usuario
    cargas_realizadas = current_user.cargas_realizadas
    total_cargas = len(cargas_realizadas)

    # Calcular total de pagos procesados
    total_pagos_procesados = sum(c.registros_exitosos for c in cargas_realizadas)

    # Última actividad
    ultima_carga = cargas_realizadas[0] if cargas_realizadas else None

    return render_template('usuarios/perfil.html',
                         total_cargas=total_cargas,
                         total_pagos_procesados=total_pagos_procesados,
                         ultima_carga=ultima_carga,
                         cargas_recientes=cargas_realizadas[:5])

@usuarios_bp.route('/perfil/cambiar-password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    """Cambiar contraseña del usuario actual"""
    if request.method == 'POST':
        try:
            password_actual = request.form.get('password_actual', '').strip()
            password_nueva = request.form.get('password_nueva', '').strip()
            password_confirmar = request.form.get('password_confirmar', '').strip()

            # Validaciones
            if not password_actual or not password_nueva or not password_confirmar:
                flash('Todos los campos son requeridos', 'error')
                return redirect(url_for('usuarios.cambiar_password'))

            # Verificar contraseña actual
            if not current_user.check_password(password_actual):
                flash('La contraseña actual es incorrecta', 'error')
                return redirect(url_for('usuarios.cambiar_password'))

            # Verificar que las nuevas contraseñas coincidan
            if password_nueva != password_confirmar:
                flash('Las contraseñas nuevas no coinciden', 'error')
                return redirect(url_for('usuarios.cambiar_password'))

            # Validar longitud
            if len(password_nueva) < 6:
                flash('La contraseña debe tener al menos 6 caracteres', 'error')
                return redirect(url_for('usuarios.cambiar_password'))

            # Cambiar contraseña
            current_user.set_password(password_nueva)
            db.session.commit()

            flash('Contraseña actualizada exitosamente', 'success')
            return redirect(url_for('usuarios.perfil'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error cambiando contraseña: {str(e)}', 'error')

    return render_template('usuarios/cambiar_password.html')

@usuarios_bp.route('/configuracion')
@login_required
@coordinador_required
def configuracion():
    """Configuración del sistema (solo coordinadores)"""
    from models import Grado

    # Obtener todos los grados
    grados = Grado.query.order_by(Grado.id).all()

    # Estadísticas generales
    from models import Estudiante
    total_estudiantes = Estudiante.query.filter_by(activo=True).count()
    total_grados = Grado.query.filter_by(activo=True).count()

    return render_template('usuarios/configuracion.html',
                         grados=grados,
                         total_estudiantes=total_estudiantes,
                         total_grados=total_grados)

@usuarios_bp.route('/configuracion/grado/<int:grado_id>/editar', methods=['POST'])
@login_required
@coordinador_required
def editar_grado(grado_id):
    """Editar cuota de un grado"""
    from models import Grado

    grado = Grado.query.get_or_404(grado_id)

    try:
        nueva_cuota = request.form.get('cuota_mensual', type=float)

        if not nueva_cuota or nueva_cuota <= 0:
            flash('La cuota debe ser mayor a 0', 'error')
            return redirect(url_for('usuarios.configuracion'))

        grado.cuota_mensual = nueva_cuota
        db.session.commit()

        flash(f'Cuota de {grado.nombre} actualizada a Q{nueva_cuota:.2f}', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error actualizando cuota: {str(e)}', 'error')

    return redirect(url_for('usuarios.configuracion'))
