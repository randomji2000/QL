import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import type { BackendInfo, Circuit, ModuleSummary, TemplateDetail, UserProgress, CourseModule, LessonContentBlock, SimResult } from '../types'
import { api, getUserId } from '../api'
import CircuitDiagram from '../components/CircuitDiagram'
import ResultsPanel from '../components/ResultsPanel'
import { PageHead, Spinner, Err } from '../components/ui'

const ICON_MAP: Record<string, string> = {
  atom: '⚛',
  link: '∞',
  gate: '◈',
  algorithm: '✧',
  rocket: '⟁',
}

function useProgress() {
  const [prog, setProg] = useState<UserProgress | null>(null)
  useEffect(() => {
    api.getProgress(getUserId()).then(setProg).catch(() => {})
  }, [])
  return { prog, setProg }
}

function DemoCircuit({ block }: { block: LessonContentBlock }) {
  const nav = useNavigate()
  const [circuit, setCircuit] = useState<Circuit | null>(null)
  const [res, setRes] = useState<SimResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [backend, setBackend] = useState('local')
  const [backends, setBackends] = useState<BackendInfo[]>([])
  const [err, setErr] = useState('')

  useEffect(() => {
    api.backends().then((r) => setBackends(r.backends)).catch(() => {})
  }, [])

  useEffect(() => {
    let alive = true
    const spec = block.circuit
    if (!spec) return
    if (typeof spec === 'string') {
      api.template(spec).then((td: TemplateDetail) => {
        if (!alive) return
        setCircuit({ num_qubits: td.num_qubits, gates: td.gates })
      })
    } else {
      setCircuit(spec)
    }
    return () => {
      alive = false
    }
  }, [block])

  const run = async () => {
    if (!circuit) return
    setBusy(true)
    setErr('')
    try {
      const r = await api.simulate(circuit, backend, 1024)
      setRes(r)
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    if (circuit && !res && !err) run()
  }, [circuit])

  if (!circuit) return <Spinner label="Preparing circuit…" />

  return (
    <div className="demo card">
      <div className="demo-head">
        <span className="chip">⚛ Interactive</span>
        <b>{block.title}</b>
        <div className="demo-actions">
          <select value={backend} onChange={(e) => setBackend(e.target.value)}>
            {backends.map((b) => (
              <option key={b.id} value={b.id} disabled={!b.available}>
                {b.name}
              </option>
            ))}
          </select>
          <button className="btn small primary" onClick={run} disabled={busy}>
            {busy ? 'Running…' : '▶ Run'}
          </button>
          <button
            className="btn small ghost"
            onClick={() => nav('/circuit-lab', { state: { circuit } })}
            title="Open this circuit in the full Circuit Lab"
          >
            Open in Lab →
          </button>
        </div>
      </div>
      <CircuitDiagram numQubits={circuit.num_qubits} gates={circuit.gates} readOnly />
      {err && <Err e={err} />}
      {res && <ResultsPanel result={res} />}
    </div>
  )
}

function ConceptStarter({ concept, onAsk }: { concept: string; onAsk: (q: string) => void }) {
  const tips: Record<string, string[]> = {
    qubit: ['What exactly is a qubit?', 'Why can a qubit hold more information than a bit?'],
    superposition: ['Explain superposition with an analogy', 'What does H|0⟩ = (|0⟩+|1⟩)/√2 mean?'],
    measurement: ['What happens when I measure a superposition?', 'What is the collapse postulate?'],
    cnot: ['What does CNOT do to |10⟩?', 'Why is CNOT reversible?'],
    entanglement: ['What makes a Bell state entangled?', 'How is entanglement different from classical correlation?'],
    'multi-qubit': ['Explain GHZ vs W states', 'What is entanglement monogamy?'],
    phase: ['What is a relative phase?', 'How do phase gates change measurement outcomes?'],
    'deutsch-jozsa': ['Walk me through Deutsch–Jozsa step by step'],
    'bernstein-vazirani': ['How does Bernstein–Vazirani find s in one query?'],
    qft: ['What does the Quantum Fourier Transform do?', 'Why is QFT useful for period finding?'],
    grover: ['How does Grover’s algorithm achieve a quadratic speedup?'],
    'phase-estimation': ['Explain the role of the inverse QFT in phase estimation'],
    teleportation: ['Walk me through teleportation step by step'],
    decoherence: ['What is decoherence and why does it matter?'],
  }
  const list = tips[concept] || ['Explain this concept to me', 'Give me a quiz question about this topic']
  return (
    <div className="concept-starter">
      <span>💬 Ask the AI tutor:</span>
      {list.map((q) => (
        <button key={q} className="chip starter" onClick={() => onAsk(q)}>
          {q}
        </button>
      ))}
    </div>
  )
}

export default function Learn() {
  const { moduleId, lessonId } = useParams()
  const nav = useNavigate()
  const { prog, setProg } = useProgress()

  return (
    <div className="learn">
      {!moduleId ? (
        <ModulesGrid />
      ) : (
        <ModuleView
          key={moduleId}
          moduleId={moduleId}
          lessonId={lessonId}
          progress={prog}
          onProgress={setProg}
          nav={nav}
        />
      )}
    </div>
  )
}

