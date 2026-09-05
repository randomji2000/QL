import { NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import Home from './pages/Home'
import Learn from './pages/Learn'
import CircuitLab from './pages/CircuitLab'
import CodeLab from './pages/CodeLab'
import Challenges from './pages/Challenges'
import Quizzes from './pages/Quizzes'
import Tutor from './pages/Tutor'
import Dashboard from './pages/Dashboard'
import { getUserId } from './api'
import { useEffect, useState } from 'react'

const NAV = [
  { to: '/', label: 'Home', icon: '⌂' },
  { to: '/learn', label: 'Learn', icon: '✦' },
  { to: '/circuit-lab', label: 'Circuit Lab', icon: '◈' },
  { to: '/code-lab', label: 'Code Lab', icon: '</>' },
  { to: '/challenges', label: 'Challenges', icon: '⚡' },
  { to: '/quizzes', label: 'Quizzes', icon: '✓' },
  { to: '/tutor', label: 'AI Tutor', icon: '✺' },
  { to: '/dashboard', label: 'Analytics', icon: '▤' },
]

export default function App() {
  const [userId] = useState(() => getUserId())
  const loc = useLocation()
  useEffect(() => {
    const el = document.querySelector('.main')
    if (el) el.scrollTop = 0
  }, [loc.pathname])

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo">Q</div>
          <div>
            <b>Quantum Studio</b>
            <span>AI Quantum Learning</span>
          </div>
        </div>
        <nav className="nav">
          <div className="nav-label">Workspace</div>
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === '/'}
              className={({ isActive }) => 'nav-item' + (isActive ? ' active' : '')}
            >
              <span className="ic">{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="user-chip">
          <div className="faint">{userId}</div>
        </div>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/learn" element={<Learn />} />
          <Route path="/circuit-lab" element={<CircuitLab />} />
          <Route path="/code-lab" element={<CodeLab />} />
          <Route path="/challenges" element={<Challenges />} />
          <Route path="/quizzes" element={<Quizzes />} />
          <Route path="/tutor" element={<Tutor />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
