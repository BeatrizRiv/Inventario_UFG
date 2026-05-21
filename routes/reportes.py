from flask import Blueprint, render_template, request, send_file, session, redirect, url_for
from db import conectar
from utils.fechas import format_fecha, format_fecha_hora
import io
import os
from datetime import datetime

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

reportes_bp = Blueprint('reportes', __name__)

LOGO_UFG = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'logo.png')

@reportes_bp.route('/reportes', methods=['GET', 'POST'])
def reportes():
    if 'usuario' not in session:
        return redirect(url_for('login.login'))

    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    # 1. MÉTODO GET
    if request.method == 'GET':
        cursor.execute("SELECT id_area, nombre_area AS nombre FROM areas WHERE estado=1")
        areas = cursor.fetchall()
        
        cursor.execute("SELECT id_tipo, nombre_tipo AS nombre FROM tipos_activo")
        tipos = cursor.fetchall()
        
        conn.close()
        return render_template("reportes.html", areas=areas, tipos=tipos)

    # 2. MÉTODO POST
    if request.method == 'POST':
        adq_inicio = request.form.get('adquisicion_inicio')
        adq_fin = request.form.get('adquisicion_fin')
        reg_inicio = request.form.get('registro_inicio')
        reg_fin = request.form.get('registro_fin')
        id_tipo = request.form.get('id_tipo')
        id_area = request.form.get('id_area')

        sql = """
            SELECT m.tipo AS tipo_mov, m.fecha AS fecha_mov, m.detalle, m.motivo, 
                   a.codigo, a.nombre AS nombre_activo, a.fecha_ingreso,
                   t.nombre_tipo AS tipo_activo, ar.nombre_area AS area_asignada
            FROM movimientos m
            JOIN activos_fijos a ON m.id_activo = a.id_activo
            LEFT JOIN tipos_activo t ON a.id_tipo = t.id_tipo
            LEFT JOIN areas ar ON a.id_area = ar.id_area
            WHERE 1=1
        """
        params = []
        filtros_texto = []
        tags_archivo = []

        if adq_inicio:
            sql += " AND DATE(a.fecha_ingreso) >= %s"
            params.append(adq_inicio)
            filtros_texto.append(f"Adquisición desde {format_fecha(adq_inicio)}")
            tags_archivo.append("AdqIn")
            
        if adq_fin:
            sql += " AND DATE(a.fecha_ingreso) <= %s"
            params.append(adq_fin)
            filtros_texto.append(f"Adquisición hasta {format_fecha(adq_fin)}")
            tags_archivo.append("AdqFin")

        if reg_inicio:
            sql += " AND DATE(m.fecha) >= %s"
            params.append(reg_inicio)
            filtros_texto.append(f"Registro desde {format_fecha(reg_inicio)}")
            tags_archivo.append("RegIn")
            
        if reg_fin:
            sql += " AND DATE(m.fecha) <= %s"
            params.append(reg_fin)
            filtros_texto.append(f"Registro hasta {format_fecha(reg_fin)}")
            tags_archivo.append("RegFin")

        if id_tipo:
            sql += " AND a.id_tipo = %s"
            params.append(id_tipo)
            filtros_texto.append("Filtro por Tipo de Activo")
            tags_archivo.append("Tipo")

        if id_area:
            sql += " AND a.id_area = %s"
            params.append(id_area)
            filtros_texto.append("Filtro por Área")
            tags_archivo.append("Area")

        sql += " ORDER BY m.fecha DESC"
        
        cursor.execute(sql, tuple(params))
        data = cursor.fetchall()
        conn.close()

        # --- GENERACIÓN DEL PDF ---
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=landscape(letter),
            rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
        )
        elementos = []
        styles = getSampleStyleSheet()

        estilo_titulo = ParagraphStyle(
            'Titulo', parent=styles['Heading1'], alignment=TA_CENTER, 
            fontSize=16, textColor=colors.HexColor('#00427A'), spaceAfter=5, fontName="Helvetica-Bold"
        )
        estilo_subtitulo = ParagraphStyle(
            'Subtitulo', parent=styles['Normal'], alignment=TA_CENTER, 
            fontSize=10, textColor=colors.HexColor('#555555'), spaceAfter=20
        )
        estilo_celda = ParagraphStyle('Celda', parent=styles['Normal'], fontSize=9, leading=11)

        # 1. Aumento del tamaño del logo a 3.5 pulgadas (más del doble del original)
        if os.path.isfile(LOGO_UFG):
            logo = Image(LOGO_UFG, width=3.5 * inch, height=1.2 * inch, kind='proportional')
            logo.hAlign = 'CENTER'
            elementos.append(logo)
            elementos.append(Spacer(1, 15))

        elementos.append(Paragraph("UNIVERSIDAD FRANCISCO GAVIDIA", estilo_titulo))
        elementos.append(Paragraph("DEPARTAMENTO DE CONTABILIDAD Y ACTIVOS FIJOS", estilo_titulo))
        
        texto_filtros = " | ".join(filtros_texto) if filtros_texto else "Todos los registros históricos"
        usuario_actual = session.get('usuario', 'Administrador')
        
        subtitulo_html = f"Reporte Oficial de Auditoría SGA<br/><b>Filtros aplicados:</b> {texto_filtros}<br/>Emitido por: <b>{usuario_actual}</b>"
        elementos.append(Paragraph(subtitulo_html, estilo_subtitulo))
        elementos.append(Spacer(1, 10))

        if not data:
            elementos.append(Paragraph("No se encontraron registros que coincidan con los filtros seleccionados.", estilo_subtitulo))
        else:
            cabeceras = [
                Paragraph("<b>FECHA OP.</b>", estilo_celda), 
                Paragraph("<b>TIPO</b>", estilo_celda), 
                Paragraph("<b>CÓDIGO</b>", estilo_celda), 
                Paragraph("<b>ACTIVO</b>", estilo_celda), 
                Paragraph("<b>ÁREA ASIGNADA</b>", estilo_celda),
                Paragraph("<b>DETALLE DE OPERACIÓN</b>", estilo_celda)
            ]
            datos_tabla = [cabeceras]

            for row in data:
                datos_tabla.append([
                    Paragraph(format_fecha_hora(row['fecha_mov']), estilo_celda),
                    Paragraph(row['tipo_activos'] if 'tipo_activos' in row else row['tipo_activo'], estilo_celda),
                    Paragraph(row['codigo'], estilo_celda),
                    Paragraph(row['nombre_activo'], estilo_celda),
                    Paragraph(row['area_asignada'] if row['area_asignada'] else "N/A", estilo_celda),
                    Paragraph(row['detalle'], estilo_celda)
                ])

            # 2. Ajuste milimétrico de los anchos de columna (Suma total = 732 pts que es el máximo de la hoja)
            tabla = Table(datos_tabla, colWidths=[80, 60, 65, 120, 105, 302], repeatRows=1)
            
            estilo_tabla = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00427A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#00427A')),
            ])

            for i in range(1, len(datos_tabla)):
                if i % 2 == 0:
                    estilo_tabla.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F2F2F2'))
                else:
                    estilo_tabla.add('BACKGROUND', (0, i), (-1, i), colors.white)

            tabla.setStyle(estilo_tabla)
            elementos.append(tabla)

        doc.build(elementos)
        buffer.seek(0)
        
        timestamp_descarga = datetime.now().strftime("%Y%m%d_%H%M%S")
        etiquetas = ("_" + "_".join(tags_archivo)) if tags_archivo else "_Completo"
        nombre_archivo = f"SGA_UFG_Auditoria{etiquetas}_{timestamp_descarga}.pdf"

        return send_file(
            buffer,
            as_attachment=True,
            download_name=nombre_archivo,
            mimetype='application/pdf'
        )