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

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    result = None
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid
    except Exception as e:
        print(f"Erreur execute_query: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()
    return result

def execute_many(query, params_list):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany(query, params_list)
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        print(f"Erreur execute_many: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def select_one(table, conditions=None, columns='*'):
    query = f"SELECT {columns} FROM {table}"
    params = []
    if conditions:
        where_clause = ' AND '.join([f"{k} = ?" for k in conditions.keys()])
        query += f" WHERE {where_clause}"
        params = list(conditions.values())
    return execute_query(query, params, fetch_one=True)

def select_all(table, conditions=None, columns='*', order_by=None, limit=None):
    query = f"SELECT {columns} FROM {table}"
    params = []
    if conditions:
        where_clause = ' AND '.join([f"{k} = ?" for k in conditions.keys()])
        query += f" WHERE {where_clause}"
        params = list(conditions.values())
    if order_by:
        query += f" ORDER BY {order_by}"
    if limit:
        query += f" LIMIT {limit}"
    return execute_query(query, params, fetch_all=True)

def insert_one(table, data):
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data])
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    return execute_query(query, list(data.values()))

def update_one(table, data, conditions):
    set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
    where_clause = ' AND '.join([f"{k} = ?" for k in conditions.keys()])
    query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
    params = list(data.values()) + list(conditions.values())
    return execute_query(query, params)

def delete_one(table, conditions):
    where_clause = ' AND '.join([f"{k} = ?" for k in conditions.keys()])
    query = f"DELETE FROM {table} WHERE {where_clause}"
    return execute_query(query, list(conditions.values()))

def table_exists(table):
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
    result = execute_query(query, (table,), fetch_one=True)
    return result is not None

def get_table_columns(table):
    query = f"PRAGMA table_info({table})"
    result = execute_query(query, fetch_all=True)
    return [col[1] for col in result] if result else []

def init_database():
    if os.path.exists(DB_PATH):
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql_file_path = os.path.join(os.path.dirname(__file__), 'database.sql')
    
    if not os.path.exists(sql_file_path):
        print(f"Fichier database.sql non trouve: {sql_file_path}")
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
        print("Base de donnees SQLite creee avec succes: collodev.db")
        print("Compte admin: admin@collodev.com / admin123")
        print("Compte jean: jean@collodev.com / admin123")
    except Exception as e:
        print(f"Erreur lors de l'execution du script SQL: {e}")
    finally:
        conn.close()