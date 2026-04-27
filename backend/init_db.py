import sqlite3
import hashlib
import os

DB_PATH = 'collodev.db'

def hash_password(password):
    salt = "collodev_secret_71"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def init_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            avatar TEXT,
            bio TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS friendships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            friend_id INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (friend_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, friend_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            owner_id INTEGER NOT NULL,
            is_public INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_members (
            project_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role VARCHAR(20) DEFAULT 'developer',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (project_id, user_id),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            message_type VARCHAR(20) DEFAULT 'text',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (channel_id) REFERENCES chat_channels(id) ON DELETE CASCADE,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            assigned_to INTEGER,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            priority VARCHAR(10),
            status VARCHAR(20) DEFAULT 'todo',
            due_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS snippets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            title VARCHAR(100),
            code_content TEXT NOT NULL,
            language VARCHAR(30),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            user_id INTEGER,
            action TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()[0] == 0:
        admin_hash = hash_password('admin123')
        cursor.execute(
            "INSERT INTO users (id, username, email, password_hash) VALUES (?, ?, ?, ?)",
            (1, 'admin', 'admin@collodev.com', admin_hash)
        )
        cursor.execute(
            "INSERT INTO users (id, username, email, password_hash) VALUES (?, ?, ?, ?)",
            (2, 'jean', 'jean@collodev.com', admin_hash)
        )
        
        cursor.execute(
            "INSERT INTO friendships (user_id, friend_id, status) VALUES (?, ?, ?)",
            (1, 2, 'accepted')
        )
        
        cursor.execute(
            "INSERT INTO projects (id, name, description, owner_id, is_public) VALUES (?, ?, ?, ?, ?)",
            (1, 'ARES - Platform Optimization', 'Optimisation multi-cloud', 1, 1)
        )
        cursor.execute(
            "INSERT INTO projects (id, name, description, owner_id, is_public) VALUES (?, ?, ?, ?, ?)",
            (2, 'Cloud Operation', 'Infrastructure as Code', 1, 1)
        )
        cursor.execute(
            "INSERT INTO projects (id, name, description, owner_id, is_public) VALUES (?, ?, ?, ?, ?)",
            (3, 'ColloDev Core', 'Dashboard collaboratif', 2, 0)
        )
        
        cursor.execute(
            "INSERT INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)",
            (1, 1, 'admin')
        )
        cursor.execute(
            "INSERT INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)",
            (1, 2, 'developer')
        )
        cursor.execute(
            "INSERT INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)",
            (2, 1, 'admin')
        )
        cursor.execute(
            "INSERT INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)",
            (3, 2, 'admin')
        )
        
        cursor.execute(
            "INSERT INTO chat_channels (id, project_id, name) VALUES (?, ?, ?)",
            (1, 1, 'general')
        )
        cursor.execute(
            "INSERT INTO chat_channels (id, project_id, name) VALUES (?, ?, ?)",
            (2, 2, 'general')
        )
        cursor.execute(
            "INSERT INTO chat_channels (id, project_id, name) VALUES (?, ?, ?)",
            (3, 3, 'general')
        )
        
        cursor.execute(
            "INSERT INTO messages (channel_id, sender_id, content) VALUES (?, ?, ?)",
            (1, 1, 'Bienvenue sur ColloDev')
        )
        cursor.execute(
            "INSERT INTO messages (channel_id, sender_id, content) VALUES (?, ?, ?)",
            (1, 2, 'Merci, hate de tester')
        )
        
        cursor.execute(
            "INSERT INTO tasks (id, project_id, author_id, assigned_to, title, priority, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (1, 1, 1, 2, 'Implementer les amis', 'high', 'in_progress')
        )
        cursor.execute(
            "INSERT INTO tasks (id, project_id, author_id, assigned_to, title, priority, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (2, 1, 1, 1, 'Dashboard final', 'urgent', 'todo')
        )
        cursor.execute(
            "INSERT INTO tasks (id, project_id, author_id, assigned_to, title, priority, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (3, 2, 1, 2, 'Deployer l''API', 'medium', 'done')
        )
        
        cursor.execute(
            "INSERT INTO snippets (id, project_id, user_id, title, code_content, language) VALUES (?, ?, ?, ?, ?, ?)",
            (1, 1, 1, 'useSession hook', 'const useSession = () => { return session; }', 'javascript')
        )
        
        cursor.execute(
            "INSERT INTO logs (project_id, user_id, action) VALUES (?, ?, ?)",
            (1, 1, 'a cree le projet ARES')
        )
    
    conn.commit()
    conn.close()
    
    print("Base de donnees SQLite creee avec succes: collodev.db")
    print("Compte admin: admin@collodev.com / admin123")
    print("Compte jean: jean@collodev.com / admin123")
