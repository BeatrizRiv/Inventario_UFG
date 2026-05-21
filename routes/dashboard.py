from flask import Blueprint, render_template, session, redirect, url_for
from db import conectar

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def dashboard():

    if 'usuario' not in session:
        return redirect(url_for('login.login'))

    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(*) AS total 
        FROM activos_fijos 
        WHERE estado != 'Retirado'
    """)
    total = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS activos 
        FROM activos_fijos 
        WHERE estado != 'Retirado'
    """)
    activos = cursor.fetchone()['activos']

    cursor.execute("""
        SELECT COUNT(*) AS retirados 
        FROM activos_fijos 
        WHERE estado = 'Retirado'
    """)
    retirados = cursor.fetchone()['retirados']

    cursor.execute("SELECT COUNT(*) AS movimientos FROM movimientos")
    movimientos = cursor.fetchone()['movimientos']

    cursor.execute("""
        SELECT m.tipo, a.codigo AS codigo_activo, m.fecha
        FROM movimientos m
        JOIN activos_fijos a ON m.id_activo = a.id_activo
        ORDER BY m.fecha DESC
        LIMIT 5
    """)
    ultimos_movimientos = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        activos=activos,
        retirados=retiros if False else retirados,  
        movimientos=movimientos,
        ultimos_movimientos=ultimos_movimientos
    )