import psycopg2
from datetime import datetime

HASH = "$2b$12$Ihnjw9rTwLmN1YsUMiNNvuIrMRHTERXl7ElN/P/sEaTaT0NzceVzi"
EMAIL = "dissem.tasnim@gmail.com"

conn = psycopg2.connect(host='localhost', port=5433, dbname='esg_db', user='esg_user', password='esg_password')
cur = conn.cursor()
cur.execute("UPDATE users SET password = %s WHERE email = %s", (HASH, EMAIL))
conn.commit()
cur.execute("SELECT id, email, role, length(password) FROM users WHERE email = %s", (EMAIL,))
print(cur.fetchone())
cur.close()
conn.close()
