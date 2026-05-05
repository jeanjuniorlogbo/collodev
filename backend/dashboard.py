from auth import json_response, require_auth
from init_db import get_db_connection

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