function ModulesGrid() {
  const [modules, setModules] = useState<ModuleSummary[]>([])
  const [err, setErr] = useState('')
  const { prog } = useProgress()
  const nav = useNavigate()

  useEffect(() => {
    api.courses().then((r) => setModules(r.modules)).catch((e) => setErr(e.message))
  }, [])

  return (
    <>
      <PageHead
        icon="✦"
        title="Learn"
        sub="Pick a module and go from a single qubit to Shor-ready algorithms. Every lesson embeds live, runnable circuits."
      />
      {err && <Err e={err} />}
      <div className="module-grid">
        {modules.map((m, idx) => {
          const completed = (prog?.completed_lessons || []).filter((l) => l.startsWith(m.id)).length
          const pct = m.lesson_count ? Math.round((completed / m.lesson_count) * 100) : 0
          return (
            <button key={m.id} className="card module-card" onClick={() => nav(`/learn/${m.id}`)}>
              <div className="module-icon">{ICON_MAP[m.icon] || '✦'}</div>
              <div className="module-body">
                <div className="module-meta">
                  <span className={'badge ' + m.level}>{m.level}</span>
                  <span className="faint">{m.lesson_count} lessons</span>
                </div>
                <h3>{m.title}</h3>
                <p>{m.description}</p>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: pct + '%' }} />
                </div>
                <div className="progress-label">
                  {completed}/{m.lesson_count} completed {pct === 100 && '· done'}
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </>
  )
}

function ModuleView({ moduleId, lessonId, progress, onProgress, nav }: {
  moduleId: string
  lessonId?: string
  progress: UserProgress | null
  onProgress: (p: UserProgress) => void
  nav: (to: string, opts?: any) => void
}) {
  const [module, setModule] = useState<CourseModule | null>(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    setModule(null)
    api.course(moduleId).then((r) => setModule(r.module)).catch((e) => setErr(e.message))
  }, [moduleId])

  const lessons = module?.lessons || []
  const idx = Math.max(0, lessons.findIndex((l) => l.id === lessonId) >= 0 ? lessons.findIndex((l) => l.id === lessonId) : 0)
  const lesson = lessons[idx]

  const completedIds = progress?.completed_lessons || []
  const isDone = lesson && completedIds.includes(lesson.id)

  const markComplete = async (gotoNext = true) => {
    if (!lesson) return
    setBusy(true)
    try {
      const p = await api.recordActivity(getUserId(), 'lesson', { lesson_id: lesson.id })
      onProgress(p)
      if (gotoNext && idx < lessons.length - 1) nav(`/learn/${moduleId}/${lessons[idx + 1].id}`)
      else if (gotoNext && idx === lessons.length - 1) nav(`/learn/${moduleId}`)
    } finally {
      setBusy(false)
    }
  }

  if (!module) return err ? <Err e={err} /> : <Spinner label="Loading module…" />

  return (
    <div className="module-view">
      <div className="module-side card">
        <button className="back-link" onClick={() => nav('/learn')}>
          ← All modules
        </button>
        <h3>{module.title}</h3>
        <div className="lesson-list">
          {lessons.map((l, i) => {
            const done = completedIds.includes(l.id)
            return (
              <button
                key={l.id}
                className={'lesson-item' + (l.id === lesson?.id ? ' active' : '')}
                onClick={() => nav(`/learn/${moduleId}/${l.id}`)}
              >
                <span className="lesson-num">{done ? '✓' : i + 1}</span>
                <span className="lesson-name">{l.title}</span>
                <span className="lesson-time">{l.duration}</span>
              </button>
            )
          })}
        </div>
        <div className="module-xp">🏅 {progress?.xp || 0} XP earned</div>
      </div>

      <div className="lesson-main">
        {lesson ? (
          <div className="card lesson-card">
            <div className="lesson-head">
              <div className="module-meta">
                <span className={'badge ' + module.level}>{module.level}</span>
                <span className="faint">{lesson.duration}</span>
                {isDone && <span className="badge ok">✓ completed</span>}
              </div>
              <h2>{lesson.title}</h2>
              <ConceptStarter
                concept={lesson.concept}
                onAsk={(q) => nav('/tutor', { state: { question: q, circuit: null } })}
              />
            </div>
            <div className="lesson-body">
              {lesson.content.map((b, i) =>
                b.type === 'p' ? (
                  <p key={i} className="lesson-p">
                    {b.text}
                  </p>
                ) : b.type === 'code' ? (
                  <DemoCircuit key={i} block={b} />
                ) : null,
              )}
            </div>
            <div className="lesson-foot">
              <button className="btn ghost" disabled={idx === 0} onClick={() => nav(`/learn/${moduleId}/${lessons[idx - 1].id}`)}>
                ← Previous
              </button>
              <div className="foot-actions">
                {!isDone && (
                  <button className="btn ghost" onClick={() => markComplete(false)} disabled={busy}>
                    Mark complete
                  </button>
                )}
                {idx < lessons.length - 1 ? (
                  <button className="btn primary" onClick={() => (isDone ? nav(`/learn/${moduleId}/${lessons[idx + 1].id}`) : markComplete())} disabled={busy}>
                    {isDone ? 'Next lesson →' : 'Complete & continue →'}
                  </button>
                ) : (
                  <button className="btn primary" onClick={() => nav(`/quizzes`)} disabled={busy}>
                    Module done — take the quiz →
                  </button>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="card lesson-empty">
            <h3>Module finished 🎉</h3>
            <p>You’ve reached the end of {module.title}.</p>
            <div className="foot-actions">
              <button className="btn primary" onClick={() => nav(`/quizzes`)}>
                Take the quiz →
              </button>
              <button className="btn ghost" onClick={() => nav(`/learn`)}>
                Browse modules
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
