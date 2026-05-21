from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import conectar

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']

        conn = conectar()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM usuarios 
            WHERE usuario=%s AND password=%s
        """, (usuario, password))

        user = cursor.fetchone()
        conn.close()

        if user:
            session['usuario'] = user['usuario']
            return redirect(url_for('dashboard.dashboard'))

        flash("❌ Usuario o contraseña incorrectos")
        return redirect(url_for('login.login'))

    return render_template("login.html")


@login_bp.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente")
    return redirect(url_for('login.login'))