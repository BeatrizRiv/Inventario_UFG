from db import conectar
c = conectar()
cur = c.cursor()
cur.execute("ALTER TABLE movimientos MODIFY COLUMN tipo ENUM('Entrada','Traslado','Retiro','Actualización')")
c.commit()
print("Success")
