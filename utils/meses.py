"""
Utilidades para manejo de meses en español
"""
from datetime import datetime

# Mapeo de meses inglés a español
MESES_ES = {
    'January': 'Enero',
    'February': 'Febrero',
    'March': 'Marzo',
    'April': 'Abril',
    'May': 'Mayo',
    'June': 'Junio',
    'July': 'Julio',
    'August': 'Agosto',
    'September': 'Septiembre',
    'October': 'Octubre',
    'November': 'Noviembre',
    'December': 'Diciembre'
}

# Mapeo inverso español a inglés
MESES_EN = {v: k for k, v in MESES_ES.items()}

def mes_actual_es():
    """Obtener mes actual en español"""
    mes_en = datetime.now().strftime('%B')
    return MESES_ES.get(mes_en, mes_en)

def mes_actual_en():
    """Obtener mes actual en inglés (para BD)"""
    return datetime.now().strftime('%B')

def traducir_mes(mes, a_espanol=True):
    """
    Traducir mes de inglés a español o viceversa

    Args:
        mes: Nombre del mes
        a_espanol: True para traducir a español, False para inglés

    Returns:
        Nombre del mes traducido
    """
    if a_espanol:
        return MESES_ES.get(mes, mes)
    else:
        return MESES_EN.get(mes, mes)

def obtener_nombre_mes(numero_mes):
    """
    Obtener nombre del mes en español a partir del número

    Args:
        numero_mes: Número del mes (1-12)

    Returns:
        Nombre del mes en español
    """
    meses_ordenados = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]

    if 1 <= numero_mes <= 12:
        return meses_ordenados[numero_mes - 1]
    return ''

def obtener_numero_mes(nombre_mes):
    """
    Obtener número del mes a partir del nombre en español o inglés

    Args:
        nombre_mes: Nombre del mes en español o inglés

    Returns:
        Número del mes (1-12)
    """
    meses_ordenados_es = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]

    meses_ordenados_en = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]

    # Buscar en español
    if nombre_mes in meses_ordenados_es:
        return meses_ordenados_es.index(nombre_mes) + 1

    # Buscar en inglés
    if nombre_mes in meses_ordenados_en:
        return meses_ordenados_en.index(nombre_mes) + 1

    return 0
