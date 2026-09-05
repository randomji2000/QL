import { useEffect, useMemo, useState } from 'react'
import { api, getUserId } from '../api'
import type { CodeRunResult, TemplateDetail, TemplateSummary, TutorReply } from '../types'
import CodeEditor from '../components/CodeEditor'
import { PageHead, Spinner, Err, Alert } from '../components/ui'

const FRAMEWORKS = [
  { id: 'qiskit', name: 'Qiskit', demo: 'bell', installed: true },
  { id: 'cirq', name: 'Cirq', demo: 'bell', installed: true },
  { id: 'pennylane', name: 'PennyLane', demo: 'ghz', installed: false },
  { id: 'braket', name: 'Braket', demo: 'bell', installed: false },
]

const SAMPLE_HINTS = 'print(circuit.draw())'

export default function CodeLab() {
  const [framework, setFramework] = useState('qiskit')
  const [code, setCode] = useState('')
  const [templateList, setTemplateList] = useState<TemplateSummary[]>([])
  const [example, setExample] = useState('bell')
  const [res, setRes] = useState<CodeRunResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [tutorText, setTutorText] = useState('')
  const [tutorReplies, setTutorReplies] = useState<{ role: string; text: string }[]>([])
  const [aiMsg, setAiMsg] = useState('')

  useEffect(() => {
    api.templates().then((r) => setTemplateList(r.templates)).catch(() => {})
  }, [])

  const loadExample = async (tid: string, fw: string) => {
    try {
      const td = await api.template(tid)
      const snippet = td.code?.[fw]
      setCode(snippet || '')
      setExample(tid)
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  useEffect(() => {
    loadExample('bell', framework)
  }, [framework])

  const run = async () => {
    if (!code.trim() || !fx.installed) return
    setBusy(true)
    setErr('')
    setRes(null)
    try {
      const r = await api.runCode(code, 25)
      setRes(r)
      api.recordActivity(getUserId(), 'code_run', { framework }).catch(() => {})
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  const askTutor = async (custom?: string) => {
    const msg = (custom ?? tutorText).trim()
    if (!msg) return
    setTutorReplies((p) => [...p, { role: 'you', text: msg }])
    setTutorText('')
    setAiMsg('…')
    try {
      const r = await api.tutorChat(msg)
      setTutorReplies((p) => [...p, { role: 'tutor', text: r.text }])
    } catch (e) {
      setTutorReplies((p) => [...p, { role: 'tutor', text: 'Sorry, the tutor is unavailable: ' + (e instanceof Error ? e.message : String(e)) }])
    } finally {
      setAiMsg('')
    }
  }

  const explainError = async () => {
    const ctx = `Here is my Python code for the ${framework} framework:\n\`\`\`python\n${code}\n\`\`\`\n\nExecution output:\n${res?.stderr || res?.stdout || '(none)'}\n\nExplain what is wrong and show the corrected code.`
    setTutorReplies((p) => [...p, { role: 'you', text: 'Help me debug this error in my ' + framework + ' code.' }])
    setAiMsg('…')
    try {
      const r = await api.tutorChat(ctx)
      setTutorReplies((p) => [...p, { role: 'tutor', text: r.text }])
    } catch (e) {
      setTutorReplies((p) => [...p, { role: 'tutor', text: 'Tutor unavailable.' }])
    } finally {
      setAiMsg('')
    }
  }

  const fx = FRAMEWORKS.find((f) => f.id === framework)!

  return (
    <div className="codelab-page">
      <PageHead icon="</>" title="Code Lab" sub="Write real quantum programs in Python and run them in a sandboxed simulator with a safe import whitelist." />
      <div className="codelab-layout">
        <div className="editor-col card">
          <div className="editor-head">
            <div className="fw-tabs">
              {FRAMEWORKS.map((f) => (
                <button key={f.id} className={f.id === framework ? 'fw active' : 'fw'} onClick={() => setFramework(f.id)}>
                  {f.name}
                </button>
              ))}
            </div>
            <div className="editor-actions">
              <select
                value={example}
                onChange={(e) => loadExample(e.target.value, framework)}
                title="Load a verified example template"
              >
                <option value="bell">Template: Bell</option>
                {templateList
                  .filter((t) => t.id !== 'bell')
                  .map((t) => (
                    <option key={t.id} value={t.id}>
                      Template: {t.name}
                    </option>
                  ))}
              </select>
              <button className="btn primary" onClick={run} disabled={busy || !code.trim() || !fx.installed} title={!fx.installed ? 'PennyLane / Braket SDKs are not installed in the sandbox — use the code with your own environment.' : ''}>
                {busy ? 'Running…' : '▶ Run code'}
              </button>
            </div>
          </div>
          <div className="editor-body">
            <CodeEditor value={code} onChange={(v) => { setCode(v); setRes(null) }} height="520px" />
          </div>
          <div className="sandbox-note">
            {fx.installed
              ? <>Sandbox: pure Python + <code>{fx.name}</code> are installed and runnable here. Long-running or network code is killed automatically.</>
              : <><code>{fx.name}</code> is not installed in this sandbox, so Run is disabled — the generated code is still ready to copy into your own environment.</>}
          </div>
        </div>

        <div className="right-col">
          <div className="card output-card">
            <h3>Output</h3>
            {busy ? (
              <Spinner label="Executing…" />
            ) : res ? (
              <div className="output-body">
                {res.ok && (
                  <Alert kind="ok">Finished (exit {res.returncode ?? 0}).</Alert>
                )}
                {!res.ok && <Alert kind="warn">Program failed with exit code {res.returncode ?? -1}.</Alert>}
                {res.stderr && (
                  <pre className="code-block err">{res.stderr}</pre>
                )}
                {res.stdout ? (
                  <pre className="code-block">{res.stdout}</pre>
                ) : (
                  <p className="faint">No output.</p>
                )}
                {res.artifacts && Object.keys(res.artifacts).length > 0 && (
                  <div className="artifact-grid">
                    {Object.entries(res.artifacts).map(([k, v]) => (
                      <div className="artifact" key={k}>
                        <b>{k}</b>
                        <pre>{typeof v === 'string' ? v : JSON.stringify(v, null, 2)}</pre>
                      </div>
                    ))}
                  </div>
                )}
                {!res.ok && res.stderr && (
                  <button className="btn small" onClick={explainError}>
                    ✺ Ask the tutor to fix this
                  </button>
                )}
              </div>
            ) : (
              <div className="empty-inline">
                <p>Output will appear here.</p>
                <div className="hint-small">
                  Try <code>{SAMPLE_HINTS}</code> and a measurement, then run. Measurements print count dictionaries.
                </div>
              </div>
            )}
          </div>

          <div className="card tutor-card">
            <h3>✺ AI tutor</h3>
            <div className="chat">
              {tutorReplies.map((m, i) => (
                <div key={i} className={m.role === 'you' ? 'msg you' : 'msg tutor'}>
                  {m.text}
                </div>
              ))}
              {aiMsg && <div className="msg tutor loading">{aiMsg}</div>}
            </div>
            <div className="chat-input">
              <input
                placeholder="Ask about this code, e.g. why is my phase wrong?"
                value={tutorText}
                onChange={(e) => setTutorText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && askTutor()}
              />
              <button className="btn primary small" onClick={() => askTutor()}>
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
