import { useState, useEffect } from 'react'
import Header from './Header'
import './Home.css'

function Home() {
  const [data, setData] = useState({
    user: null,
    projects: [],
    tasks: [],
    friends: [],
    stats: { projects: { total: 0, inProgress: 0, completed: 0 } }
  })
  const [isLoading, setIsLoading] = useState(true)
  const [showProjectModal, setShowProjectModal] = useState(false)
  const [showFriendModal, setShowFriendModal] = useState(false)
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [newProject, setNewProject] = useState({ name: '', description: '' })
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [invitations, setInvitations] = useState([])
  const [searchUser, setSearchUser] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [selectedUser, setSelectedUser] = useState(null)
  const [showPreview, setShowPreview] = useState(false)

  const getSessionId = () => localStorage.getItem('session_id')

  useEffect(() => {
    const fetchDashboardData = async () => {
      const sessionId = getSessionId()
      if (!sessionId) {
        window.location.href = '/login'
        return
      }

      try {
        const [dashboardRes, friendsRes, projectsRes, tasksRes, invitesRes] = await Promise.all([
          fetch('http://localhost:3000/api/dashboard', {
            headers: { 'X-Session-ID': sessionId }
          }),
          fetch('http://localhost:3000/api/friends', {
            headers: { 'X-Session-ID': sessionId }
          }),
          fetch('http://localhost:3000/api/projects', {
            headers: { 'X-Session-ID': sessionId }
          }),
          fetch('http://localhost:3000/api/tasks', {
            headers: { 'X-Session-ID': sessionId }
          }),
          fetch('http://localhost:3000/api/friends/requests', {
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
        const projects = await projectsRes.json()
        const tasks = await tasksRes.json()
        const invites = await invitesRes.json()

        if (dashboard.success) {
          const totalProjects = dashboard.stats.activeProjects || 0
          const inProgressProjects = projects.projects?.filter(p => p.status === 'in_progress').length || 0
          const completedProjects = projects.projects?.filter(p => p.status === 'done').length || 0

          const totalTasks = tasks.tasks?.length || 0
          const inProgressTasks = tasks.tasks?.filter(t => t.status === 'in_progress').length || 0
          const completedTasks = tasks.tasks?.filter(t => t.status === 'done').length || 0

          const totalFriends = friends.friends?.length || 0
          const pendingFriends = friends.friends?.filter(f => f.status === 'pending').length || 0

          setData({
            user: dashboard.user,
            projects: projects.projects || [],
            tasks: tasks.tasks || [],
            friends: friends.friends || [],
            stats: {
              projects: { 
                total: totalProjects, 
                inProgress: inProgressProjects, 
                completed: completedProjects 
              },
              tasks: { 
                total: totalTasks, 
                inProgress: inProgressTasks, 
                completed: completedTasks 
              },
              friends: { 
                total: totalFriends, 
                inProgress: pendingFriends, 
                cancel: 0 
              }
            }
          })

          setInvitations(invites.requests || [])
        }
      } catch (error) {
        console.error("Erreur fetch:", error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchDashboardData()
  }, [])

  const handleCreateProject = async () => {
    if (!newProject.name.trim()) return
    const sessionId = getSessionId()
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

  useEffect(() => {
    if (!searchUser.trim()) {
      setSearchResults([])
      setShowPreview(false)
      setSelectedUser(null)
      return
    }

    const delayDebounce = setTimeout(() => {
      searchUsers()
    }, 500)

    return () => clearTimeout(delayDebounce)
  }, [searchUser])

  const searchUsers = async () => {
    const sessionId = getSessionId()
    if (!sessionId) {
      console.error("Session ID manquant")
      return
    }

    try {
      const response = await fetch(`http://localhost:3000/api/users/search?q=${encodeURIComponent(searchUser)}`, {
        headers: { 
          'X-Session-ID': sessionId,
          'Content-Type': 'application/json'
        }
      })
      
      if (response.status === 401) {
        localStorage.removeItem('session_id')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return
      }

      const result = await response.json()
      if (result.success && result.users.length > 0) {
        setSearchResults(result.users)
        setSelectedUser(result.users[0])
        setShowPreview(true)
      } else {
        setSearchResults([])
        setSelectedUser(null)
        setShowPreview(false)
      }
    } catch (error) {
      console.error("Erreur recherche:", error)
    }
  }

  const handleSendFriendRequest = async () => {
    if (!selectedUser) return
    const sessionId = getSessionId()
    try {
      const response = await fetch('http://localhost:3000/api/friends/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': sessionId
        },
        body: JSON.stringify({ user_id: selectedUser.id })
      })
      const result = await response.json()
      if (result.success) {
        alert('Demande envoyee a ' + selectedUser.username)
        setShowFriendModal(false)
        setSearchUser('')
        setSearchResults([])
        setSelectedUser(null)
        setShowPreview(false)
        window.location.reload()
      } else {
        alert(result.message)
      }
    } catch (error) {
      console.error("Erreur envoi demande:", error)
    }
  }

  const handleSelectUser = (user) => {
    setSelectedUser(user)
    setShowPreview(true)
    setSearchResults([])
  }

  const handleAcceptInvitation = async (requestId) => {
    const sessionId = getSessionId()
    try {
      const response = await fetch('http://localhost:3000/api/friends/accept', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': sessionId
        },
        body: JSON.stringify({ request_id: requestId })
      })
      const result = await response.json()
      if (result.success) {
        alert('Ami ajoute')
        window.location.reload()
      }
    } catch (error) {
      console.error("Erreur acceptation:", error)
    }
  }

  if (isLoading) {
    return (
      <div className="loader-container">
        <div className="loader"></div>
      </div>
    )
  }

  const recentProjects = data.projects.slice(0, 6)

  return (
    <div className="home-container">
      <Header onNavigate={setCurrentPage} activePage={currentPage} />

      <main className="home-main">
        <div className="dashboard-content">
          <div className="quick-actions">
            <button className="quick-action-btn" onClick={() => setShowProjectModal(true)}>
              <svg className="quick-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 4v16M4 12h16"/>
              </svg>
              Nouveau Projet
            </button>
            <button className="quick-action-btn" onClick={() => setShowFriendModal(true)}>
              <svg className="quick-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              Nouvel Ami
            </button>
            <button className="quick-action-btn" onClick={() => setShowInviteModal(true)}>
              <svg className="quick-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
              </svg>
              Invitations
              {invitations.length > 0 && <span className="badge">{invitations.length}</span>}
            </button>
          </div>

          <div className="stats-blocks">
            <div className="stat-block">
              <h3>Projets</h3>
              <div className="stat-line">
                <span>Total</span>
                <strong>{data.stats.projects.total}</strong>
              </div>
              <div className="stat-line">
                <span>En cours</span>
                <strong>{data.stats.projects.inProgress}</strong>
              </div>
              <div className="stat-line">
                <span>Terminer</span>
                <strong>{data.stats.projects.completed}</strong>
              </div>
            </div>

            <div className="stat-block">
              <h3>Tâches</h3>
              <div className="stat-line">
                <span>Total</span>
                <strong>{data.stats.tasks.total}</strong>
              </div>
              <div className="stat-line">
                <span>En cours</span>
                <strong>{data.stats.tasks.inProgress}</strong>
              </div>
              <div className="stat-line">
                <span>Terminer</span>
                <strong>{data.stats.tasks.completed}</strong>
              </div>
            </div>

            <div className="stat-block">
              <h3>Amis</h3>
              <div className="stat-line">
                <span>Total</span>
                <strong>{data.stats.friends.total}</strong>
              </div>
              <div className="stat-line">
                <span>En cours</span>
                <strong>{data.stats.friends.inProgress}</strong>
              </div>
              <div className="stat-line">
                <span>Annuler</span>
                <strong className="cancel">{data.stats.friends.cancel}</strong>
              </div>
            </div>
          </div>

          <div className="projects-section">
            <div className="section-header">
              <h3>Projets récents</h3>
            </div>

            {recentProjects.length === 0 ? (
              <div className="empty-state">Aucun projet pour le moment</div>
            ) : (
              <div className="projects-grid">
                {recentProjects.map((project) => (
                  <div key={project.id} className="project-card">
                    <div className="project-header">
                      <svg className="project-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                      </svg>
                      <div className="project-title">{project.name}</div>
                    </div>
                    <div className="project-details">
                      <div className="detail-cell">
                        <span>Dirigeant</span>
                        <strong>{project.owner_name || data.user?.username || 'Moi'}</strong>
                      </div>
                      <div className="detail-cell">
                        <span>État du projet</span>
                        <strong className="status-badge">
                          {project.is_public ? 'Public' : 'Privé'}
                        </strong>
                      </div>
                      <div className="detail-cell">
                        <span>Mon statut</span>
                        <strong>{project.user_role || 'Admin'}</strong>
                      </div>
                      <div className="detail-cell">
                        <button 
                          className="consult-btn"
                          onClick={() => window.location.href = `/project/${project.id}`}
                        >
                          consulter
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="home-footer">
        <p>© 2024 ColloDev - Plateforme de collaboration développeurs</p>
      </footer>

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

      {showFriendModal && (
        <div className="modal-overlay" onClick={() => setShowFriendModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>Ajouter un ami</h3>
            <div className="search-container">
              <div className="search-input-group">
                <input
                  type="text"
                  placeholder="Nom d'utilisateur ou email..."
                  value={searchUser}
                  onChange={(e) => setSearchUser(e.target.value)}
                  autoFocus
                />
              </div>
              
              {showPreview && selectedUser && (
                <div className="user-preview">
                  <div className="user-preview-avatar">
                    {selectedUser.username?.charAt(0).toUpperCase()}
                  </div>
                  <div className="user-preview-info">
                    <div className="user-preview-name">{selectedUser.username}</div>
                    <div className="user-preview-email">{selectedUser.email}</div>
                  </div>
                </div>
              )}

              {searchResults.length > 1 && !showPreview && (
                <div className="search-results">
                  {searchResults.map((user) => (
                    <div key={user.id} className="search-result-item" onClick={() => handleSelectUser(user)}>
                      <div className="user-info">
                        <div className="user-avatar-small">
                          {user.username?.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div className="user-name">{user.username}</div>
                          <div className="user-email">{user.email}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="modal-buttons">
              <button 
                onClick={() => {
                  setShowFriendModal(false)
                  setSearchUser('')
                  setSearchResults([])
                  setSelectedUser(null)
                  setShowPreview(false)
                }} 
                className="btn-secondary"
              >
                Annuler
              </button>
              <button 
                onClick={handleSendFriendRequest} 
                className="btn-primary"
                disabled={!selectedUser}
              >
                Inviter
              </button>
            </div>
          </div>
        </div>
      )}

      {showInviteModal && (
        <div className="modal-overlay" onClick={() => setShowInviteModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>Invitations en attente</h3>
            {invitations.length === 0 ? (
              <div className="empty-state" style={{ padding: '20px' }}>
                Aucune invitation en attente
              </div>
            ) : (
              <div className="invitations-list">
                {invitations.map((invite) => (
                  <div key={invite.id} className="invitation-item">
                    <div className="invitation-info">
                      <div className="user-avatar-small">
                        {invite.username?.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <strong>{invite.username}</strong>
                        <span>{invite.email}</span>
                      </div>
                    </div>
                    <button 
                      className="btn-primary"
                      onClick={() => handleAcceptInvitation(invite.id)}
                    >
                      Accepter
                    </button>
                  </div>
                ))}
              </div>
            )}
            <div className="modal-buttons">
              <button onClick={() => setShowInviteModal(false)} className="btn-secondary">Fermer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Home