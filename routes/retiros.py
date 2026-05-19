from flask import Blueprint, render_template, request, redirect, url_for, session
from db import conectar

retiros_bp = Blueprint('retiros', __name__)

@retiros_bp.route('/retiros', methods=['GET', 'POST'])
def retiros():

    if 'usuario' not in session:
        return redirect(url_for('login.login'))

    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        codigo = request.form['codigo']
        motivo = request.form['motivo']

        cursor.execute("SELECT * FROM activos_fijos WHERE codigo=%s", (codigo,))
        activo = cursor.fetchone()

        if not activo:
            conn.close()
            return "❌ Activo no encontrado"

        id_activo = activo['id_activo']

        cursor.execute("SELECT nombre FROM responsables WHERE id_responsable=%s", (activo['id_responsable'],))
        responsable_row = cursor.fetchone()
        responsable_nombre = responsable_row['nombre'] if responsable_row else ''

        cursor.execute("""
            UPDATE activos_fijos SET estado='Retirado'
            WHERE id_activo=%s
        """, (id_activo,))

        cursor.execute("""
            INSERT INTO movimientos (tipo, id_activo, detalle, usuario)
            VALUES ('Retiro', %s, %s, %s)
        """, (id_activo, f'{motivo}. Responsable: {responsable_nombre}', session.get('usuario')))

        conn.commit()
        conn.close()

        return redirect(url_for('movimientos.movimientos'))

    conn.close()
    return render_template("retiros.html")