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
    busqueda_realizada = False
    dato_buscado = ""

    if request.method == 'POST':
        busqueda_realizada = True
        dato_buscado = request.form['busqueda'].strip()

        # Separar por espacios para buscar coincidencias parciales de múltiples palabras
        palabras = dato_buscado.split()
        
        condiciones = []
        valores = []
        
        for palabra in palabras:
            termino = f"%{palabra}%"
            condiciones.append("(a.codigo LIKE %s OR a.serie LIKE %s OR a.nombre LIKE %s)")
            valores.extend([termino, termino, termino])
            
        where_clause = " AND ".join(condiciones) if condiciones else "1=0"

        query = f"""
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
            WHERE {where_clause}
        """

        cursor.execute(query, tuple(valores))

        resultados = cursor.fetchall()

    conn.close()
    return render_template("busqueda.html", resultados=resultados, busqueda_realizada=busqueda_realizada, dato_buscado=dato_buscado)