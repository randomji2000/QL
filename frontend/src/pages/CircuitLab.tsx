import { useEffect, useMemo, useState } from 'react'
import { useLocation, useSearchParams } from 'react-router-dom'
import type { BackendInfo, Circuit, CircuitAnalysis, GateOp, SimResult, TemplateDetail } from '../types'
import { api, getUserId } from '../api'
import CircuitDiagram from '../components/CircuitDiagram'
import ResultsPanel from '../components/ResultsPanel'
import { DEFAULT_PARAMS, GATE_PALETTE, uid, type GateDef } from '../lib/gates'
import { Spinner, PageHead, Err } from '../components/ui'

function copyCircuit(src: Circuit, qubits?: number): Circuit {
  return {
    num_qubits: qubits ?? src.num_qubits,
    gates: src.gates.map((g) => ({ ...g, id: g.id ?? uid() })),
  }
}

export default function CircuitLab() {
  const [params] = useSearchParams()
  const location = useLocation()
  const stateCircuit = (location.state as { circuit?: Circuit } | null)?.circuit
  const [backend, setBackend] = useState('local')
  const [shots, setShots] = useState(1024)
  const [backends, setBackends] = useState<BackendInfo[]>([])
  const [circuit, setCircuit] = useState<Circuit>({ num_qubits: 3, gates: [{ gate: 'h', target: 0, id: uid() }] })
  const [result, setResult] = useState<SimResult | null>(null)
  const [analysis, setAnalysis] = useState<CircuitAnalysis | null>(null)
  const [code, setCode] = useState<Record<string, string>>({})
  const [activeGate, setActiveGate] = useState<GateDef | null>(null)
  const [pendingControls, setPendingControls] = useState<number[]>([])
  const [pendingTarget, setPendingTarget] = useState<number | null>(null)
  const [selectedGateId, setSelectedGateId] = useState<string | null>(null)
  const [editParam, setEditParam] = useState<{ gateId: string; def: GateDef } | null>(null)
  const [paramVal, setParamVal] = useState('')
  const [busy, setBusy] = useState<'sim' | 'code' | null>(null)
  const [err, setErr] = useState('')
  const [tab, setTab] = useState<'sim' | 'analyze' | 'code'>('sim')
  const [framework, setFramework] = useState('qiskit')

  useEffect(() => {
    api.backends().then((r) => {
      setBackends(r.backends)
      const avail = r.backends.filter((b) => b.available)
      if (avail.length && !avail.find((b) => b.id === backend)) setBackend(avail[0].id)
    })
  }, [])

  useEffect(() => {
    if (stateCircuit) {
      setCircuit(copyCircuit(stateCircuit))
      setResult(null)
      setTab('sim')
      return
    }
    const t = params.get('template')
    if (t) {
      api.template(t).then((td: TemplateDetail) => {
        setCircuit({
          num_qubits: td.num_qubits,
          gates: td.gates.map((g) => ({ ...g, id: uid() })),
        })
        setCode(td.code || {})
        setResult(null)
        setTab('sim')
      })
    }
  }, [params, stateCircuit])

  const defs = useMemo(() => {
    const palette = [...GATE_PALETTE]
    return {
      single: palette.filter((g) => g.category === 'single'),
      two: palette.filter((g) => g.category === 'two'),
      three: palette.filter((g) => g.category === 'three'),
      special: palette.filter((g) => g.category === 'special'),
    }
  }, [])

  const resetEditor = () => {
    setActiveGate(null)
    setPendingTarget(null)
    setPendingControls([])
    setSelectedGateId(null)
  }

  const handleWireClick = (wire: number) => {
    if (!activeGate) return
    if (activeGate.controls === 0) {
      // single-target (or multi-target) gate: the wire click is the first target
      const paramsVals = activeGate.params ? [DEFAULT_PARAMS[activeGate.id] ?? Math.PI / 2] : []
      const g: GateOp = { gate: activeGate.id, target: wire, id: uid() }
      if (activeGate.params) g.params = paramsVals
      setCircuit((c) => ({ ...c, gates: [...c.gates, g] }))
      api.recordActivity(getUserId(), 'gate_added', { gate: activeGate.id }).catch(() => {})
      resetEditor()
      setResult(null)
      return
    }
    if (pendingTarget === null) {
      // first click on wire = choose target for controlled gate
      setPendingTarget(wire)
      return
    }
    // subsequent clicks add controls on other wires
    if (pendingControls.includes(wire) || wire === pendingTarget) return
    const next = [...pendingControls, wire]
    setPendingControls(next)
    if (next.length === activeGate.controls) {
      const g: GateOp = { gate: activeGate.id, target: pendingTarget, controls: next, id: uid() }
      setCircuit((c) => ({ ...c, gates: [...c.gates, g] }))
      api.recordActivity(getUserId(), 'gate_added', { gate: activeGate.id }).catch(() => {})
      resetEditor()
      setResult(null)
    }
  }

  const removeGate = (gateId: string) => {
    setCircuit((c) => ({ ...c, gates: c.gates.filter((g) => g.id !== gateId) }))
    setSelectedGateId(null)
    setResult(null)
  }

  const openParam = (g: GateOp) => {
    const def = GATE_PALETTE.find((d) => d.id === g.gate)
    if (!def || !def.params) return
    setEditParam({ gateId: g.id!, def })
    setParamVal(String(g.params?.[0] ?? DEFAULT_PARAMS[def.id] ?? Math.PI / 2))
  }

  const saveParam = () => {
    if (!editParam) return
    const v = parseFloat(paramVal)
    if (Number.isFinite(v)) {
      setCircuit((c) => ({
        ...c,
        gates: c.gates.map((g) => (g.id === editParam.gateId ? { ...g, params: [v] } : g)),
      }))
      setResult(null)
    }
    setEditParam(null)
  }

  const run = async () => {
    setBusy('sim')
    setErr('')
    setTab('sim')
    try {
      const r = await api.simulate(circuit, backend, shots)
      setResult(r)
      api.recordActivity(getUserId(), 'simulation', { backend }).catch(() => {})
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(null)
    }
  }

  const analyze = async () => {
    setBusy('sim')
    setErr('')
    setTab('analyze')
    try {
      const a = await api.analyzeCircuit(circuit)
      setAnalysis(a)
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(null)
    }
  }

  const genCode = async () => {
    setBusy('code')
    setErr('')
    try {
      const r = await api.generateCode(circuit, framework)
      setCode((prev) => ({ ...prev, [framework]: r.code }))
      setTab('code')
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(null)
    }
  }

  const numQubits = circuit.num_qubits

  const wiresUnused = Array.from({ length: numQubits }).filter(
    (_, w) => !circuit.gates.some((g) => {
      const ws = g.controls || []
      if (g.target !== undefined) ws.push(g.target)
      if (g.targets) ws.push(...g.targets)
      return ws.includes(w)
    }),
  )

  return (
    <div className="circuit-page">
      <PageHead icon="◈" title="Circuit Lab" sub="Place gates on wires to build a circuit, then simulate it, analyse it, or export code." />
      <div className="lab-layout">
        <div className="palette card">
          <h3>Gates</h3>
          {activeGate && (
            <div className="toolbar-note">
              <b>Placing {activeGate.label}</b>
              {activeGate.controls > 0 ? (
                pendingTarget === null ? (
                  <span className="hint">Click a wire to set <b>target</b>…</span>
                ) : (
                  <span className="hint">
                    Controls ({pendingControls.length}/{activeGate.controls}) — click more wires, then auto-place.
                  </span>
                )
              ) : (
                <span className="hint">Click a wire to place.</span>
              )}
            </div>
          )}
          <div className="palette-block">
            {defs.single.map((g) => (
              <button
                key={g.id}
                className={'palette-gate' + (activeGate?.id === g.id ? ' active' : '')}
                style={{ ['--gc' as string]: g.color }}
                title={`${g.full} — ${g.desc}`}
                onClick={() => {
                  if (activeGate?.id === g.id) resetEditor()
                  else {
                    setActiveGate(g)
                    setPendingTarget(null)
                    setPendingControls([])
                    setSelectedGateId(null)
                  }
                }}
              >
                {g.label}
              </button>
            ))}
          </div>
          <div className="palette-divider" />
          <div className="palette-block">
            {defs.two.map((g) => (
              <button
                key={g.id}
                className={'palette-gate' + (activeGate?.id === g.id ? ' active' : '')}
                style={{ ['--gc' as string]: g.color }}
                title={`${g.full} — ${g.desc}`}
                onClick={() => {
                  if (activeGate?.id === g.id) resetEditor()
                  else {
                    setActiveGate(g)
                    setPendingTarget(null)
                    setPendingControls([])
                    setSelectedGateId(null)
                  }
                }}
              >
                {g.label}
              </button>
            ))}
          </div>
          <div className="palette-divider" />
          <div className="palette-block">
            {defs.three.map((g) => (
              <button
                key={g.id}
                className={'palette-gate' + (activeGate?.id === g.id ? ' active' : '')}
                style={{ ['--gc' as string]: g.color }}
                title={`${g.full} — ${g.desc}`}
                onClick={() => {
                  if (activeGate?.id === g.id) resetEditor()
                  else {
                    setActiveGate(g)
                    setPendingTarget(null)
                    setPendingControls([])
                    setSelectedGateId(null)
                  }
                }}
              >
                {g.label}
              </button>
            ))}
          </div>
          <div className="palette-divider" />
          <div className="palette-block">
            {defs.special.map((g) => (
              <button
                key={g.id}
                className={'palette-gate' + (activeGate?.id === g.id ? ' active' : '')}
                style={{ ['--gc' as string]: g.color }}
                title={`${g.full} — ${g.desc}`}
                onClick={() => {
                  if (activeGate?.id === g.id) resetEditor()
                  else {
                    setActiveGate(g)
                    setPendingTarget(null)
                    setPendingControls([])
                    setSelectedGateId(null)
                  }
                }}
              >
                {g.label}
              </button>
            ))}
          </div>
          <div className="palette-tip">
            Tip: for {`CNOT / CZ / CCX`}, first click = target, next clicks = controls.
          </div>
        </div>

        <div className="workspace">
          <div className="lab-topbar">
            <div className="lab-controls">
              <label>Qubits</label>
              <div className="stepper">
                <button disabled={numQubits <= 1} onClick={() => setCircuit((c) => ({ ...c, num_qubits: numQubits - 1 }))}>
                  −
                </button>
                <span>{numQubits}</span>
                <button disabled={numQubits >= 18} onClick={() => setCircuit((c) => ({ ...c, num_qubits: numQubits + 1 }))}>
                  +
                </button>
              </div>
              <label>Backend</label>
              <select value={backend} onChange={(e) => setBackend(e.target.value)}>
                {backends.map((b) => (
                  <option key={b.id} value={b.id} disabled={!b.available}>
                    {b.name}
                    {!b.available ? ' (offline)' : ''}
                  </option>
                ))}
              </select>
              <label>Shots</label>
              <input
                type="number"
                min={1}
                max={200000}
                value={shots}
                onChange={(e) => setShots(Math.max(1, Math.min(200000, parseInt(e.target.value) || 1)))}
                className="num-inp"
              />
            </div>
            <div className="lab-actions">
              <button className="btn primary" onClick={run} disabled={busy !== null}>
                {busy === 'sim' ? 'Running…' : '▶ Simulate'}
              </button>
              <button className="btn ghost" onClick={analyze} disabled={busy !== null}>
                ✦ Analyse
              </button>
              <select
                value={framework}
                onChange={(e) => {
                  setFramework(e.target.value)
                  setCode((prev) => (prev[e.target.value] ? prev : prev))
                }}
                title="Code framework"
              >
                {['qiskit', 'cirq', 'pennylane', 'braket'].map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </select>
              <button className="btn ghost" onClick={genCode} disabled={busy !== null}>
                {'⟨/⟩'} Code
              </button>
              <button
                className="btn ghost"
                onClick={() => {
                  setCircuit({ num_qubits: 3, gates: [{ gate: 'h', target: 0, id: uid() }] })
                  setResult(null)
                  setAnalysis(null)
                  resetEditor()
                }}
              >
                ↺ Clear
              </button>
            </div>
          </div>

          <div className="canvas card">
            <CircuitDiagram
              numQubits={numQubits}
              gates={circuit.gates}
              readOnly={false}
              activeGate={!!activeGate}
              pendingTarget={pendingTarget}
              onWireClick={handleWireClick}
              onGateSelect={setSelectedGateId}
              selectedGateId={selectedGateId}
              highlightWires={activeGate && activeGate.controls > 0 ? Array.from({ length: numQubits }, (_, w) => w) : []}
            />
            {selectedGateId && (
              <div className="gate-toolbar">
                <button className="btn small" onClick={() => { const g = circuit.gates.find((x) => x.id === selectedGateId); if (g) openParam(g) }}>
                  {GATE_PALETTE.find((d) => d.id === circuit.gates.find((x) => x.id === selectedGateId)?.gate)?.params ? 'Edit param' : 'Gate: ' + circuit.gates.find((x) => x.id === selectedGateId)?.gate}
                </button>
                <button className="btn small danger" onClick={() => removeGate(selectedGateId)}>
                  Delete
                </button>
                <button className="btn small ghost" onClick={() => setSelectedGateId(null)}>
                  Close
                </button>
              </div>
            )}
            {wiresUnused.length > 0 && (
              <div className="canvas-foot">Unused wires: {wiresUnused.join(', ')}</div>
            )}
          </div>

          <div className="tabs">
            <button className={tab === 'sim' ? 'tab active' : 'tab'} onClick={() => setTab('sim')}>
              Simulation
            </button>
            <button className={tab === 'analyze' ? 'tab active' : 'tab'} onClick={() => setTab('analyze')}>
              Analysis
            </button>
            <button className={tab === 'code' ? 'tab active' : 'tab'} onClick={() => setTab('code')}>
              Code ({framework})
            </button>
            <button className="btn small ghost" onClick={run}>
              Re-run
            </button>
          </div>

          {err && <Err e={err} />}

          {tab === 'sim' && (
            <div className="result card">
              {busy === 'sim' ? <Spinner label="Simulating…" /> : <ResultsPanel result={result} />}
            </div>
          )}

          {tab === 'analyze' && (
            <div className="result card">
              {busy === 'sim' ? (
                <Spinner label="Analysing…" />
              ) : analysis ? (
                <div className="analysis">
                  {analysis.identification && (
                    <div className="analysis-id">
                      <b>Recognised pattern: {analysis.identification.name}</b>
                      <p>{analysis.identification.detail}</p>
                    </div>
                  )}
                  {analysis.facts.length > 0 && (
                    <div className="analysis-facts">
                      {analysis.facts.map((f, i) => (
                        <span className="fact-chip" key={i}>
                          {f.type === 'superposition' ? '⚛ superposition' : f.type === 'entanglement' ? '∞ entangled' : f.type === 'measurement' ? '⊗ measure' : '◈ gates'} · {f.message}
                        </span>
                      ))}
                    </div>
                  )}
                  {analysis.issues.length > 0 && (
                    <div className="analysis-issues">
                      <b>Issues</b>
                      {analysis.issues.map((is, i) => (
                        <div className="issue-line" key={i}>
                          {is.message}
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="analysis-steps">
                    <b>Step-by-step walkthrough</b>
                    {analysis.steps.map((s, i) => (
                      <div className="step-line" key={i}>
                        <span className="step-num">{i + 1}</span>
                        {s}
                      </div>
                    ))}
                  </div>
                  {analysis.suggestions.length > 0 && (
                    <div className="analysis-sugg">
                      <b>Suggestions</b>
                      {analysis.suggestions.map((s, i) => (
                        <div key={i}>{s.message}</div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <p className="faint">Click “Analyse” to get a structural walkthrough of your circuit.</p>
              )}
            </div>
          )}

          {tab === 'code' && (
            <div className="result card code-panel">
              {busy === 'code' ? (
                <Spinner label="Generating…" />
              ) : code[framework] ? (
                <>
                  <pre className="code-block">{code[framework]}</pre>
                  <button className="btn small ghost" onClick={() => navigator.clipboard.writeText(code[framework])}>
                    Copy
                  </button>
                </>
              ) : (
                <p className="faint">Click “Code” to generate Python for the current circuit.</p>
              )}
            </div>
          )}
        </div>
      </div>

      {editParam && (
        <div className="modal">
          <div className="modal-card">
            <h3>Set {editParam.def.full} angle</h3>
            <label>{editParam.def.paramHint || 'Parameter'}</label>
            <input value={paramVal} onChange={(e) => setParamVal(e.target.value)} placeholder="e.g. 1.570796" autoFocus />
            <div className="quick-angles">
              <button onClick={() => setParamVal(String(Math.PI / 2))}>π/2</button>
              <button onClick={() => setParamVal(String(Math.PI))}>π</button>
              <button onClick={() => setParamVal(String(Math.PI / 4))}>π/4</button>
            </div>
            <div className="modal-actions">
              <button className="btn ghost" onClick={() => setEditParam(null)}>
                Cancel
              </button>
              <button className="btn primary" onClick={saveParam}>
                Apply
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
