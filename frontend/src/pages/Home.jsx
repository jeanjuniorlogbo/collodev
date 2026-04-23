import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import reactLogo from '../assets/react.svg'
import viteLogo from '../assets/vite.svg'
import heroImg from '../assets/hero.png'
import '../App.css'

function Home() {
  const [count, setCount] = useState(0)
  const [user, setUser] = useState(null)
  const navigate = useNavigate()

  // Vérification de session au chargement
  useEffect(() => {
    const token = localStorage.getItem('token')
    const userData = localStorage.getItem('user')
    
    if (!token || !userData) {
      // Pas de session, rediriger vers login
      navigate('/login')
    } else {
      setUser(JSON.parse(userData))
    }
  }, [navigate])

  // Déconnexion
  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  if (!user) {
    return <div>Chargement...</div>
  }

  return (
    <>
      <section id="center">
        <div className="hero">
          <img src={heroImg} className="base" width="170" height="179" alt="" />
          <img src={reactLogo} className="framework" alt="React logo" />
          <img src={viteLogo} className="vite" alt="Vite logo" />
        </div>
        <div>
          <h1>Bienvenue {user.name || 'développeur'} !</h1>
          <p>
            ColloDev - Collaboration entre développeurs
          </p>
          <p>
            Édite <code>src/App.jsx</code> et sauvegarde pour tester le <code>HMR</code>
          </p>
        </div>
        <button
          type="button"
          className="counter"
          onClick={() => setCount((count) => count + 1)}
        >
          Count is {count}
        </button>
        <button
          type="button"
          className="logout-btn"
          onClick={handleLogout}
          style={{ marginLeft: '10px', background: '#dc2626' }}
        >
          Déconnexion
        </button>
      </section>

      <div className="ticks"></div>

      <section id="next-steps">
        <div id="docs">
          <svg className="icon" role="presentation" aria-hidden="true">
            <use href="/icons.svg#documentation-icon"></use>
          </svg>
          <h2>Documentation ColloDev</h2>
          <p>Guide pour les développeurs</p>
          <ul>
            <li>
              <a href="https://vite.dev/" target="_blank">
                <img className="logo" src={viteLogo} alt="" />
                Vite
              </a>
            </li>
            <li>
              <a href="https://react.dev/" target="_blank">
                <img className="button-icon" src={reactLogo} alt="" />
                React
              </a>
            </li>
          </ul>
        </div>
        <div id="social">
          <svg className="icon" role="presentation" aria-hidden="true">
            <use href="/icons.svg#social-icon"></use>
          </svg>
          <h2>Équipe ColloDev</h2>
          <p>Connecte-toi avec les autres devs</p>
          <ul>
            <li>
              <button className="button-icon">👥</button>
              Mes collaborateurs
            </li>
            <li>
              <button className="button-icon">💬</button>
              Messages
            </li>
            <li>
              <button className="button-icon">📁</button>
              Projets
            </li>
          </ul>
        </div>
      </section>

      <div className="ticks"></div>
      <section id="spacer"></section>
    </>
  )
}

export default Home