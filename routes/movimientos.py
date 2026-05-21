from flask import Blueprint, render_template, request, session, redirect, url_for
from db import conectar

movimientos_bp = Blueprint('movimientos', __name__)

@movimientos_bp.route('/movimientos', methods=['GET', 'POST'])
def movimientos():

    if 'usuario' not in session:
        return redirect(url_for('login.login'))

    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    tipo = request.values.get('tipo')
    fecha = request.values.get('fecha')

    query = """
        SELECT
            a.codigo,
            a.nombre AS activo,
            ar.nombre_area,
            m.tipo,
            m.fecha,
            m.detalle,
            m.motivo,
            m.usuario
        FROM movimientos m
        JOIN activos_fijos a ON m.id_activo = a.id_activo
        LEFT JOIN areas ar ON a.id_area = ar.id_area
        WHERE 1=1
    """

    valores = []

    if tipo and tipo != "Todos":
        query += " AND m.tipo = %s"
        valores.append(tipo)

    if fecha:
        query += " AND DATE(m.fecha) = %s"
        valores.append(fecha)

    query += " ORDER BY m.fecha DESC"

    cursor.execute(query, tuple(valores))
    movimientos = cursor.fetchall()

    conn.close()
    return render_template(
        "movimientos.html",
        movimientos=movimientos,
        filtro_tipo=tipo,
        filtro_fecha=fecha,
    )
