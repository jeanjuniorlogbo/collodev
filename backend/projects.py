from auth import require_auth, json_response
from init_db import get_db_connection
import json

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
