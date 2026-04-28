from init_db import init_database, get_db_connection, hash_password
from wsgiref.simple_server import make_server
from urllib.parse import urlparse
import json
import re
import secrets

sessions = {}

def generate_session_id():
    return secrets.token_hex(32)

def validate_email(email):
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None

def validate_username(username):
    return len(username.strip()) >= 3

def validate_password(password):
    return len(password) >= 6

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
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return json_response(start_response, 200, {'success': False, 'message': 'Email deja utilise'})
            
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return json_response(start_response, 200, {'success': False, 'message': 'Nom d\'utilisateur deja pris'})
            
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, hash_password(password))
            )
            user_id = cursor.lastrowid
            conn.commit()
            
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
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email, password_hash FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            if user and user[3] == hash_password(password):
                session_id = generate_session_id()
                sessions[session_id] = {'user_id': user[0], 'username': user[1], 'email': user[2]}
                
                return json_response(start_response, 200, {
                    'success': True,
                    'session_id': session_id,
                    'user': {
                        'id': user[0],
                        'username': user[1],
                        'email': user[2]
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
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
            user_data = cursor.fetchone()
            
            cursor.execute("""
                SELECT p.*, 
                       (SELECT COUNT(*) FROM tasks WHERE project_id = p.id) as total_tasks,
                       (SELECT COUNT(*) FROM tasks WHERE project_id = p.id AND status = 'done') as completed_tasks
                FROM projects p
                WHERE p.owner_id = ? OR p.id IN (SELECT project_id FROM project_members WHERE user_id = ?)
                ORDER BY p.created_at DESC
                LIMIT 6
            """, (user_id, user_id))
            projects = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) as total FROM projects WHERE owner_id = ?", (user_id,))
            stats_projects = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) as total FROM tasks 
                WHERE assigned_to = ? AND status IN ('todo', 'in_progress')
            """, (user_id,))
            stats_tasks = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) as total FROM project_members 
                WHERE project_id IN (SELECT id FROM projects WHERE owner_id = ?)
            """, (user_id,))
            stats_collabs = cursor.fetchone()[0]
            
            projects_list = []
            for p in projects:
                projects_list.append({
                    'id': p[0],
                    'name': p[1],
                    'description': p[2],
                    'owner_id': p[3],
                    'is_public': p[4],
                    'created_at': p[5],
                    'total_tasks': p[6],
                    'completed_tasks': p[7],
                    'user_role': 'admin' if p[3] == user_id else 'member'
                })
            
            return json_response(start_response, 200, {
                'success': True,
                'user': {
                    'id': user_data[0],
                    'username': user_data[1],
                    'email': user_data[2]
                },
                'projects': projects_list,
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
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.name, p.description, p.owner_id, p.is_public, p.created_at, u.username as owner_name
                FROM projects p
                JOIN users u ON p.owner_id = u.id
                WHERE p.owner_id = ? OR p.id IN (SELECT project_id FROM project_members WHERE user_id = ?)
                ORDER BY p.created_at DESC
            """, (user_id, user_id))
            projects = cursor.fetchall()
            
            projects_list = []
            for p in projects:
                projects_list.append({
                    'id': p[0],
                    'name': p[1],
                    'description': p[2],
                    'owner_id': p[3],
                    'owner_name': p[6],
                    'is_public': p[4],
                    'created_at': p[5],
                    'user_role': 'admin' if p[3] == user_id else 'member'
                })
            
            return json_response(start_response, 200, {'success': True, 'projects': projects_list})
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur get_projects: {e}")
        return json_response(start_response, 500, {'success': False})

@require_auth
def handle_get_project(environ, start_response):
    try:
        path_parts = environ.get('PATH_INFO', '').split('/')
        project_id = path_parts[-1] if len(path_parts) > 2 else None
        
        if not project_id:
            return json_response(start_response, 400, {'success': False, 'message': 'ID projet requis'})
        
        user = environ['user']
        user_id = user['user_id']
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, u.username as owner_name
                FROM projects p
                JOIN users u ON p.owner_id = u.id
                WHERE p.id = ? AND (p.owner_id = ? OR p.id IN (SELECT project_id FROM project_members WHERE user_id = ?))
            """, (project_id, user_id, user_id))
            project = cursor.fetchone()
            
            if not project:
                return json_response(start_response, 404, {'success': False, 'message': 'Projet non trouve'})
            
            cursor.execute("""
                SELECT u.id, u.username, u.email, pm.role
                FROM project_members pm
                JOIN users u ON pm.user_id = u.id
                WHERE pm.project_id = ?
            """, (project_id,))
            members = cursor.fetchall()
            
            members_list = []
            for m in members:
                members_list.append({
                    'id': m[0],
                    'username': m[1],
                    'email': m[2],
                    'role': m[3]
                })
            
            cursor.execute("""
                SELECT * FROM tasks WHERE project_id = ? ORDER BY created_at DESC
            """, (project_id,))
            tasks = cursor.fetchall()
            
            tasks_list = []
            for t in tasks:
                tasks_list.append({
                    'id': t[0],
                    'title': t[4],
                    'description': t[5],
                    'priority': t[6],
                    'status': t[7],
                    'due_date': t[8],
                    'created_at': t[9]
                })
            
            return json_response(start_response, 200, {
                'success': True,
                'project': {
                    'id': project[0],
                    'name': project[1],
                    'description': project[2],
                    'owner_id': project[3],
                    'owner_name': project[11],
                    'is_public': project[4],
                    'created_at': project[5]
                },
                'members': members_list,
                'tasks': tasks_list
            })
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur get_project: {e}")
        return json_response(start_response, 500, {'success': False})

@require_auth
def handle_create_project(environ, start_response):
    try:
        length = int(environ.get('CONTENT_LENGTH', 0))
        body = json.loads(environ['wsgi.input'].read(length).decode('utf-8'))
        user = environ['user']
        name = body.get('name', '').strip()
        description = body.get('description', '').strip()
        is_public = 1 if body.get('is_public', False) else 0
        
        if not name:
            return json_response(start_response, 200, {'success': False, 'message': 'Nom du projet requis'})
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO projects (name, description, owner_id, is_public) VALUES (?, ?, ?, ?)",
                (name, description, user['user_id'], is_public)
            )
            project_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)",
                (project_id, user['user_id'], 'admin')
            )
            cursor.execute(
                "INSERT INTO chat_channels (project_id, name) VALUES (?, ?)",
                (project_id, 'general')
            )
            conn.commit()
            return json_response(start_response, 200, {'success': True, 'project_id': project_id})
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur create_project: {e}")
        return json_response(start_response, 500, {'success': False})

