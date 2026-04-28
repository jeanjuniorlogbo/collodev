import { useState, useEffect, useRef } from 'react'
import './Header.css'

function Header({ onNavigate, activePage: externalActivePage }) {
  const [activePage, setActivePage] = useState(externalActivePage || 'dashboard')
  const [userName, setUserName] = useState('')
  const navRef = useRef(null)
  const headerRef = useRef(null)

  const pages = [
    { id: 'dashboard', label: 'Dashboard', path: '/', icon: 'M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z' },
    { id: 'projects', label: 'Mes projets', path: '/projects', icon: 'M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z' },
    { id: 'friends', label: 'Mes amis', path: '/friends', icon: 'M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z' },
    { id: 'settings', label: 'Paramètres', path: '/settings', icon: 'M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z' },
    { id: 'notifications', label: 'Notifications', path: '/notifications', icon: 'M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z' },
    { id: 'logout', label: 'Déconnexion', path: '/login', icon: 'M10.09 15.59L11.5 17l5-5-5-5-1.41 1.41L12.67 11H3v2h9.67l-2.58 2.59zM19 3H5c-1.11 0-2 .9-2 2v4h2V5h14v14H5v-4H3v4c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z' }
  ]

  useEffect(() => {
    const userData = localStorage.getItem('user')
    if (userData) {
      try {
        const user = JSON.parse(userData)
        setUserName(user.username || user.name || 'Utilisateur')
      } catch {
        setUserName('Utilisateur')
      }
    } else {
      setUserName('Utilisateur')
    }
  }, [])

  useEffect(() => {
    if (externalActivePage) {
      setActivePage(externalActivePage)
    }
  }, [externalActivePage])

  useEffect(() => {
    const applyHoverCollapseLogic = () => {
      const nav = navRef.current
      if (!nav) return

      const actionButtons = document.querySelectorAll('.action-btn')
      const containerWidth = nav.clientWidth
      let totalWidth = 0

      actionButtons.forEach(btn => {
        btn.style.transition = 'all 0.2s ease'
        btn.style.flexShrink = '0'
        const spanEl = btn.querySelector('span')
        if (spanEl) {
          spanEl.style.display = ''
          spanEl.style.maxWidth = ''
          spanEl.style.opacity = ''
        }
        btn.style.gap = '10px'
        totalWidth += btn.getBoundingClientRect().width
      })

      const hasOverflow = totalWidth > containerWidth - 10

      if (!hasOverflow) {
        actionButtons.forEach(btn => {
          const span = btn.querySelector('span')
          if (span) {
            span.style.display = 'flex'
            span.style.maxWidth = '300px'
            span.style.opacity = '1'
          }
          btn.style.gap = '10px'
        })
        return
      }

      const activeButton = Array.from(actionButtons).find(btn => btn.classList.contains('active'))
      const otherButtons = Array.from(actionButtons).filter(btn => !btn.classList.contains('active'))

      if (activeButton) {
        const activeSpan = activeButton.querySelector('span')
        if (activeSpan) {
          activeSpan.style.display = 'flex'
          activeSpan.style.maxWidth = '200px'
          activeSpan.style.opacity = '1'
        }
        activeButton.style.gap = '10px'
      }

      otherButtons.forEach(btn => {
        const span = btn.querySelector('span')
        if (span) {
          span.style.display = 'none'
          span.style.opacity = '0'
          span.style.maxWidth = '0'
          span.style.overflow = 'hidden'
          span.style.margin = '0'
          span.style.padding = '0'
        }
        btn.style.gap = '0px'
      })

      otherButtons.forEach(btn => {
        const spanElem = btn.querySelector('span')
        if (!spanElem) return

        const handleMouseEnter = () => {
          if (btn.classList.contains('active')) return
          const activeNow = document.querySelector('.action-btn.active')
          if (activeNow && activeNow !== btn) {
            const activeSpanNow = activeNow.querySelector('span')
            if (activeSpanNow) {
              activeSpanNow.style.display = 'flex'
              activeSpanNow.style.maxWidth = '200px'
              activeSpanNow.style.opacity = '1'
            }
            activeNow.style.gap = '10px'
          }

          if (spanElem) {
            spanElem.style.display = 'flex'
            spanElem.style.maxWidth = '160px'
            spanElem.style.opacity = '1'
          }
          btn.style.gap = '10px'
          btn.style.backgroundColor = '#f1f5f9'
        }

        const handleMouseLeave = () => {
          if (btn.classList.contains('active')) return
          if (spanElem && !btn.classList.contains('active')) {
            spanElem.style.display = 'none'
            spanElem.style.maxWidth = '0'
            spanElem.style.opacity = '0'
          }
          btn.style.gap = '0px'
          btn.style.backgroundColor = ''

          const activeElement = document.querySelector('.action-btn.active')
          if (activeElement && activeElement !== btn) {
            const activeSpanEl = activeElement.querySelector('span')
            if (activeSpanEl) {
              activeSpanEl.style.display = 'flex'
              activeSpanEl.style.maxWidth = '200px'
              activeSpanEl.style.opacity = '1'
            }
            activeElement.style.gap = '10px'
          }
        }

        btn.addEventListener('mouseenter', handleMouseEnter)
        btn.addEventListener('mouseleave', handleMouseLeave)
      })
    }

    applyHoverCollapseLogic()

    const resizeObserver = new ResizeObserver(() => {
      applyHoverCollapseLogic()
    })
    if (navRef.current) resizeObserver.observe(navRef.current)
    if (headerRef.current) resizeObserver.observe(headerRef.current)

    window.addEventListener('resize', () => setTimeout(applyHoverCollapseLogic, 100))

    return () => {
      resizeObserver.disconnect()
      window.removeEventListener('resize', () => {})
    }
  }, [])

  const handleClick = (page) => {
    setActivePage(page.id)
    
    if (page.id === 'logout') {
      localStorage.clear()
      window.location.href = page.path
      return
    }
    
    if (onNavigate) {
      onNavigate(page.id)
    } else {
      window.location.href = page.path
    }
  }

  const getUserInitial = () => {
    if (userName && userName.length > 0) {
      return userName.charAt(0).toUpperCase()
    }
    return 'U'
  }

  return (
    <header className="collodev-header" ref={headerRef}>
      <a href="/" className="app-infos" onClick={(e) => e.preventDefault()}>
        <svg viewBox="0 0 24 24">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
        <h2>ColloDev</h2>
      </a>

      <nav className="actions-nav" ref={navRef}>
        {pages.map((page) => (
          <button
            key={page.id}
            className={`action-btn ${activePage === page.id ? 'active' : ''}`}
            onClick={() => handleClick(page)}
            data-page={page.id}
          >
            <svg viewBox="0 0 24 24">
              <path d={page.icon}/>
            </svg>
            <span>{page.label}</span>
          </button>
        ))}
      </nav>

      <div className="user-infos">
        <h2>{userName}</h2>
        <div className="user-avatar">
          {getUserInitial()}
        </div>
      </div>
    </header>
  )
}

export default Header