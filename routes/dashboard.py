"""
Dashboard principal del sistema
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from models import obtener_resumen_pagos, Grado, Estudiante, Pago, db
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def panel():
    """Panel principal del dashboard"""
    resumen = obtener_resumen_pagos()
    return render_template('dashboard.html', resumen=resumen)

@dashboard_bp.route('/api/datos-grado')
@login_required  
def datos_por_grado():
    """API para obtener datos reales por grado para el gráfico"""
    try:
        # Obtener mes y año actual
        ahora = datetime.now()
        mes_actual = ahora.strftime('%B')
        anio_actual = ahora.year
        
        # Consulta para obtener datos por grado
        grados_datos = []
        grados = Grado.query.filter_by(activo=True).order_by(Grado.id).all()
        
        for grado in grados:
            # Total de estudiantes en el grado
            total_estudiantes = Estudiante.query.filter_by(
                grado_id=grado.id, 
                activo=True
            ).count()
            
            # Estudiantes al día en este grado
            estudiantes_al_dia = db.session.query(Estudiante.id).join(Pago).filter(
                Estudiante.grado_id == grado.id,
                Estudiante.activo == True,
                Pago.mes == mes_actual,
                Pago.anio == anio_actual
            ).distinct().count()
            
            # Estudiantes morosos en este grado
            estudiantes_morosos = total_estudiantes - estudiantes_al_dia
            
            grados_datos.append({
                'grado': grado.nombre,
                'al_dia': estudiantes_al_dia,
                'morosos': estudiantes_morosos,
                'total': total_estudiantes
            })
        
        return jsonify({
            'success': True,
            'datos': grados_datos,
            'mes_actual': f"{mes_actual} {anio_actual}"
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500