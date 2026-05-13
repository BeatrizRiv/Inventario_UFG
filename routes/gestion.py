from flask import Blueprint, render_template, session, redirect, url_for, request
from db import conectar

gestion_bp = Blueprint('gestion', __name__)

@gestion_bp.route('/gestion')
def gestion():

    if 'usuario' not in session:
        return redirect(url_for('login.login'))

    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT 
        a.*, 
        ar.nombre_area,
        r.nombre AS responsable,
        t.nombre_tipo,
        u.nombre_uso
    FROM activos_fijos a
    LEFT JOIN areas ar ON a.id_area = ar.id_area
    LEFT JOIN responsables r ON a.id_responsable = r.id_responsable
    LEFT JOIN tipos_activo t ON a.id_tipo = t.id_tipo
    LEFT JOIN usos_activo u ON a.id_uso = u.id_uso
    WHERE a.estado != 'Retirado'
""")

    activos = cursor.fetchall()
    conn.close()

    return render_template("gestion.html", activos=activos)

@gestion_bp.route('/detalle/<codigo>')
def detalle_activo(codigo):
    if 'usuario' not in session:
        return redirect(url_for('login.login'))

    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            a.*, 
            ar.nombre_area,
            r.nombre AS responsable,
            t.nombre_tipo,
            u.nombre_uso
        FROM activos_fijos a
        LEFT JOIN areas ar ON a.id_area = ar.id_area
        LEFT JOIN responsables r ON a.id_responsable = r.id_responsable
        LEFT JOIN tipos_activo t ON a.id_tipo = t.id_tipo
        LEFT JOIN usos_activo u ON a.id_uso = u.id_uso
        WHERE a.codigo = %s
    """, (codigo,))
    activo = cursor.fetchone()

    if not activo:
        conn.close()
        return redirect(url_for('gestion.gestion'))

    cursor.execute("""
        SELECT m.*
        FROM movimientos m
        JOIN activos_fijos a ON m.id_activo = a.id_activo
        WHERE a.codigo = %s
        ORDER BY m.fecha DESC
    """, (codigo,))
    historial = cursor.fetchall()

    def extraer_responsable(detalle):
        if not detalle:
            return ''
        import re
        match = re.search(r'Responsable:\s*[^\-]+->\s*([^.;\n]+)', detalle)
        if match:
            return match.group(1).strip()
        match = re.search(r'Responsable:\s*([^.;\n]+)', detalle)
        return match.group(1).strip() if match else ''

    for m in historial:
        # Rellenar responsable: primero lo que ya está en el movimiento,
        # luego intentar extraerlo del texto `detalle`, finalmente usar el responsable actual del activo.
        responsable_existente = m.get('responsable')
        responsable_extraido = extraer_responsable(m.get('detalle'))
        m['responsable'] = responsable_existente or responsable_extraido or activo.get('responsable') or ''

        # Preparar campo de detalle/ubicación según lo que tenga el movimiento
        if m.get('ubicacion_destino'):
            m['detalle_ubicacion'] = m.get('ubicacion_destino')
        elif m.get('estado_nuevo'):
            m['detalle_ubicacion'] = f"Estado: {m.get('estado_nuevo')}"
        else:
            m['detalle_ubicacion'] = m.get('detalle', '')

    conn.close()
    return render_template('detalle_activo.html', activo=activo, historial=historial)


@gestion_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_activo(id):
    if 'usuario' not in session:
        return redirect(url_for('login.login'))

    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # Obtener depreciación basada en el tipo seleccionado
        cursor.execute(
            "SELECT depreciacion FROM tipos_activo WHERE id_tipo = %s",
            (request.form['id_tipo'],)
        )
        dep_row = cursor.fetchone()
        depreciacion = dep_row['depreciacion'] if dep_row else 0

        # Actualizar el activo
        cursor.execute("""
            UPDATE activos_fijos 
            SET codigo=%s, nombre=%s, descripcion=%s, marca=%s, modelo=%s, 
                serie=%s, valor=%s, depreciacion=%s, fecha_ingreso=%s, 
                estado=%s, id_area=%s, id_responsable=%s, id_tipo=%s, id_uso=%s
            WHERE id_activo=%s
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
            request.form['id_uso'],
            id
        ))

        # Registro de Auditoría (Movimiento)
        # cursor.execute("""
        #     INSERT INTO movimientos (tipo, id_activo, detalle)
        #     VALUES ('Actualiz', %s, %s)
        # """, (id, "Datos actualizados"))

        conn.commit()
        conn.close()
        # Idealmente usaríamos flash('Activo actualizado', 'success') aquí
        return redirect(url_for('gestion.gestion'))

    # Para el método GET, obtener todos los catálogos
    cursor.execute("SELECT * FROM areas WHERE estado=1")
    areas = cursor.fetchall()

    cursor.execute("SELECT * FROM responsables WHERE estado=1")
    responsables = cursor.fetchall()

    cursor.execute("SELECT * FROM tipos_activo")
    tipos = cursor.fetchall()

    cursor.execute("SELECT * FROM usos_activo")
    usos = cursor.fetchall()

    # Obtener los datos del activo específico, junto con la ubicación de su área
    cursor.execute("""
        SELECT a.*, ar.ubicacion AS nombre_area_ubicacion 
        FROM activos_fijos a 
        LEFT JOIN areas ar ON a.id_area = ar.id_area 
        WHERE a.id_activo = %s
    """, (id,))
    activo = cursor.fetchone()

    conn.close()

    if not activo:
        return redirect(url_for('gestion.gestion'))

    return render_template("editar.html", 
                           activo=activo,
                           areas=areas,
                           responsables=responsables,
                           tipos=tipos,
                           usos=usos)