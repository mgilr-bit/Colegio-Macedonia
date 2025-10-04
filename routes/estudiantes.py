"""
Gestión de estudiantes - Módulo completo CORREGIDO
"""
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models import Estudiante, Grado, Pago, db
from datetime import datetime
from sqlalchemy import or_, desc, cast, String

estudiantes_bp = Blueprint('estudiantes', __name__, url_prefix='/estudiantes')

@estudiantes_bp.route('/')
@login_required
def lista():
    """Lista de estudiantes con filtros y búsqueda"""
    # Obtener parámetros de filtro
    grado_id = request.args.get('grado_id', type=int)
    busqueda = request.args.get('busqueda', '')
    estado_pago = request.args.get('estado_pago', 'todos')  # 'al_dia', 'moroso', 'todos'
    page = request.args.get('page', 1, type=int)
    per_page = 50  # Estudiantes por página
    
    # Construir query base
    query = Estudiante.query.filter_by(activo=True)
    
    # Filtro por grado
    if grado_id:
        query = query.filter_by(grado_id=grado_id)
    
    # Filtro por búsqueda (nombre o carnet) - CORREGIDO
    if busqueda:
        # Para búsqueda numérica (carnet)
        if busqueda.isdigit():
            carnet_busqueda = int(busqueda)
            query = query.filter(
                or_(
                    Estudiante.nombre.ilike(f'%{busqueda}%'),
                    Estudiante.carnet == carnet_busqueda,
                    cast(Estudiante.carnet, String).like(f'%{busqueda}%')
                )
            )
        else:
            # Solo buscar por nombre si no es número
            query = query.filter(Estudiante.nombre.ilike(f'%{busqueda}%'))
    
    # Obtener estudiantes con paginación
    try:
        estudiantes_pag = query.order_by(Estudiante.nombre).paginate(
            page=page, per_page=per_page, error_out=False
        )
    except Exception as e:
        print(f"Error en paginación: {e}")
        # Fallback sin filtros problemáticos
        query_simple = Estudiante.query.filter_by(activo=True)
        if grado_id:
            query_simple = query_simple.filter_by(grado_id=grado_id)
        estudiantes_pag = query_simple.order_by(Estudiante.nombre).paginate(
            page=page, per_page=per_page, error_out=False
        )
        flash('Error en la búsqueda, mostrando todos los estudiantes del grado', 'warning')
    
    # Si hay filtro por estado de pago, filtrar después
    if estado_pago and estado_pago != 'todos':
        mes_actual = datetime.now().strftime('%B')
        anio_actual = datetime.now().year
        
        estudiantes_filtrados = []
        for estudiante in estudiantes_pag.items:
            esta_al_dia = estudiante.esta_al_dia(mes_actual, anio_actual)
            
            if estado_pago == 'al_dia' and esta_al_dia:
                estudiantes_filtrados.append(estudiante)
            elif estado_pago == 'moroso' and not esta_al_dia:
                estudiantes_filtrados.append(estudiante)
        
        estudiantes_pag.items = estudiantes_filtrados
    
    # Obtener lista de grados para el filtro
    grados = Grado.query.filter_by(activo=True).order_by(Grado.nombre).all()
    
    # Estadísticas rápidas
    total_estudiantes = Estudiante.query.filter_by(activo=True).count()
    
    return render_template('estudiantes/lista.html',
                         estudiantes=estudiantes_pag,
                         grados=grados,
                         grado_seleccionado=grado_id,
                         busqueda=busqueda,
                         estado_pago=estado_pago,
                         total_estudiantes=total_estudiantes)

@estudiantes_bp.route('/<int:carnet>')
@login_required
def detalle(carnet):
    """Detalle de un estudiante específico"""
    estudiante = Estudiante.query.filter_by(carnet=carnet, activo=True).first_or_404()
    
    # Obtener historial de pagos
    pagos = Pago.query.filter_by(estudiante_id=estudiante.id)\
                     .order_by(desc(Pago.anio), desc(Pago.mes))\
                     .limit(12).all()
    
    # Verificar estado actual
    mes_actual = datetime.now().strftime('%B')
    anio_actual = datetime.now().year
    al_dia = estudiante.esta_al_dia(mes_actual, anio_actual)
    
    return render_template('estudiantes/detalle.html',
                         estudiante=estudiante,
                         pagos=pagos,
                         al_dia=al_dia,
                         mes_actual=mes_actual,
                         anio_actual=anio_actual)