@require_auth
def handle_get_friends(environ, start_response):
    try:
        user = environ['user']
        user_id = user['user_id']
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.email, f.status, f.created_at
                FROM friendships f
                JOIN users u ON (f.friend_id = u.id OR f.user_id = u.id)
                WHERE (f.user_id = ? OR f.friend_id = ?) AND u.id != ?
                AND f.status = 'accepted'
            """, (user_id, user_id, user_id))
            friends = cursor.fetchall()
            
            friends_list = []
            for f in friends:
                friends_list.append({
                    'id': f[0],
                    'username': f[1],
                    'email': f[2],
                    'status': f[3],
                    'since': f[4]
                })
            
            return json_response(start_response, 200, {'success': True, 'friends': friends_list})
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur get_friends: {e}")
        return json_response(start_response, 500, {'success': False})

@require_auth
def handle_get_friend_requests(environ, start_response):
    try:
        user = environ['user']
        user_id = user['user_id']
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.email, f.created_at
                FROM friendships f
                JOIN users u ON f.user_id = u.id
                WHERE f.friend_id = ? AND f.status = 'pending'
            """, (user_id,))
            requests = cursor.fetchall()
            
            requests_list = []
            for r in requests:
                requests_list.append({
                    'id': r[0],
                    'username': r[1],
                    'email': r[2],
                    'created_at': r[3]
                })
            
            return json_response(start_response, 200, {'success': True, 'requests': requests_list})
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur get_friend_requests: {e}")
        return json_response(start_response, 500, {'success': False})

