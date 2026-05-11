from flask import Blueprint, render_template, request, session, redirect, url_for
from db import conectar

busqueda_bp = Blueprint('busqueda', __name__)

@busqueda_bp.route('/busqueda', methods=['GET', 'POST'])
def busqueda():

    if 'usuario' not in session:
        return redirect(url_for('login.login'))

    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    resultados = []

    if request.method == 'POST':
        dato = request.form['busqueda']

        cursor.execute("""
            SELECT 
                a.codigo,
                a.serie,       
                a.nombre,
                a.estado,
                ar.nombre_area,
                r.nombre AS responsable
            FROM activos_fijos a
            LEFT JOIN areas ar ON a.id_area = ar.id_area
            LEFT JOIN responsables r ON a.id_responsable = r.id_responsable
            WHERE a.codigo LIKE %s OR a.serie LIKE %s OR a.nombre LIKE %s
        """, (f"%{dato}%", f"%{dato}%", f"%{dato}%"))

        resultados = cursor.fetchall()

    conn.close()
    return render_template("busqueda.html", resultados=resultados)