import mysql.connector

def conectar():
    return mysql.connector.connect(
        host="gateway01.us-east-1.prod.aws.tidbcloud.com",
        port=4000,
        user="3TGwmX9GJtH7Xoc.root",
        password="qJYVUDm4T1Gzcx2J",  
        database="inventario_ufg"
    )