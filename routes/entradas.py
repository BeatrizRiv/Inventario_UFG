from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, session
from db import conectar

entradas_bp = Blueprint('entradas', __name__)

VALOR_MIN = Decimal('0.01')
VALOR_MAX = Decimal('500000.00')


def validar_valor_activo(valor_raw):
    if valor_raw is None:
        return None, 'El valor es obligatorio.'
    texto = str(valor_raw).strip()
    if not texto or len(texto) > 12:
        return None, 'Valor no válido.'
    if 'e' in texto.lower() or not all(c.isdigit() or c in '.-' for c in texto) or texto.count('.') > 1:
        return None, 'Use solo números y hasta 2 decimales.'
    try:
        valor = Decimal(texto)
    except InvalidOperation:
        return None, 'Valor no válido.'
    if valor != valor.quantize(Decimal('0.01')):
        return None, 'El valor solo puede tener hasta 2 decimales.'
    if valor < VALOR_MIN or valor > VALOR_MAX:
        return None, f'El valor debe estar entre ${VALOR_MIN} y ${VALOR_MAX:,.2f}.'
    return float(valor), None

@entradas_bp.route('/entradas', methods=['GET', 'POST'])
def entradas():

    if 'usuario' not in session:
        return redirect(url_for('login.login'))

    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM areas WHERE estado=1")
    areas = cursor.fetchall()

    cursor.execute("SELECT * FROM responsables WHERE estado=1")
    responsables = cursor.fetchall()

    cursor.execute("SELECT * FROM tipos_activo")
    tipos = cursor.fetchall()

    cursor.execute("SELECT * FROM usos_activo")
    usos = cursor.fetchall()

    if request.method == 'POST':
        valor, error_valor = validar_valor_activo(request.form.get('valor'))
        if error_valor:
            conn.close()
            return render_template(
                "entradas.html",
                areas=areas,
                responsables=responsables,
                tipos=tipos,
                usos=usos,
                error_valor=error_valor,
            )

        cursor.execute(
            "SELECT depreciacion FROM tipos_activo WHERE id_tipo = %s",
            (request.form['id_tipo'],)
        )
        dep_row = cursor.fetchone()
        depreciacion = dep_row['depreciacion'] if dep_row else 0

        cursor.execute("""
            INSERT INTO activos_fijos 
            (codigo, nombre, descripcion, marca, modelo, serie, valor, depreciacion, fecha_ingreso, estado, id_area, id_responsable, id_tipo, id_uso)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.form['codigo'],
            request.form['nombre'],
            request.form['descripcion'],
            request.form['marca'],
            request.form['modelo'],
            request.form['serie'],
            valor,
            depreciacion,
            request.form['fecha_ingreso'],
            request.form['estado'],
            request.form['id_area'],
            request.form['id_responsable'],
            request.form['id_tipo'],
            request.form['id_uso']
        ))

        responsable_nombre = ''
        for r in responsables:
            if r['id_responsable'] == int(request.form['id_responsable']):
                responsable_nombre = r['nombre']
                break

        motivo = request.form.get('motivo', '').strip() or None
        detalle = f'Ingreso de activo fijo. Responsable asignado: {responsable_nombre}'

        cursor.execute("""
            INSERT INTO movimientos (tipo, id_activo, detalle, motivo, usuario)
            VALUES (%s, LAST_INSERT_ID(), %s, %s, %s)
        """, ('Entrada', detalle, motivo, session.get('usuario')))

        conn.commit()
        conn.close()

        return redirect(url_for('gestion.gestion'))

    conn.close()
    return render_template("entradas.html",
                           areas=areas,
                           responsables=responsables,
                           tipos=tipos,
                           usos=usos)