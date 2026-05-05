from friends import handle_accept_friend_request, handle_get_friend_requests, handle_get_friends, handle_send_friend_request, handle_search_users
from projects import handle_create_project, handle_get_project, handle_get_projects
from auth import json_response, handle_login, handle_register, handle_logout
from init_db import init_database
from wsgiref.simple_server import make_server
from dashboard import handle_dashboard
import json

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
    '/api/friends/accept': {'POST': handle_accept_friend_request},
    '/api/users/search': {'GET': handle_search_users}
}

def application(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    if path.startswith('/api/projects/') and method == 'GET':
        return handle_get_project(environ, start_response)
    
    if method == 'OPTIONS':
        return handle_options(environ, start_response)
    
    handler = ROUTES.get(path, {}).get(method)
    if handler:
        return handler(environ, start_response)
    
    return json_response(start_response, 404, {'error': 'Not Found'})

if __name__ == '__main__':
    print("Initialisation de la base de donnees...")
    init_database()    
    make_server('0.0.0.0', 3000, application).serve_forever()