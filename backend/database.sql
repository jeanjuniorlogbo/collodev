CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    avatar TEXT,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS friendships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    friend_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (friend_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, friend_id)
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL,
    is_public BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS project_members (
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role VARCHAR(20) DEFAULT 'developer',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, user_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES chat_channels(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    assigned_to INTEGER,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(10) CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    status VARCHAR(20) DEFAULT 'todo',
    due_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL
);

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
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    user_id INTEGER,
    action TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

INSERT OR IGNORE INTO users (id, username, email, password_hash) VALUES (1, 'admin', 'admin@collodev.com', '0c142c47f290714f6d7e1b7caffb3342bc9ce612572a772c8131ac3e08b5d6f8');
INSERT OR IGNORE INTO users (id, username, email, password_hash) VALUES (2, 'jean', 'jean@collodev.com', '0c142c47f290714f6d7e1b7caffb3342bc9ce612572a772c8131ac3e08b5d6f8');

INSERT OR IGNORE INTO friendships (user_id, friend_id, status) VALUES (1, 2, 'accepted');

INSERT OR IGNORE INTO projects (id, name, description, owner_id, is_public) VALUES (1, 'ARES - Platform Optimization', 'Optimisation multi-cloud', 1, 1);
INSERT OR IGNORE INTO projects (id, name, description, owner_id, is_public) VALUES (2, 'Cloud Operation', 'Infrastructure as Code', 1, 1);
INSERT OR IGNORE INTO projects (id, name, description, owner_id, is_public) VALUES (3, 'ColloDev Core', 'Dashboard collaboratif', 2, 0);

INSERT OR IGNORE INTO project_members (project_id, user_id, role) VALUES (1, 1, 'admin');
INSERT OR IGNORE INTO project_members (project_id, user_id, role) VALUES (1, 2, 'developer');
INSERT OR IGNORE INTO project_members (project_id, user_id, role) VALUES (2, 1, 'admin');
INSERT OR IGNORE INTO project_members (project_id, user_id, role) VALUES (3, 2, 'admin');

INSERT OR IGNORE INTO chat_channels (id, project_id, name) VALUES (1, 1, 'general');
INSERT OR IGNORE INTO chat_channels (id, project_id, name) VALUES (2, 2, 'general');
INSERT OR IGNORE INTO chat_channels (id, project_id, name) VALUES (3, 3, 'general');

INSERT OR IGNORE INTO messages (channel_id, sender_id, content) VALUES (1, 1, 'Bienvenue sur ColloDev');
INSERT OR IGNORE INTO messages (channel_id, sender_id, content) VALUES (1, 2, 'Merci, hâte de tester');

INSERT OR IGNORE INTO tasks (id, project_id, author_id, assigned_to, title, priority, status) VALUES (1, 1, 1, 2, 'Implémenter les amis', 'high', 'in_progress');
INSERT OR IGNORE INTO tasks (id, project_id, author_id, assigned_to, title, priority, status) VALUES (2, 1, 1, 1, 'Dashboard final', 'urgent', 'todo');
INSERT OR IGNORE INTO tasks (id, project_id, author_id, assigned_to, title, priority, status) VALUES (3, 2, 1, 2, 'Déployer l''API', 'medium', 'done');

INSERT OR IGNORE INTO snippets (id, project_id, user_id, title, code_content, language) VALUES (1, 1, 1, 'useSession hook', 'const useSession = () => { return session; }', 'javascript');

INSERT OR IGNORE INTO logs (project_id, user_id, action) VALUES (1, 1, 'a créé le projet ARES');