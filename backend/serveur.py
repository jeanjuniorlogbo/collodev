from wsgiref.simple_server import make_server
import json
import pymysql
import hashlib
import re
from urllib.parse import parse_qs, urlparse

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Hellodb71.',
    'charset': 'utf8mb4'
}

DB_NAME = 'collodev'

def get_db_connection():
    return pymysql.connect(**DB_CONFIG, database=DB_NAME)

def get_db_connection_without_db():
    return pymysql.connect(**DB_CONFIG)

def init_database():
    conn = get_db_connection_without_db()
    cursor = conn.cursor()
    
    cursor.execute(f'CREATE DATABASE IF NOT EXISTS {DB_NAME}')
    conn.commit()
    conn.close()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email):
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None

def validate_username(username):
    return len(username.strip()) >= 3

def validate_password(password):
    return len(password) >= 6

def cors_headers():
    return [
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'POST, GET, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
        ('Access-Control-Max-Age', '86400')
    ]

def json_response(status, data):
    response_body = json.dumps(data).encode('utf-8')
    headers = cors_headers()
    headers.extend([
        ('Content-Type', 'application/json'),
        ('Content-Length', str(len(response_body)))
    ])
    return headers, response_body

def handle_register(environ):
    try:
        content_length = int(environ.get('CONTENT_LENGTH', 0))
        post_data = environ['wsgi.input'].read(content_length)
        body = json.loads(post_data.decode('utf-8'))
        
        username = body.get('username', '').strip()
        email = body.get('email', '').strip().lower()
        password = body.get('password', '')
        
        if not username:
            return json_response(200, {'success': False, 'message': 'Nom d\'utilisateur requis'})
        
        if not validate_username(username):
            return json_response(200, {'success': False, 'message': 'Nom d\'utilisateur trop court (minimum 3 caracteres)'})
        
        if not email:
            return json_response(200, {'success': False, 'message': 'Email requis'})
        
        if not validate_email(email):
            return json_response(200, {'success': False, 'message': 'Email invalide'})
        
        if not password:
            return json_response(200, {'success': False, 'message': 'Mot de passe requis'})
        
        if not validate_password(password):
            return json_response(200, {'success': False, 'message': 'Mot de passe trop court (minimum 6 caracteres)'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
        if cursor.fetchone():
            conn.close()
            return json_response(200, {'success': False, 'message': 'Cet email est deja utilise'})
        
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            conn.close()
            return json_response(200, {'success': False, 'message': 'Ce nom d\'utilisateur est deja pris'})
        
        password_hash = hash_password(password)
        
        cursor.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)',
            (username, email, password_hash)
        )
        conn.commit()
        conn.close()
        
        return json_response(200, {'success': True})
        
    except json.JSONDecodeError:
        return json_response(200, {'success': False, 'message': 'Donnees invalides'})
    except Exception as e:
        return json_response(200, {'success': False, 'message': 'Erreur serveur'})

def handle_login(environ):
    try:
        content_length = int(environ.get('CONTENT_LENGTH', 0))
        post_data = environ['wsgi.input'].read(content_length)
        body = json.loads(post_data.decode('utf-8'))
        
        email = body.get('email', '').strip().lower()
        password = body.get('password', '')
        
        if not email:
            return json_response(200, {'success': False, 'message': 'Email requis'})
        
        if not password:
            return json_response(200, {'success': False, 'message': 'Mot de passe requis'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, username, password_hash FROM users WHERE email = %s',
            (email,)
        )
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return json_response(200, {'success': False, 'message': 'Email ou mot de passe incorrect'})
        
        password_hash = hash_password(password)
        
        if user[2] != password_hash:
            return json_response(200, {'success': False, 'message': 'Email ou mot de passe incorrect'})
        
        return json_response(200, {
            'success': True,
            'user': {
                'id': user[0],
                'username': user[1],
                'email': email
            }
        })
        
    except json.JSONDecodeError:
        return json_response(200, {'success': False, 'message': 'Donnees invalides'})
    except Exception as e:
        return json_response(200, {'success': False, 'message': 'Erreur serveur'})

def handle_options(environ):
    headers = cors_headers()
    headers.extend([
        ('Content-Type', 'application/json'),
        ('Content-Length', '0')
    ])
    return headers, b''

def application(environ, start_response):
    path = urlparse(environ.get('PATH_INFO', '')).path
    method = environ.get('REQUEST_METHOD', '')
    
    if method == 'OPTIONS':
        status = '200 OK'
        headers, body = handle_options(environ)
        start_response(status, headers)
        return [body]
    
    if path == '/api/register' and method == 'POST':
        status = '200 OK'
        headers, body = handle_register(environ)
        start_response(status, headers)
        return [body]
    
    elif path == '/api/login' and method == 'POST':
        status = '200 OK'
        headers, body = handle_login(environ)
        start_response(status, headers)
        return [body]
    
    else:
        status = '404 Not Found'
        response_body = json.dumps({'error': 'Not found'}).encode('utf-8')
        headers = cors_headers()
        headers.extend([
            ('Content-Type', 'application/json'),
            ('Content-Length', str(len(response_body)))
        ])
        start_response(status, headers)
        return [response_body]

if __name__ == '__main__':
    init_database()
    print('=' * 50)
    print('Serveur ColloDev demarre')
    print('=' * 50)
    print('URL: http://localhost:3000')
    print('')
    print('Endpoints disponibles:')
    print('  POST /api/register - Inscription')
    print('  POST /api/login    - Connexion')
    print('')
    print('Appuyez sur Ctrl+C pour arreter')
    print('=' * 50)
    make_server('localhost', 3000, application).serve_forever()