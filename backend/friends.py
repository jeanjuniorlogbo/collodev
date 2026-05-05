from auth import require_auth, json_response, get_db_connection, get_session
import json

def handle_search_users(environ, start_response):
    try:
        session = get_session(environ)
        if not session:
            print("search_users: Pas de session trouvee")
            return json_response(start_response, 401, {'success': False, 'message': 'Session requise'})
        
        query = environ.get('QUERY_STRING', '')
        q = ''
        if query.startswith('q='):
            q = query[2:]
        
        if not q:
            return json_response(start_response, 200, {'success': True, 'users': []})
        
        user_id = session['user_id']
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email
                FROM users
                WHERE (username LIKE ? OR email LIKE ?)
                AND id != ?
                LIMIT 10
            """, (f'%{q}%', f'%{q}%', user_id))
            users = cursor.fetchall()
            
            users_list = []
            for u in users:
                users_list.append({
                    'id': u[0],
                    'username': u[1],
                    'email': u[2]
                })
            
            return json_response(start_response, 200, {'success': True, 'users': users_list})
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur search_users: {e}")
        return json_response(start_response, 500, {'success': False})

def handle_get_friends(environ, start_response):
    try:
        session = get_session(environ)
        if not session:
            print("get_friends: Pas de session trouvee")
            return json_response(start_response, 401, {'success': False, 'message': 'Session requise'})
        
        user_id = session['user_id']
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

def handle_get_friend_requests(environ, start_response):
    try:
        session = get_session(environ)
        if not session:
            print("get_friend_requests: Pas de session trouvee")
            return json_response(start_response, 401, {'success': False, 'message': 'Session requise'})
        
        user_id = session['user_id']
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

def handle_send_friend_request(environ, start_response):
    try:
        session = get_session(environ)
        if not session:
            print("send_friend_request: Pas de session trouvee")
            return json_response(start_response, 401, {'success': False, 'message': 'Session requise'})
        
        length = int(environ.get('CONTENT_LENGTH', 0))
        body = json.loads(environ['wsgi.input'].read(length).decode('utf-8'))
        friend_id = body.get('user_id')
        user_id = session['user_id']
        
        print(f"send_friend_request: user_id={user_id}, friend_id={friend_id}")
        
        if not friend_id or user_id == friend_id:
            return json_response(start_response, 200, {'success': False, 'message': 'ID invalide'})
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE id = ?", (friend_id,))
            if not cursor.fetchone():
                return json_response(start_response, 200, {'success': False, 'message': 'Utilisateur inexistant'})
            
            cursor.execute("SELECT * FROM friendships WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)", 
                          (user_id, friend_id, friend_id, user_id))
            if cursor.fetchone():
                return json_response(start_response, 200, {'success': False, 'message': 'Demande deja existante'})
            
            cursor.execute(
                "INSERT INTO friendships (user_id, friend_id, status) VALUES (?, ?, 'pending')",
                (user_id, friend_id)
            )
            conn.commit()
            return json_response(start_response, 200, {'success': True, 'message': 'Demande envoyee'})
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur send_friend_request: {e}")
        return json_response(start_response, 500, {'success': False})

def handle_accept_friend_request(environ, start_response):
    try:
        session = get_session(environ)
        if not session:
            print("accept_friend_request: Pas de session trouvee")
            return json_response(start_response, 401, {'success': False, 'message': 'Session requise'})
        
        length = int(environ.get('CONTENT_LENGTH', 0))
        body = json.loads(environ['wsgi.input'].read(length).decode('utf-8'))
        request_id = body.get('request_id')
        user_id = session['user_id']
        
        if not request_id:
            return json_response(start_response, 200, {'success': False, 'message': 'ID requis'})
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE friendships SET status = 'accepted' WHERE user_id = ? AND friend_id = ? AND status = 'pending'",
                (request_id, user_id)
            )
            conn.commit()
            return json_response(start_response, 200, {'success': True, 'message': 'Demande acceptee'})
        finally:
            conn.close()
    except Exception as e:
        print(f"Erreur accept_friend_request: {e}")
        return json_response(start_response, 500, {'success': False})