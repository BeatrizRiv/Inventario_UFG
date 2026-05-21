from flask import Blueprint, render_template, request, redirect, url_for, session
from db import conectar

traslados_bp = Blueprint('traslados', __name__)

@traslados_bp.route('/buscar_activo', methods=['GET'])
def buscar_activo():
    if 'usuario' not in session:
        return {"error": "No autorizado"}, 401

    codigo = request.args.get('codigo')
    if not codigo:
        return {"error": "Código requerido"}, 400

    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            a.codigo,
            a.serie,
            a.nombre,
            ar.nombre_area AS area,
            r.nombre AS responsable,
            u.nombre_uso AS uso,
            a.estado
        FROM activos_fijos a
        LEFT JOIN areas ar ON a.id_area = ar.id_area
        LEFT JOIN responsables r ON a.id_responsable = r.id_responsable
        LEFT JOIN usos_activo u ON a.id_uso = u.id_uso
        WHERE a.codigo = %s
    """, (codigo,))

    activo = cursor.fetchone()
    conn.close()

    if not activo:
        return {"error": "Activo no encontrado"}

    return activo

@traslados_bp.route('/traslados', methods=['GET', 'POST'])
def traslados():
    if 'usuario' not in session:
        return redirect(url_for('login.login'))

    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM areas WHERE estado=1")
    areas = cursor.fetchall()

    cursor.execute("SELECT * FROM responsables WHERE estado=1")
    responsables = cursor.fetchall()

    cursor.execute("SELECT * FROM usos_activo")
    usos = cursor.fetchall()

    estados = ['Disponible', 'En uso', 'Mantenimiento', 'Depreciado', 'Retirado']

    if request.method == 'POST':
        codigo = request.form.get('codigo')
        motivo = request.form.get('motivo', '').strip() or None

        cursor.execute("SELECT * FROM activos_fijos WHERE codigo=%s", (codigo,))
        activo = cursor.fetchone()

        if not activo:
            conn.close()
            return "❌ Activo no encontrado"

        id_activo = activo['id_activo']

        nueva_area = request.form.get('id_area')
        nuevo_responsable = request.form.get('id_responsable')
        nuevo_uso = request.form.get('id_uso')
        nuevo_estado = request.form.get('estado')

        cambios = []
        updates = []
        valores_update = []
        
        if nueva_area and activo['id_area'] is not None and int(nueva_area) != activo['id_area'] or nueva_area and activo['id_area'] is None:
            cursor.execute("SELECT nombre_area FROM areas WHERE id_area=%s", (nueva_area,))
            row = cursor.fetchone()
            nombre_n = row['nombre_area'] if row else ''
            cambios.append(f"Área -> {nombre_n}")
            updates.append("id_area=%s")
            valores_update.append(nueva_area)

        if nuevo_responsable and activo['id_responsable'] is not None and int(nuevo_responsable) != activo['id_responsable'] or nuevo_responsable and activo['id_responsable'] is None:
            cursor.execute("SELECT nombre FROM responsables WHERE id_responsable=%s", (nuevo_responsable,))
            row = cursor.fetchone()
            nombre_n = row['nombre'] if row else ''
            cambios.append(f"Responsable -> {nombre_n}")
            updates.append("id_responsable=%s")
            valores_update.append(nuevo_responsable)

        if nuevo_uso and activo['id_uso'] is not None and int(nuevo_uso) != activo['id_uso'] or nuevo_uso and activo['id_uso'] is None:
            cursor.execute("SELECT nombre_uso FROM usos_activo WHERE id_uso=%s", (nuevo_uso,))
            row = cursor.fetchone()
            nombre_n = row['nombre_uso'] if row else ''
            cambios.append(f"Uso -> {nombre_n}")
            updates.append("id_uso=%s")
            valores_update.append(nuevo_uso)

        if nuevo_estado and nuevo_estado != activo['estado']:
            cambios.append(f"Estado -> {nuevo_estado}")
            updates.append("estado=%s")
            valores_update.append(nuevo_estado)

        # Validación silenciosa si no hubieron cambios
        if not cambios:
            conn.close()
            return redirect(request.url)

        cambio_ubicacion = any(
            c.startswith("Área") or c.startswith("Responsable") or c.startswith("Uso")
            for c in cambios
        )
        cambio_estado = any(c.startswith("Estado") for c in cambios)

        if cambio_estado and not cambio_ubicacion:
            tipo_mov = 'Estado'
        elif cambio_ubicacion:
            tipo_mov = 'Ubicación'
        else:
            tipo_mov = 'Estado'

        query_update = f"UPDATE activos_fijos SET {', '.join(updates)} WHERE id_activo=%s"
        valores_update.append(id_activo)
        cursor.execute(query_update, tuple(valores_update))

        detalle_str = ', '.join(cambios)

        cursor.execute("""
            INSERT INTO movimientos (tipo, id_activo, detalle, motivo, usuario)
            VALUES (%s, %s, %s, %s, %s)
        """, (tipo_mov, id_activo, detalle_str, motivo, session.get('usuario')))

        conn.commit()
        conn.close()

        # AQUÍ ESTÁ LA MAGIA PARA QUE SALGA EL POP-UP
        return render_template("traslados.html", 
                               exito=True, 
                               areas=areas, 
                               responsables=responsables, 
                               usos=usos, 
                               estados=estados)

    conn.close()
    return render_template("traslados.html",
                           areas=areas,
                           responsables=responsables,
                           usos=usos,
                           estados=estados)