from wsgiref.simple_server import make_server
import json
import pymysql
import hashlib
import re
import secrets
from urllib.parse import urlparse

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Hellodb71.',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

DB_NAME = 'collodev'
sessions = {}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG, database=DB_NAME)

def get_db_connection_without_db():
    return pymysql.connect(**DB_CONFIG)

def hash_password(password):
    salt = "collodev_secret_71"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def generate_session_id():
    return secrets.token_hex(32)

def validate_email(email):
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None

def validate_username(username):
    return len(username.strip()) >= 3

def validate_password(password):
    return len(password) >= 6

def init_database():
    conn = get_db_connection_without_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
            cursor.execute(f"USE `{DB_NAME}`")
            
            tables = [
                """CREATE TABLE IF NOT EXISTS users (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(50) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                """CREATE TABLE IF NOT EXISTS projects (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    owner_id INT,
                    is_public BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
                )""",
                """CREATE TABLE IF NOT EXISTS project_members (
                    project_id INT,
                    user_id INT,
                    role VARCHAR(20) DEFAULT 'developer',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (project_id, user_id),
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )""",
                """CREATE TABLE IF NOT EXISTS chat_channels (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    project_id INT,
                    name VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )""",
                """CREATE TABLE IF NOT EXISTS messages (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    channel_id INT,
                    sender_id INT,
                    content TEXT NOT NULL,
                    message_type VARCHAR(20) DEFAULT 'text',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (channel_id) REFERENCES chat_channels(id) ON DELETE CASCADE,
                    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE SET NULL
                )""",
                """CREATE TABLE IF NOT EXISTS tasks (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    project_id INT,
                    author_id INT,
                    assigned_to INT,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
                    status VARCHAR(20) DEFAULT 'todo',
                    due_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL
                )""",
                """CREATE TABLE IF NOT EXISTS snippets (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    project_id INT,
                    user_id INT,
                    title VARCHAR(100),
                    code_content TEXT NOT NULL,
                    language VARCHAR(30),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )""",
                """CREATE TABLE IF NOT EXISTS logs (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    project_id INT,
                    user_id INT,
                    action TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )"""
            ]
            for table in tables:
                cursor.execute(table)
            
            cursor.execute("SELECT COUNT(*) as count FROM users")
            if cursor.fetchone()['count'] == 0:
                admin_hash = hash_password('admin123')
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    ('admin', 'admin@collodev.com', admin_hash)
                )
                
                cursor.execute(
                    "INSERT INTO projects (name, description, owner_id, is_public) VALUES (%s, %s, %s, %s)",
                    ('Projet Demo', 'Projet de demonstration pour ColloDev', 1, True)
                )
                
                cursor.execute(
                    "INSERT INTO project_members (project_id, user_id, role) VALUES (%s, %s, %s)",
                    (1, 1, 'owner')
                )
                
                cursor.execute(
                    "INSERT INTO tasks (project_id, author_id, assigned_to, title, description, priority, status) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (1, 1, 1, 'Implementer l\'authentification', 'Mettre en place les sessions', 'high', 'in_progress')
                )
                
                cursor.execute(
                    "INSERT INTO tasks (project_id, author_id, assigned_to, title, priority, status) VALUES (%s, %s, %s, %s, %s, %s)",
                    (1, 1, 1, 'Creer le dashboard', 'medium', 'todo')
                )
                
                cursor.execute(
                    "INSERT INTO chat_channels (project_id, name) VALUES (%s, %s)",
                    (1, 'general')
                )
        conn.commit()
    except Exception as e:
        print(f"Erreur init DB: {e}")
    finally:
        conn.close()

def json_response(start_response, status_code, data):
    response_body = json.dumps(data, default=str).encode('utf-8')
    status = '200 OK' if status_code == 200 else f'{status_code} Error'
    headers = [
        ('Content-Type', 'application/json'),
        ('Content-Length', str(len(response_body))),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type, X-Session-ID')
    ]
    start_response(status, headers)
    return [response_body]

def get_session(environ):
    session_id = environ.get('HTTP_X_SESSION_ID', '')
    return sessions.get(session_id)

def require_auth(handler):
    def wrapper(environ, start_response):
        session = get_session(environ)
        if not session:
            return json_response(start_response, 401, {'success': False, 'message': 'Session requise'})
        environ['user'] = session
        return handler(environ, start_response)
    return wrapper

def handle_register(environ, start_response):
    try:
        length = int(environ.get('CONTENT_LENGTH', 0))
        body = json.loads(environ['wsgi.input'].read(length).decode('utf-8'))
        username = body.get('username', '').strip()
        email = body.get('email', '').strip().lower()
        password = body.get('password', '')
        
        if not username or not email or not password:
            return json_response(start_response, 200, {'success': False, 'message': 'Tous les champs sont requis'})
        
        if not validate_username(username):
            return json_response(start_response, 200, {'success': False, 'message': 'Nom d\'utilisateur trop court (min 3 caracteres)'})
        
        if not validate_email(email):
            return json_response(start_response, 200, {'success': False, 'message': 'Email invalide'})
        
        if not validate_password(password):
            return json_response(start_response, 200, {'success': False, 'message': 'Mot de passe trop court (min 6 caracteres)'})
        
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    return json_response(start_response, 200, {'success': False, 'message': 'Email deja utilise'})
                
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    return json_response(start_response, 200, {'success': False, 'message': 'Nom d\'utilisateur deja pris'})
                
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, hash_password(password))
                )
                user_id = cursor.lastrowid
                
                session_id = generate_session_id()
                sessions[session_id] = {'user_id': user_id, 'username': username, 'email': email}
                
                return json_response(start_response, 200, {
                    'success': True,
                    'session_id': session_id,
                    'user': {'id': user_id, 'username': username, 'email': email}
                })
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur register: {e}")
        return json_response(start_response, 500, {'success': False, 'message': 'Erreur serveur'})

def handle_login(environ, start_response):
    try:
        length = int(environ.get('CONTENT_LENGTH', 0))
        body = json.loads(environ['wsgi.input'].read(length).decode('utf-8'))
        email = body.get('email', '').strip().lower()
        password = body.get('password', '')
        
        if not email or not password:
            return json_response(start_response, 200, {'success': False, 'message': 'Email et mot de passe requis'})
        
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, username, email, password_hash FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                if user and user['password_hash'] == hash_password(password):
                    session_id = generate_session_id()
                    sessions[session_id] = {'user_id': user['id'], 'username': user['username'], 'email': user['email']}
                    
                    return json_response(start_response, 200, {
                        'success': True,
                        'session_id': session_id,
                        'user': {
                            'id': user['id'],
                            'username': user['username'],
                            'email': user['email']
                        }
                    })
            return json_response(start_response, 200, {'success': False, 'message': 'Identifiants incorrects'})
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur login: {e}")
        return json_response(start_response, 500, {'success': False, 'message': 'Erreur serveur'})

def handle_logout(environ, start_response):
    session_id = environ.get('HTTP_X_SESSION_ID', '')
    if session_id in sessions:
        del sessions[session_id]
    return json_response(start_response, 200, {'success': True})

@require_auth
def handle_dashboard(environ, start_response):
    try:
        user = environ['user']
        user_id = user['user_id']
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
                user_data = cursor.fetchone()
                
                cursor.execute("""
                    SELECT p.*, 
                           (SELECT COUNT(*) FROM tasks WHERE project_id = p.id) as total_tasks,
                           (SELECT COUNT(*) FROM tasks WHERE project_id = p.id AND status = 'done') as completed_tasks
                    FROM projects p
                    WHERE p.owner_id = %s OR p.id IN (SELECT project_id FROM project_members WHERE user_id = %s)
                    ORDER BY p.created_at DESC
                    LIMIT 5
                """, (user_id, user_id))
                projects = cursor.fetchall()
                
                cursor.execute("SELECT COUNT(*) as total FROM projects WHERE owner_id = %s", (user_id,))
                stats_projects = cursor.fetchone()['total']
                
                cursor.execute("""
                    SELECT COUNT(*) as total FROM tasks 
                    WHERE assigned_to = %s AND status IN ('todo', 'in_progress')
                """, (user_id,))
                stats_tasks = cursor.fetchone()['total']
                
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) as total FROM project_members 
                    WHERE project_id IN (SELECT id FROM projects WHERE owner_id = %s)
                """, (user_id,))
                stats_collabs = cursor.fetchone()['total']
                
                return json_response(start_response, 200, {
                    'success': True,
                    'user': user_data,
                    'projects': projects,
                    'stats': {
                        'activeProjects': stats_projects,
                        'pendingTasks': stats_tasks,
                        'collaborators': stats_collabs
                    }
                })
        except Exception as e:
            print(f"Erreur dashboard DB: {e}")
            return json_response(start_response, 500, {'success': False, 'message': 'Erreur base de donnees'})
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur dashboard: {e}")
        return json_response(start_response, 500, {'success': False, 'message': 'Erreur serveur'})

