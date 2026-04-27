import { useState, useEffect } from 'react'
import './Home.css'

function Home() {
  const [data, setData] = useState({ 
    user: null, 
    projects: [], 
    tasks: [],
    friends: [],
    stats: {} 
  })
  const [isLoading, setIsLoading] = useState(true)
  const [showProjectModal, setShowProjectModal] = useState(false)
  const [newProject, setNewProject] = useState({ name: '', description: '' })
  const [activeTab, setActiveTab] = useState('dashboard')

  useEffect(() => {
    const fetchDashboardData = async () => {
      const sessionId = localStorage.getItem('session_id')
      if (!sessionId) {
        window.location.href = '/login'
        return
      }

      try {
        const [dashboardRes, friendsRes] = await Promise.all([
          fetch('http://localhost:3000/api/dashboard', {
            headers: { 'X-Session-ID': sessionId }
          }),
          fetch('http://localhost:3000/api/friends', {
            headers: { 'X-Session-ID': sessionId }
          })
        ])
        
        if (dashboardRes.status === 401 || friendsRes.status === 401) {
          localStorage.removeItem('session_id')
          localStorage.removeItem('user')
          window.location.href = '/login'
          return
        }

        const dashboard = await dashboardRes.json()
        const friends = await friendsRes.json()
        
        if (dashboard.success) {
          setData({
            user: dashboard.user,
            projects: dashboard.projects || [],
            tasks: dashboard.tasks || [],
            friends: friends.friends || [],
            stats: dashboard.stats || { activeProjects: 0, pendingTasks: 0, collaborators: 0 }
          })
        }
      } catch (error) {
        console.error("Erreur fetch:", error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchDashboardData()
  }, [])

  const handleLogout = async () => {
    const sessionId = localStorage.getItem('session_id')
    if (sessionId) {
      await fetch('http://localhost:3000/api/logout', {
        method: 'POST',
        headers: { 'X-Session-ID': sessionId }
      })
    }
    localStorage.removeItem('session_id')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  const handleCreateProject = async () => {
    if (!newProject.name.trim()) return
    const sessionId = localStorage.getItem('session_id')
    try {
      const response = await fetch('http://localhost:3000/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': sessionId
        },
        body: JSON.stringify(newProject)
      })
      const result = await response.json()
      if (result.success) {
        setShowProjectModal(false)
        setNewProject({ name: '', description: '' })
        window.location.reload()
      }
    } catch (error) {
      console.error("Erreur creation projet:", error)
    }
  }

  const getPriorityClass = (priority) => {
    switch(priority) {
      case 'urgent': return 'priority-urgent'
      case 'high': return 'priority-high'
      case 'medium': return 'priority-medium'
      default: return 'priority-low'
    }
  }

  const getPriorityLabel = (priority) => {
    switch(priority) {
      case 'urgent': return 'Urgent'
      case 'high': return 'Haute'
      case 'medium': return 'Moyenne'
      default: return 'Basse'
    }
  }

  const getStatusLabel = (status) => {
    switch(status) {
      case 'todo': return 'À faire'
      case 'in_progress': return 'En cours'
      case 'done': return 'Terminé'
      default: return status
    }
  }

  const getStatusClass = (status) => {
    switch(status) {
      case 'todo': return 'status-todo'
      case 'in_progress': return 'status-progress'
      case 'done': return 'status-done'
      default: return 'status-todo'
    }
  }

  if (isLoading) {
    return (
      <div className="loader-container">
        <div className="loader"></div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
          <span>ColloDev</span>
        </div>
        
        <nav className="sidebar-nav">
          <button onClick={() => setActiveTab('dashboard')} className={activeTab === 'dashboard' ? 'active' : ''}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="9" y1="21" x2="9" y2="9"/>
            </svg>
            Tableau de bord
          </button>
          <button onClick={() => setActiveTab('projects')} className={activeTab === 'projects' ? 'active' : ''}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
            Projets
          </button>
          <button onClick={() => setActiveTab('teams')} className={activeTab === 'teams' ? 'active' : ''}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            Équipes
          </button>
          <button>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H5.78a1.65 1.65 0 0 0-1.51 1 1.65 1.65 0 0 0 .33 1.82l.07.08A10 10 0 0 0 12 17.66a10 10 0 0 0 6.82-2.58z"/>
            </svg>
            Paramètres
          </button>
        </nav>
        
        <div className="sidebar-footer">
          <button className="logout-btn" onClick={handleLogout}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Déconnexion
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="top-header">
          <div className="welcome">
            <h2>Bonjour, {data.user?.username} 👋</h2>
            <p>Voici ce qui se passe sur vos projets aujourd'hui.</p>
          </div>
          <div className="user-info">
            <button className="notifications">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                <path d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
              <span className="badge"></span>
            </button>
            <div className="profile">
              <div className="avatar">{data.user?.username?.charAt(0).toUpperCase()}</div>
              <div className="profile-text">
                <span className="name">{data.user?.username}</span>
                <span className="email">{data.user?.email}</span>
              </div>
            </div>
          </div>
        </header>

        <div className="content">
          {activeTab === 'dashboard' && (
            <>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-icon blue">📁</div>
                  <div className="stat-info">
                    <span>Projets Actifs</span>
                    <h3>{data.stats.activeProjects || 0}</h3>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon yellow">✅</div>
                  <div className="stat-info">
                    <span>Tâches en cours</span>
                    <h3>{data.stats.pendingTasks || 0}</h3>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon green">👥</div>
                  <div className="stat-info">
                    <span>Collaborateurs</span>
                    <h3>{data.stats.collaborators || 0}</h3>
                  </div>
                </div>
              </div>

              <div className="two-columns">
                <div className="card">
                  <div className="card-header">
                    <h3>Projets récents</h3>
                    <button onClick={() => setActiveTab('projects')} className="link-btn">Voir tout →</button>
                  </div>
                  <div className="card-body">
                    {data.projects.length === 0 ? (
                      <div className="empty-state">Aucun projet</div>
                    ) : (
                      data.projects.slice(0, 3).map(project => (
                        <div key={project.id} className="project-item">
                          <div>
                            <h4>{project.name}</h4>
                            <p>{project.description || 'Aucune description'}</p>
                            <div className="project-meta">
                              <span>📊 {project.total_tasks || 0} tâches</span>
                              <span>✅ {project.completed_tasks || 0} terminées</span>
                            </div>
                          </div>
                          <span className="badge-success">Actif</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                <div className="card">
                  <div className="card-header">
                    <h3>Mes tâches</h3>
                    <button className="link-btn">Voir tout →</button>
                  </div>
                  <div className="card-body">
                    {data.tasks?.length === 0 ? (
                      <div className="empty-state">Aucune tâche</div>
                    ) : (
                      data.tasks?.slice(0, 3).map(task => (
                        <div key={task.id} className="task-item">
                          <div className={`priority-dot ${getPriorityClass(task.priority)}`}></div>
                          <div className="task-content">
                            <h4>{task.title}</h4>
                            <p>{task.description?.substring(0, 80)}</p>
                            <div className="task-meta">
                              <span className={`priority-badge ${getPriorityClass(task.priority)}`}>
                                {getPriorityLabel(task.priority)}
                              </span>
                              <span className={`status-badge ${getStatusClass(task.status)}`}>
                                {getStatusLabel(task.status)}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3>Collaborateurs</h3>
                </div>
                <div className="card-body">
                  {data.friends?.length === 0 ? (
                    <div className="empty-state">Aucun collaborateur</div>
                  ) : (
                    <div className="friends-grid">
                      {data.friends.map(friend => (
                        <div key={friend.id} className="friend-card">
                          <div className="friend-avatar">{friend.username?.charAt(0).toUpperCase()}</div>
                          <div className="friend-info">
                            <span className="friend-name">{friend.username}</span>
                            <span className="friend-email">{friend.email}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {activeTab === 'projects' && (
            <div className="card">
              <div className="card-header">
                <h3>Tous les projets</h3>
                <button onClick={() => setShowProjectModal(true)} className="btn-primary">+ Nouveau Projet</button>
              </div>
              <div className="card-body">
                {data.projects.length === 0 ? (
                  <div className="empty-state">Aucun projet</div>
                ) : (
                  data.projects.map(project => (
                    <div key={project.id} className="project-full-item">
                      <div className="project-full-header">
                        <h4>{project.name}</h4>
                        <span className="badge-success">Actif</span>
                      </div>
                      <p>{project.description || 'Aucune description'}</p>
                      <div className="project-full-meta">
                        <span>👥 {project.total_members || 0} membres</span>
                        <span>📊 {project.total_tasks || 0} tâches</span>
                        <span>✅ {project.completed_tasks || 0} terminées</span>
                      </div>
                      <button className="btn-outline">Consulter</button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'teams' && (
            <div className="card">
              <div className="card-header">
                <h3>Mes collaborateurs</h3>
                <p className="subtitle">Vos amis et collègues sur ColloDev</p>
              </div>
              <div className="card-body">
                {data.friends?.length === 0 ? (
                  <div className="empty-state">Aucun collaborateur</div>
                ) : (
                  <div className="friends-list">
                    {data.friends.map(friend => (
                      <div key={friend.id} className="friend-full-item">
                        <div className="friend-avatar-large">{friend.username?.charAt(0).toUpperCase()}</div>
                        <div className="friend-full-info">
                          <span className="friend-full-name">{friend.username}</span>
                          <span className="friend-full-email">{friend.email}</span>
                          <span className="friend-since">Collaborateur depuis {new Date(friend.since).toLocaleDateString()}</span>
                        </div>
                        <button className="btn-message">Message</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      {showProjectModal && (
        <div className="modal-overlay" onClick={() => setShowProjectModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>Nouveau projet</h3>
            <input
              type="text"
              placeholder="Nom du projet"
              value={newProject.name}
              onChange={e => setNewProject({ ...newProject, name: e.target.value })}
            />
            <textarea
              placeholder="Description"
              rows="3"
              value={newProject.description}
              onChange={e => setNewProject({ ...newProject, description: e.target.value })}
            />
            <div className="modal-buttons">
              <button onClick={() => setShowProjectModal(false)} className="btn-secondary">Annuler</button>
              <button onClick={handleCreateProject} className="btn-primary">Créer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Home