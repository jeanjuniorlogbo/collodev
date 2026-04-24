import { useState, useEffect } from 'react'
import './Home.css'

function Home() {
  const [data, setData] = useState({ user: null, projects: [], stats: {} })
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchDashboardData = async () => {
      const sessionId = localStorage.getItem('session_id')
      if (!sessionId) {
        window.location.href = '/login'
        return
      }

      try {
        const response = await fetch('http://localhost:3000/api/dashboard', {
          headers: {
            'X-Session-ID': sessionId
          }
        })
        
        if (response.status === 401) {
          localStorage.removeItem('session_id')
          localStorage.removeItem('user')
          window.location.href = '/login'
          return
        }

        const result = await response.json()
        if (result.success) {
          setData({
            user: result.user,
            projects: result.projects || [],
            stats: result.stats || { activeProjects: 0, pendingTasks: 0, collaborators: 0 }
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

  if (isLoading) return <div className="loader-container"><div className="loader"></div></div>

  return (
    <div className="dashboard-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
          <span>ColloDev</span>
        </div>
        <nav className="sidebar-nav">
          <a href="#" className="active">Tableau de bord</a>
          <a href="#">Mes Projets</a>
          <a href="#">Équipes</a>
          <a href="#">Paramètres</a>
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

      <main className="dashboard-main">
        <header className="dashboard-header">
          <div className="welcome">
            <h2>Ravi de vous revoir, {data.user?.username} 👋</h2>
            <p>Voici ce qui se passe sur vos projets aujourd'hui.</p>
          </div>
          <div className="user-profile">
            <div className="avatar">{data.user?.username?.charAt(0)}</div>
          </div>
        </header>

        <section className="stats-grid">
          <div className="stat-card">
            <span>Projets Actifs</span>
            <h3>{data.stats.activeProjects || 0}</h3>
          </div>
          <div className="stat-card">
            <span>Tâches en cours</span>
            <h3>{data.stats.pendingTasks || 0}</h3>
          </div>
          <div className="stat-card">
            <span>Collaborateurs</span>
            <h3>{data.stats.collaborators || 0}</h3>
          </div>
        </section>

        <section className="content-section">
          <div className="section-header">
            <h3>Projets récents</h3>
            <button className="btn-primary">Nouveau Projet</button>
          </div>
          <div className="projects-list">
            {data.projects.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>
                Aucun projet. Cliquez sur "Nouveau Projet" pour commencer !
              </div>
            ) : (
              data.projects.map(project => (
                <div key={project.id} className="project-item">
                  <div className="project-info">
                    <h4>{project.name}</h4>
                    <p>{project.description || 'Aucune description'}</p>
                  </div>
                  <div className="project-status">En cours</div>
                </div>
              ))
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

export default Home