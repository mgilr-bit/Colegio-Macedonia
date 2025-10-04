"""
Procesamiento de pagos
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from utils.excel_processor import ExcelProcessor
from models import db, CargaArchivo, ErrorProcesamiento

pagos_bp = Blueprint('pagos', __name__, url_prefix='/pagos')

@pagos_bp.route('/subir')
@login_required
def subir():
    """Página para subir archivo del banco"""
    if not current_user.puede_cargar_archivos():
        flash('No tienes permisos para cargar archivos', 'error')
        return redirect(url_for('dashboard.panel'))
    
    return render_template('pagos/subir.html')

@pagos_bp.route('/procesar', methods=['POST'])
@login_required
def procesar():
    """Procesar archivo Excel del banco - CORREGIDO"""
    if not current_user.puede_cargar_archivos():
        flash('No tienes permisos para cargar archivos', 'error')
        return redirect(url_for('dashboard.panel'))
    
    try:
        # Verificar que se subió un archivo
        if 'archivo' not in request.files:
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('pagos.subir'))
        
        archivo = request.files['archivo']
        
        if archivo.filename == '':
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('pagos.subir'))
        
        # Inicializar procesador
        processor = ExcelProcessor()
        
        # Validar archivo
        if not processor.es_archivo_valido(archivo.filename):
            flash('Tipo de archivo no válido. Solo se permiten archivos .xlsx y .xls', 'error')
            return redirect(url_for('pagos.subir'))
        
        # Guardar archivo
        ruta_archivo, nombre_archivo = processor.guardar_archivo(archivo)
        
        # Validar estructura
        valido, mensaje = processor.validar_archivo_estructura(ruta_archivo)
        if not valido:
            flash(f'Estructura de archivo inválida: {mensaje}', 'error')
            return redirect(url_for('pagos.subir'))
        
        # Procesar archivo
        exito, resultados = processor.procesar_archivo_banco(ruta_archivo, current_user.id)
        
        print(f"🔍 Debug procesamiento - Éxito: {exito}, Resultados: {resultados}")
        
        if exito:
            # CORRECCIÓN: Mostrar página de resultados en lugar de redirect
            print(f"✅ Procesamiento exitoso: {resultados['exitosos']} pagos, {resultados['duplicados']} duplicados")
            return render_template('resultados.html', resultados=resultados)
        else:
            flash(f'Error procesando archivo: {resultados.get("error", "Error desconocido")}', 'error')
            return redirect(url_for('pagos.subir'))
    
    except Exception as e:
        print(f"❌ Error en procesamiento: {str(e)}")
        flash(f'Error interno: {str(e)}', 'error')
        return redirect(url_for('pagos.subir'))

@pagos_bp.route('/historial')
@login_required
def historial():
    """Historial de cargas de archivos"""
    cargas = CargaArchivo.query.filter_by(usuario_id=current_user.id)\
                              .order_by(CargaArchivo.fecha_carga.desc())\
                              .limit(20).all()
    
    return render_template('pagos/historial.html', cargas=cargas)

@pagos_bp.route('/detalle/<int:carga_id>')
@login_required
def detalle_carga(carga_id):
    """Detalle de una carga específica"""
    carga = CargaArchivo.query.get_or_404(carga_id)
    
    # Verificar permisos
    if not current_user.puede_cargar_archivos() and carga.usuario_id != current_user.id:
        flash('No tienes permisos para ver este detalle', 'error')
        return redirect(url_for('pagos.historial'))
    
    # Obtener errores si los hay
    errores = ErrorProcesamiento.query.filter_by(carga_id=carga_id).all()
    
    return render_template('pagos/detalle.html', carga=carga, errores=errores)