@require_auth
def handle_get_projects(environ, start_response):
    try:
        user = environ['user']
        user_id = user['user_id']
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT p.*, u.username as owner_name
                    FROM projects p
                    JOIN users u ON p.owner_id = u.id
                    WHERE p.owner_id = %s OR p.id IN (SELECT project_id FROM project_members WHERE user_id = %s)
                    ORDER BY p.created_at DESC
                """, (user_id, user_id))
                projects = cursor.fetchall()
                return json_response(start_response, 200, {'success': True, 'projects': projects})
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur get_projects: {e}")
        return json_response(start_response, 500, {'success': False})

@require_auth
def handle_create_project(environ, start_response):
    try:
        length = int(environ.get('CONTENT_LENGTH', 0))
        body = json.loads(environ['wsgi.input'].read(length).decode('utf-8'))
        user = environ['user']
        name = body.get('name', '').strip()
        description = body.get('description', '').strip()
        is_public = body.get('is_public', False)
        
        if not name:
            return json_response(start_response, 200, {'success': False, 'message': 'Nom du projet requis'})
        
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO projects (name, description, owner_id, is_public) VALUES (%s, %s, %s, %s)",
                    (name, description, user['user_id'], is_public)
                )
                project_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO project_members (project_id, user_id, role) VALUES (%s, %s, %s)",
                    (project_id, user['user_id'], 'owner')
                )
                cursor.execute(
                    "INSERT INTO chat_channels (project_id, name) VALUES (%s, %s)",
                    (project_id, 'general')
                )
                conn.commit()
                return json_response(start_response, 200, {'success': True, 'project_id': project_id})
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur create_project: {e}")
        return json_response(start_response, 500, {'success': False})

def handle_options(environ, start_response):
    return json_response(start_response, 200, {})

ROUTES = {
    '/api/register': {'POST': handle_register},
    '/api/login': {'POST': handle_login},
    '/api/logout': {'POST': handle_logout},
    '/api/dashboard': {'GET': handle_dashboard},
    '/api/projects': {'GET': handle_get_projects, 'POST': handle_create_project}
}

def application(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    if method == 'OPTIONS':
        return handle_options(environ, start_response)
    
    handler = ROUTES.get(path, {}).get(method)
    if handler:
        return handler(environ, start_response)
    
    return json_response(start_response, 404, {'error': 'Not Found'})

if __name__ == '__main__':
    print("Initialisation de la base de donnees...")
    init_database()
    
    print("\n" + "=" * 60)
    print("SERVEUR COLLODEV DEMARRE (Mode Session)")
    print("=" * 60)
    print("URL: http://localhost:3000")
    print("")
    print("ENDPOINTS DISPONIBLES:")
    print("   POST /api/register - Inscription")
    print("   POST /api/login    - Connexion")
    print("   POST /api/logout   - Deconnexion")
    print("   GET  /api/dashboard - Dashboard")
    print("   GET  /api/projects - Liste projets")
    print("   POST /api/projects - Creer projet")
    print("")
    print("COMPTE DE TEST:")
    print("   Email: admin@collodev.com")
    print("   Mot de passe: admin123")
    print("")
    print("Appuyez sur Ctrl+C pour arreter")
    print("=" * 60)
    
    make_server('0.0.0.0', 3000, application).serve_forever()