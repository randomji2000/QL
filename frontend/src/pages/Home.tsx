import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, getUserId } from '../api'
import type { SimResult, TemplateSummary } from '../types'
import { PageHead, Spinner, LevelBadge } from '../components/ui'
import ResultsPanel from '../components/ResultsPanel'

const BELL_CIRCUIT = {
  num_qubits: 2,
  gates: [
    { gate: 'h', target: 1 },
    { gate: 'cx', target: 0, controls: [1] },
  ],
}

const FEATURES = [
  { ic: '◈', t: 'Drag-and-drop circuit lab', d: 'Build circuits on a visual wire grid and see them simulated instantly across local, Qiskit Aer, and Cirq backends.' },
  { ic: '</>', t: 'Real code, four frameworks', d: 'Generate and run Qiskit, Cirq, PennyLane or Braket Python in a sandboxed runner with an import whitelist.' },
  { ic: '✦', t: 'Guided learning paths', d: 'Structured modules from qubits to Grover’s search, with embedded, live circuits in every lesson.' },
  { ic: '⚡', t: 'Challenges that verify', d: 'Write solutions that are executed and automatically checked against hidden tests — not just pattern matched.' },
  { ic: '✓', t: 'Quizzes with feedback', d: 'Graded quizzes with per-question explanations to fix misconceptions.' },
  { ic: '✺', t: 'AI tutor & circuit analyst', d: 'Rule-based explanations, step-by-step circuit walkthroughs and concept help — available offline, always.' },
]

export default function Home() {
  const nav = useNavigate()
  const [templates, setTemplates] = useState<TemplateSummary[]>([])
  const [result, setResult] = useState<SimResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [runErr, setRunErr] = useState('')

  useEffect(() => {
    api.recordActivity(getUserId(), 'home_viewed').catch(() => {})
    api.templates().then((r) => setTemplates(r.templates.slice(0, 8))).catch(() => {})
    setLoading(true)
    api
      .simulate(BELL_CIRCUIT, 'local', 1024)
      .then(setResult)
      .catch((e) => setRunErr(e.message))
      .finally(() => setLoading(false))
  }, [])

  const featureRoute = (t: string) => {
    const s = t.toLowerCase()
    if (s.includes('circuit')) return '/circuit-lab'
    if (s.includes('code')) return '/code-lab'
    if (s.includes('learn') || s.includes('path')) return '/learn'
    if (s.includes('challenge')) return '/challenges'
    if (s.includes('quiz')) return '/quizzes'
    return '/tutor'
  }

  const groups = useMemo(() => {
    const map: Record<string, TemplateSummary[]> = {}
    for (const t of templates) {
      ;(map[t.category] = map[t.category] || []).push(t)
    }
    return map
  }, [templates])

  return (
    <div className="home">
      <header className="hero">
        <div className="hero-inner">
          <h1>
            Learn quantum computing by <span className="grad">building circuits</span>.
          </h1>
          <p className="hero-sub">
            Quantum Studio is an interactive platform combining a visual circuit editor, real quantum-code
            execution, guided lessons, auto-graded challenges and an AI tutor — for self-paced learners and
            instructors alike.
          </p>
          <div className="hero-cta">
            <button className="btn primary" onClick={() => nav('/learn')}>
              Start learning
            </button>
            <button className="btn ghost" onClick={() => nav('/circuit-lab')}>
              Open circuit lab
            </button>
          </div>
          <div className="hero-stats">
            <span>12+ verified algorithm templates</span>
            <span>4 simulation backends</span>
            <span>3 learning modules</span>
            <span>Auto-graded challenges</span>
          </div>
        </div>
      </header>

      <section className="card demo-card">
        <div className="card-head">
          <div>
            <h2>Live demo — Bell state</h2>
            <p>H ⊗ I then CNOT creates the entangled state (|00⟩ + |11⟩)/√2. No setup needed.</p>
          </div>
          <button className="btn small ghost" onClick={() => nav('/circuit-lab')}>
            Edit in Circuit Lab →
          </button>
        </div>
        <div className="demo-grid">
          <ResultsPanel result={loading ? null : result} />
          {runErr && <div className="alert error">{runErr}</div>}
        </div>
      </section>

      <section>
        <h2 className="section-title">Everything in one place</h2>
        <div className="feature-grid">
          {FEATURES.map((f) => (
            <button key={f.t} className="feature card" onClick={() => nav(featureRoute(f.t))}>
              <span className="feature-ic">{f.ic}</span>
              <b>{f.t}</b>
              <p>{f.d}</p>
            </button>
          ))}
        </div>
      </section>

      <section>
        <div className="section-title-row">
          <h2 className="section-title">Explore verified algorithm templates</h2>
          <button className="btn small ghost" onClick={() => nav('/circuit-lab')}>
            View all →
          </button>
        </div>
        {Object.entries(groups).map(([cat, list]) => (
          <div key={cat}>
            <h3 className="cat-title">{cat}</h3>
            <div className="template-grid">
              {list.map((t) => (
                <button
                  key={t.id}
                  className="card template-card"
                  onClick={() => {
                    api.recordActivity(getUserId(), 'template_open', { template: t.id }).catch(() => {})
                    nav('/circuit-lab?template=' + t.id)
                  }}
                >
                  <div className="template-top">
                    <LevelBadge level={t.level} />
                    <span className="faint">{t.num_qubits} q</span>
                  </div>
                  <b>{t.name}</b>
                  <p>{t.summary}</p>
                  <div className="concept-chips">
                    {t.concepts.slice(0, 3).map((c) => (
                      <span className="chip" key={c}>
                        {c}
                      </span>
                    ))}
                  </div>
                </button>
              ))}
            </div>
          </div>
        ))}
      </section>

      <section className="card path-card">
        <h2>Your suggested path</h2>
        <div className="path-steps">
          <div className="step"><span>1</span><div><b>Learn</b><p>Foundations, entanglement & algorithms</p></div></div>
          <div className="step"><span>2</span><div><b>Build</b><p>Recreate templates & experiment freely</p></div></div>
          <div className="step"><span>3</span><div><b>Code</b><p>Write real quantum programs</p></div></div>
          <div className="step"><span>4</span><div><b>Prove</b><p>Pass challenges & quizzes</p></div></div>
          <button className="btn primary" onClick={() => nav('/learn')}>
            Begin path
          </button>
        </div>
      </section>
    </div>
  )
}
