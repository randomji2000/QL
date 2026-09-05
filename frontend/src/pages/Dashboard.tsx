import { useEffect, useState } from 'react'
import type { DashboardStats, UserProgress } from '../types'
import { api, getUserId } from '../api'
import { PageHead, Spinner, Err } from '../components/ui'

const MOD_NAMES: Record<string, string> = {
  module1: 'Fundamentals',
  module2: 'Entanglement',
  module3: 'Gates',
  module4: 'Algorithms',
  module5: 'Advanced',
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [my, setMy] = useState<UserProgress | null>(null)
  const [err, setErr] = useState('')
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    const uid = getUserId()
    Promise.all([api.dashboard(), api.getProgress(uid)])
      .then(([s, p]) => {
        setStats(s)
        setMy(p)
      })
      .catch((e) => setErr(e.message))
      .finally(() => setLoaded(true))
  }, [])

  if (!loaded) return <Spinner label="Loading analytics…" />
  if (err) return <Err e={err} />

  const cards = [
    { ic: '👥', l: 'Learners', v: stats?.total_users },
    { ic: '📚', l: 'Lessons completed', v: stats?.total_lessons_completed },
    { ic: '▶', l: 'Simulations run', v: stats?.total_simulations },
    { ic: '◈', l: 'Circuits built', v: stats?.total_circuits_built },
    { ic: '🏅', l: 'XP earned', v: stats?.total_xp },
    { ic: '✓', l: 'Quiz avg', v: stats?.avg_quiz_score },
    { ic: '⚡', l: 'Challenges passed', v: stats?.total_challenges_passed },
    { ic: '🔥', l: 'Active today', v: stats?.active_today },
  ]

  const modEntries = Object.entries(stats?.module_completions || {})

  return (
    <div className="dash-page">
      <PageHead
        icon="▤"
        title="Instructor dashboard"
        sub="Aggregate platform analytics plus your own progress. This is the instructor view referenced in the spec."
      />
      <div className="dash-grid">
        {cards.map((c) => (
          <div key={c.l} className="card stat-card">
            <span className="stat-ic">{c.ic}</span>
            <b className="stat-v">{c.v}</b>
            <span className="stat-l">{c.l}</span>
          </div>
        ))}
      </div>

      <div className="dash-cols">
        <div className="card dash-panel">
          <h3>Module completions (all learners)</h3>
          {modEntries.length ? (
            <div className="mod-bars">
              {modEntries.map(([m, v]) => (
                <div className="mod-bar" key={m}>
                  <span className="prob-state">{MOD_NAMES[m] || m}</span>
                  <div className="bar-track">
                    <div className="bar" style={{ width: `${Math.min(100, v * 8)}%` }} />
                  </div>
                  <span className="prob-val">{v}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="faint">No lesson completions recorded yet.</p>
          )}
        </div>

        <div className="card dash-panel">
          <h3>Your profile</h3>
          <div className="my-row">
            <span className="my-label">User</span>
            <span className="my-val mono">{my?.user_id}</span>
          </div>
          <div className="my-row">
            <span className="my-label">XP</span>
            <span className="my-val">{my?.xp}</span>
          </div>
          <div className="my-row">
            <span className="my-label">Lessons</span>
            <span className="my-val">{my?.completed_lessons?.length || 0}</span>
          </div>
          <div className="my-row">
            <span className="my-label">Simulations</span>
            <span className="my-val">{my?.simulations || 0}</span>
          </div>
          <div className="my-row">
            <span className="my-label">Circuits</span>
            <span className="my-val">{my?.circuits_built || 0}</span>
          </div>
          <div className="my-row">
            <span className="my-label">Quiz scores</span>
            <span className="my-val">{Object.keys(my?.quiz_scores || {}).length} recorded</span>
          </div>
        </div>
      </div>
    </div>
  )
}