@estudiantes_bp.route('/<int:carnet>/editar', methods=['GET', 'POST'])
@login_required
def editar(carnet):
    """Editar información de estudiante"""
    if not current_user.puede_editar_estudiantes():
        flash('No tienes permisos para editar estudiantes', 'error')
        return redirect(url_for('estudiantes.detalle', carnet=carnet))
    
    estudiante = Estudiante.query.filter_by(carnet=carnet, activo=True).first_or_404()
    
    if request.method == 'POST':
        try:
            # Actualizar información básica
            estudiante.nombre = request.form.get('nombre', '').strip()
            estudiante.seccion = request.form.get('seccion', '').strip()
            
            # Cuota personalizada (opcional)
            cuota_personalizada = request.form.get('cuota_personalizada', '').strip()
            if cuota_personalizada:
                estudiante.cuota_personalizada = float(cuota_personalizada)
            else:
                estudiante.cuota_personalizada = None
            
            # Observaciones
            estudiante.observaciones = request.form.get('observaciones', '').strip()
            
            # Grado (solo coordinador puede cambiar)
            if current_user.es_coordinador:
                nuevo_grado_id = request.form.get('grado_id', type=int)
                if nuevo_grado_id:
                    estudiante.grado_id = nuevo_grado_id
            
            db.session.commit()
            flash(f'Información de {estudiante.nombre} actualizada exitosamente', 'success')
            return redirect(url_for('estudiantes.detalle', carnet=carnet))
            
        except ValueError as e:
            flash(f'Error en el formato de datos: {str(e)}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error actualizando estudiante: {str(e)}', 'error')
    
    # Obtener grados para el select
    grados = Grado.query.filter_by(activo=True).order_by(Grado.nombre).all()

    # Verificar estado de pago actual
    mes_actual = datetime.now().strftime('%B')
    anio_actual = datetime.now().year
    al_dia = estudiante.esta_al_dia(mes_actual, anio_actual)

    return render_template('estudiantes/editar.html',
                         estudiante=estudiante,
                         grados=grados,
                         al_dia=al_dia)

@estudiantes_bp.route('/api/buscar')
@login_required
def api_buscar():
    """API para búsqueda de estudiantes (autocompletado)"""
    term = request.args.get('term', '').strip()
    
    if len(term) < 2:
        return jsonify([])
    
    try:
        # Búsqueda mejorada
        if term.isdigit():
            carnet_term = int(term)
            estudiantes = Estudiante.query.filter(
                Estudiante.activo == True,
                or_(
                    Estudiante.nombre.ilike(f'%{term}%'),
                    Estudiante.carnet == carnet_term,
                    cast(Estudiante.carnet, String).like(f'%{term}%')
                )
            ).limit(10).all()
        else:
            estudiantes = Estudiante.query.filter(
                Estudiante.activo == True,
                Estudiante.nombre.ilike(f'%{term}%')
            ).limit(10).all()
    except Exception as e:
        print(f"Error en búsqueda API: {e}")
        return jsonify([])
    
    resultados = []
    for est in estudiantes:
        resultados.append({
            'carnet': est.carnet,
            'nombre': est.nombre,
            'grado': est.grado.nombre,
            'al_dia': est.esta_al_dia()
        })
    
    return jsonify(resultados)

@estudiantes_bp.route('/api/estadisticas')
@login_required
def api_estadisticas():
    """API para estadísticas por grado"""
    mes_actual = datetime.now().strftime('%B')
    anio_actual = datetime.now().year
    
    grados = Grado.query.filter_by(activo=True).order_by(Grado.id).all()
    estadisticas = []
    
    for grado in grados:
        # Total estudiantes
        total = Estudiante.query.filter_by(grado_id=grado.id, activo=True).count()
        
        # Estudiantes al día
        al_dia = db.session.query(Estudiante.id).join(Pago).filter(
            Estudiante.grado_id == grado.id,
            Estudiante.activo == True,
            Pago.mes == mes_actual,
            Pago.anio == anio_actual
        ).distinct().count()
        
        morosos = total - al_dia
        
        estadisticas.append({
            'grado': grado.nombre,
            'total': total,
            'al_dia': al_dia,
            'morosos': morosos,
            'porcentaje_al_dia': round((al_dia / total * 100) if total > 0 else 0, 1)
        })
    
    return jsonify({
        'success': True,
        'estadisticas': estadisticas,
        'mes_actual': f"{mes_actual} {anio_actual}"
    })

@estudiantes_bp.route('/exportar')
@login_required
def exportar():
    """Exportar lista de estudiantes a Excel"""
    # Esta funcionalidad se puede implementar después
    flash('Funcionalidad de exportación próximamente', 'info')
    return redirect(url_for('estudiantes.lista'))