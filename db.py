import os
import mysql.connector

def conectar():
    host = os.environ.get('DB_HOST')
    port = int(os.environ.get('DB_PORT', 3306))
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    database = os.environ.get('DB_NAME')

    try:
        return mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
    except mysql.connector.Error as e:
        err_msg = f"Error conectando a la base de datos ({host}:{port}, user={user}): {e}"
        raise RuntimeError(err_msg) from e