@require_auth
def handle_send_friend_request(environ, start_response):
    try:
        length = int(environ.get('CONTENT_LENGTH', 0))
        body = json.loads(environ['wsgi.input'].read(length).decode('utf-8'))
        user = environ['user']
        friend_id = body.get('friend_id')
        
        if not friend_id or user['user_id'] == friend_id:
            return json_response(start_response, 200, {'success': False, 'message': 'ID invalide'})
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE id = ?", (friend_id,))
            if not cursor.fetchone():
                return json_response(start_response, 200, {'success': False, 'message': 'Utilisateur inexistant'})
            
            cursor.execute("SELECT * FROM friendships WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)", 
                          (user['user_id'], friend_id, friend_id, user['user_id']))
            if cursor.fetchone():
                return json_response(start_response, 200, {'success': False, 'message': 'Demande deja existante'})
            
            cursor.execute(
                "INSERT INTO friendships (user_id, friend_id, status) VALUES (?, ?, 'pending')",
                (user['user_id'], friend_id)
            )
            conn.commit()
            return json_response(start_response, 200, {'success': True, 'message': 'Demande envoyee'})
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur send_friend_request: {e}")
        return json_response(start_response, 500, {'success': False})

@require_auth
def handle_accept_friend_request(environ, start_response):
    try:
        length = int(environ.get('CONTENT_LENGTH', 0))
        body = json.loads(environ['wsgi.input'].read(length).decode('utf-8'))
        user = environ['user']
        request_id = body.get('request_id')
        
        if not request_id:
            return json_response(start_response, 200, {'success': False, 'message': 'ID requis'})
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE friendships SET status = 'accepted' WHERE user_id = ? AND friend_id = ? AND status = 'pending'",
                (request_id, user['user_id'])
            )
            conn.commit()
            return json_response(start_response, 200, {'success': True, 'message': 'Demande acceptee'})
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur accept_friend_request: {e}")
        return json_response(start_response, 500, {'success': False})

def handle_options(environ, start_response):
    return json_response(start_response, 200, {})

ROUTES = {
    '/api/register': {'POST': handle_register},
    '/api/login': {'POST': handle_login},
    '/api/logout': {'POST': handle_logout},
    '/api/dashboard': {'GET': handle_dashboard},
    '/api/projects': {'GET': handle_get_projects, 'POST': handle_create_project},
    '/api/friends': {'GET': handle_get_friends},
    '/api/friends/requests': {'GET': handle_get_friend_requests},
    '/api/friends/send': {'POST': handle_send_friend_request},
    '/api/friends/accept': {'POST': handle_accept_friend_request}
}

def application(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    if path.startswith('/api/projects/') and method == 'GET':
        handle_get_project(environ, start_response)
    
    if method == 'OPTIONS':
        return handle_options(environ, start_response)
    
    handler = ROUTES.get(path, {}).get(method)
    if handler:
        return handler(environ, start_response)
    
    return json_response(start_response, 404, {'error': 'Not Found'})

if __name__ == '__main__':
    print("Initialisation de la base de donnees...")
    init_database()
    print("Serveur ColloDev demarre sur http://localhost:3000")
    print("")
    print("ENDPOINTS DISPONIBLES:")
    print("  POST /api/register")
    print("  POST /api/login")
    print("  POST /api/logout")
    print("  GET  /api/dashboard")
    print("  GET  /api/projects")
    print("  POST /api/projects")
    print("  GET  /api/projects/{id}")
    print("  GET  /api/friends")
    print("  GET  /api/friends/requests")
    print("  POST /api/friends/send")
    print("  POST /api/friends/accept")
    print("")
    print("COMPTES DE TEST:")
    print("  admin@collodev.com / admin123")
    print("  jean@collodev.com / admin123")
    print("")
    print("Serveur demarre sur http://localhost:3000")
    
    make_server('0.0.0.0', 3000, application).serve_forever()