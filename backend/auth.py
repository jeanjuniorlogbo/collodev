from init_db import get_db_connection, hash_password
import json, secrets, re

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
