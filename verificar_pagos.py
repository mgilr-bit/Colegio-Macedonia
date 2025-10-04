#!/usr/bin/env python3
"""
Script para verificar pagos en la base de datos
"""
from app import create_app
from models import db, Pago, Estudiante
from datetime import datetime

app = create_app()

with app.app_context():
    # Mes actual
    mes_actual = datetime.now().strftime('%B')
    anio_actual = datetime.now().year

    print(f"🔍 Verificando pagos para: {mes_actual} {anio_actual}")
    print("=" * 60)

    # Total de pagos
    total_pagos = Pago.query.count()
    print(f"📊 Total de pagos en BD: {total_pagos}")

    # Pagos del mes actual
    pagos_mes = Pago.query.filter_by(mes=mes_actual, anio=anio_actual).all()
    print(f"📅 Pagos de {mes_actual} {anio_actual}: {len(pagos_mes)}")

    # Listar algunos pagos
    if pagos_mes:
        print(f"\n📋 Primeros 10 pagos del mes:")
        for pago in pagos_mes[:10]:
            estudiante = Estudiante.query.get(pago.estudiante_id)
            if estudiante:
                print(f"   - Carnet {estudiante.carnet}: {estudiante.nombre} - Q{pago.total_pagado}")

    # Verificar meses únicos en la BD
    meses_unicos = db.session.query(Pago.mes, Pago.anio).distinct().all()
    print(f"\n📆 Meses con pagos registrados:")
    for mes, anio in meses_unicos:
        cantidad = Pago.query.filter_by(mes=mes, anio=anio).count()
        print(f"   - {mes} {anio}: {cantidad} pagos")

    # Estudiantes activos
    total_estudiantes = Estudiante.query.filter_by(activo=True).count()
    print(f"\n👥 Total estudiantes activos: {total_estudiantes}")

    # Verificar query del dashboard
    estudiantes_al_dia = db.session.query(Estudiante.id).join(Pago).filter(
        Estudiante.activo == True,
        Pago.mes == mes_actual,
        Pago.anio == anio_actual
    ).distinct().count()

    print(f"✅ Estudiantes al día ({mes_actual} {anio_actual}): {estudiantes_al_dia}")
    print(f"❌ Estudiantes morosos: {total_estudiantes - estudiantes_al_dia}")

    print("\n" + "=" * 60)
