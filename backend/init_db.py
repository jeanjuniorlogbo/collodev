import sqlite3
import hashlib
import os
import re

DB_PATH = 'collodev.db'

def hash_password(password):
    salt = "collodev_secret_71"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def init_database():
    if os.path.exists(DB_PATH):
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql_file_path = os.path.join(os.path.dirname(__file__), 'database.sql')
    
    if not os.path.exists(sql_file_path):
        return
    
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    statements = re.split(r';\s*\n', sql_content)
    
    try:
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                cursor.execute(statement)
        conn.commit()
    except Exception as e:
        pass
    finally:
        conn.close()