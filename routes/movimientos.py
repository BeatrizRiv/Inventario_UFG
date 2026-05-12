import re
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
            m.tipo,
            m.fecha,
            m.detalle,
            a.nombre AS activo,
            r.nombre AS responsable_actual
        FROM movimientos m
        JOIN activos_fijos a ON m.id_activo = a.id_activo
        LEFT JOIN responsables r ON a.id_responsable = r.id_responsable
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

    def parse_responsable_nuevo(detalle):
        if not detalle:
            return ''

        match = re.search(r'Responsable:\s*[^\-]+->\s*([^.;\n]+)', detalle)
        if match:
            return match.group(1).strip()

        match = re.search(r'Responsable:\s*([^.;\n]+)', detalle)
        return match.group(1).strip() if match else ''

    for m in movimientos:
        m['responsable_nuevo'] = parse_responsable_nuevo(m.get('detalle'))

    conn.close()
    return render_template("movimientos.html", movimientos=movimientos)