# conexao.py
import pymysql
from dbutils.pooled_db import PooledDB

# Configuração do pool
pool = PooledDB(
    creator=pymysql,
    host='localhost',
    user='root',
    password='040712',
    database='cronograma_limpeza',
    autocommit=True,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
# Configurações otimizadas:
    maxconnections=20,      # Máximo de conexões
    mincached=3,           # Mínimo em cache
    maxcached=7,           # Máximo em cache  
    maxusage=100,          # Reutiliza conexões
    blocking=True,         # Espera se pool cheio
    ping=1,                # Verifica conexão ao reutilizar
)

def get_db_connection():
    return pool.connection()