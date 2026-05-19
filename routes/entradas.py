from flask import Blueprint, render_template, request, redirect, url_for, session
from db import conectar

entradas_bp = Blueprint('entradas', __name__)

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
            request.form['valor'],
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

        cursor.execute("""
            INSERT INTO movimientos (tipo, id_activo, detalle, usuario)
            VALUES ('Entrada', LAST_INSERT_ID(), %s, %s)
        """, (f'Ingreso de activo. Responsable: {responsable_nombre}', session.get('usuario')))

        conn.commit()
        conn.close()

        return redirect(url_for('gestion.gestion'))

    conn.close()
    return render_template("entradas.html",
                           areas=areas,
                           responsables=responsables,
                           tipos=tipos,
                           usos=usos)