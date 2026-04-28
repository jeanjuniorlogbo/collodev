import { useState, useEffect } from 'react'
import Header from './Header'
import './Home.css'

function Home() {
  const [data, setData] = useState({
    user: null,
    projects: [],
    tasks: [],
    friends: [],
    stats: { projects: { total: 118, inProgress: 18, completed: 100 } }
  })
  const [isLoading, setIsLoading] = useState(true)
  const [showProjectModal, setShowProjectModal] = useState(false)
  const [showFriendModal, setShowFriendModal] = useState(false)
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [newProject, setNewProject] = useState({ name: '', description: '' })
  const [currentPage, setCurrentPage] = useState('dashboard')

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
            stats: {
              projects: { total: 118, inProgress: 18, completed: 100 },
              tasks: { total: 15, inProgress: 0, completed: 0 },
              friends: { total: 0, inProgress: 0, cancel: 0 }
            }
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
                        <strong className="status-badge">En cours</strong>
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
            <input type="email" placeholder="Email de l'ami" />
            <div className="modal-buttons">
              <button onClick={() => setShowFriendModal(false)} className="btn-secondary">Annuler</button>
              <button className="btn-primary">Inviter</button>
            </div>
          </div>
        </div>
      )}

      {showInviteModal && (
        <div className="modal-overlay" onClick={() => setShowInviteModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>Invitations en attente</h3>
            <div className="empty-state" style={{ padding: '20px' }}>
              Aucune invitation en attente
            </div>
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