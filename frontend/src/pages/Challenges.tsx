import { useEffect, useState } from 'react'
import type { Challenge, ChallengeSummary, UserProgress } from '../types'
import { api, getUserId } from '../api'
import CodeEditor from '../components/CodeEditor'
import { PageHead, Spinner, Err, Alert, LevelBadge } from '../components/ui'

export default function Challenges() {
  const [list, setList] = useState<ChallengeSummary[]>([])
  const [open, setOpen] = useState<Challenge | null>(null)
  const [code, setCode] = useState('')
  const [res, setRes] = useState<{ passed: boolean; stdout: string; stderr: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [prog, setProg] = useState<UserProgress | null>(null)

  useEffect(() => {
    api.challenges().then((r) => setList(r.challenges)).catch((e) => setErr(e.message))
    api.getProgress(getUserId()).then(setProg).catch(() => {})
  }, [])

  const openChallenge = async (c: ChallengeSummary) => {
    setBusy(true)
    setErr('')
    setRes(null)
    try {
      const r = await api.challenge(c.id)
      setOpen(r.challenge)
      setCode(r.challenge.starter)
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  const run = async () => {
    if (!open) return
    setBusy(true)
    setErr('')
    setRes(null)
    try {
      const r = await api.runChallenge(open.id, code)
      setRes(r)
      if (r.passed) {
        api.recordActivity(getUserId(), 'challenge', { challenge_id: open.id }).then(setProg).catch(() => {})
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  const passed = (id: string) => !!prog?.challenges?.[id]?.passed

  if (open) {
    return (
      <div className="challenge-page">
        <PageHead
          icon="⚡"
          title={open.title}
          sub={`Challenge · ${open.module} — ${open.description}`}
        />
        <button className="back-link" onClick={() => setOpen(null)}>
          ← All challenges
        </button>
        {err && <Err e={err} />}
        <div className="challenge-layout">
          <div className="challenge-spec card">
            <div className="module-meta">
              <LevelBadge level={open.level} />
              <span className="faint">concept · {open.concept}</span>
              {passed(open.id) && <span className="badge ok">✓ solved</span>}
            </div>
            <h3>Goal</h3>
            <p>{open.description}</p>
            <h3>How your code is judged</h3>
            <p>
              Your script runs in the sandbox; the harness applies assertions and reports whether the
              circuit/output behaves as expected.
            </p>
            <h3>Tests</h3>
            <ul className="test-list">
              {open.tests.map((t, i) => (
                <li key={i}>
                  <code>{t}</code>
                </li>
              ))}
            </ul>
            <details className="hint-box">
              <summary>Peek at a model solution</summary>
              <pre className="code-block">{open.solution}</pre>
            </details>
          </div>
          <div className="challenge-work card">
            <div className="challenge-head">
              <b>Your Python solution</b>
              <button className="btn primary" onClick={run} disabled={busy || !code.trim()}>
                {busy ? 'Checking…' : '▶ Run & check'}
              </button>
            </div>
            <CodeEditor value={code} onChange={(v) => setCode(v)} height="340px" />
            <div className="sandbox-note">
              Sandboxed subprocess · import whitelist · 25 s timeout. Use the qiskit/cirq helpers already imported.
            </div>
            {busy ? (
              <Spinner label="Running hidden tests…" />
            ) : res ? (
              <div className="challenge-result">
                {res.passed ? (
                  <Alert kind="ok">🎉 All tests passed! +50 XP</Alert>
                ) : (
                  <Alert kind="error">Some tests failed — check the output below.</Alert>
                )}
                {res.stdout && <pre className="code-block">{res.stdout}</pre>}
                {res.stderr && <pre className="code-block err">{res.stderr}</pre>}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="challenge-page">
      <PageHead icon="⚡" title="Challenges" sub="Write real quantum code and pass hidden tests to earn XP. Start with Bell, then take on Grover." />
      {err && <Err e={err} />}
      <div className="challenge-grid">
        {list.map((c) => (
          <button key={c.id} className="card challenge-card" onClick={() => openChallenge(c)}>
            <div className="challenge-top">
              <LevelBadge level={c.level} />
              {passed(c.id) ? (
                <span className="badge ok">✓ solved</span>
              ) : (
                <span className="badge neu">open</span>
              )}
            </div>
            <h3>{c.title}</h3>
            <p>{c.description}</p>
            <div className="challenge-foot-row">
              <span className="faint">module · {c.module}</span>
              <span className="faint">{c.concept}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
