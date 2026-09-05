import { useState } from 'react'
import type { SimResult } from '../types'
import BlochSphere from './BlochSphere'

const fmt = (n: number) => (Math.abs(n) < 1e-6 ? 0 : Math.round(n * 1e6) / 1e6)
const pct = (n: number) => (n * 100).toFixed(2).replace(/\.00$/, '')

export default function ResultsPanel({ result }: { result: SimResult | null }) {
  const [tab, setTab] = useState<'prob' | 'counts' | 'sv' | 'bloch'>('prob')

  if (!result) {
    return (
      <div className="results empty">
        <div className="empty-icon">◍</div>
        <p>Run a circuit to see measurement probabilities, a state vector, and Bloch-sphere visualizations.</p>
      </div>
    )
  }

  if (result.error || !result.ok) {
    return (
      <div className="results">
        <div className="alert error">
          <b>Simulation failed.</b> {result.error || 'Unknown error'}
        </div>
      </div>
    )
  }

  const hasCounts = result.counts && Object.keys(result.counts).length > 0
  const sv = result.statevector
  const topProb = Math.max(...(result.probabilities || [0]))

  return (
    <div className="results">
      <div className="results-tabs">
        <button className={tab === 'prob' ? 'active' : ''} onClick={() => setTab('prob')}>
          Probabilities
        </button>
        {hasCounts && (
          <button className={tab === 'counts' ? 'active' : ''} onClick={() => setTab('counts')}>
            Counts
          </button>
        )}
        <button className={tab === 'sv' ? 'active' : ''} onClick={() => setTab('sv')}>
          State vector
        </button>
        {result.bloch && result.bloch.length > 0 && (
          <button className={tab === 'bloch' ? 'active' : ''} onClick={() => setTab('bloch')}>
            Bloch spheres
          </button>
        )}
      </div>

      {result.backend && (
        <div className="run-meta">
          backend <b>{result.backend}</b> · {result.num_qubits} qubit{result.num_qubits === 1 ? '' : 's'}
          {typeof result.runtime_ms === 'number' && <> · {result.runtime_ms} ms</>}
          {typeof result.purity === 'number' && <> · purity {fmt(result.purity)}</>}
        </div>
      )}

      {tab === 'prob' && (
        <div className="prob-bars">
          {result.probabilities?.map((p, i) => {
            const label = result.outcome_labels?.[i] ?? i.toString(2).padStart(result.num_qubits || 1, '0')
            const dom = Math.abs(p - topProb) < 1e-9
            return (
              <div className="prob-row" key={i}>
                <span className="prob-state">|{label}⟩</span>
                <div className="bar-track">
                  <div className={'bar' + (dom ? ' dom' : '')} style={{ width: `${Math.max(p * 100, p > 0 ? 1.2 : 0)}%` }} />
                </div>
                <span className="prob-val">{pct(p)}%</span>
              </div>
            )
          })}
          {result.probabilities && (
            <div className="prob-foot">
              {result.measured_qubits && result.measured_qubits.length > 0
                ? `Distilled from ${result.shots} shots over measured qubits.`
                : 'Exact statevector probabilities (no measurement).'}
            </div>
          )}
        </div>
      )}

      {tab === 'counts' && result.counts && (
        <div className="counts-grid">
          {Object.entries(result.counts)
            .sort((a, b) => a[0].localeCompare(b[0]))
            .map(([state, n]) => {
              const total = Object.values(result.counts as Record<string, number>).reduce((a, b) => a + b, 0)
              const frac = n / total
              return (
                <div className="count-row" key={state}>
                  <span className="prob-state">{state}</span>
                  <div className="bar-track">
                    <div className="bar" style={{ width: `${frac * 100}%` }} />
                  </div>
                  <span className="prob-val">
                    {n} · {pct(frac)}%
                  </span>
                </div>
              )
            })}
        </div>
      )}

      {tab === 'sv' && sv && (
        <div className="sv-table">
          {sv.components.map((c, i) => {
            return (
              <div className="sv-row" key={i}>
                <span className="prob-state">|{c.state}⟩</span>
                <span className="sv-amp">{c.amplitude ? c.amplitude : '—'}</span>
                <span className="sv-prob">{pct(c.probability)}%</span>
                <div className="bar-track sv-track">
                  <div className="bar dom" style={{ width: `${c.probability * 100}%` }} />
                </div>
              </div>
            )
          })}
        </div>
      )}

      {tab === 'bloch' && result.bloch && (
        <div className="bloch-grid">
          {result.bloch.map((b, i) => (
            <div className="bloch-cell" key={i}>
              <div className="bloch-title">q{i}</div>
              <BlochSphere x={b.x} y={b.y} z={b.z} />
              <div className="bloch-xyz">
                x {fmt(b.x)} · y {fmt(b.y)} · z {fmt(b.z)}
              </div>
            </div>
          ))}
          {result.entanglement && result.entanglement.length > 0 && (
            <div className="ent-note">
              {result.entanglement.map((e, i) => (
                <span key={i}>
                  S(q{i}) = {fmt(e)}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
