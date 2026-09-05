import { ReactNode } from 'react'

export function Spinner({ label = 'Working…' }: { label?: string }) {
  return (
    <div className="spinner-wrap">
      <div className="spinner" />
      <span>{label}</span>
    </div>
  )
}

export function PageHead({ icon, title, sub }: { icon?: string; title: string; sub?: string }) {
  return (
    <header className="page-head">
      <div className="page-title-row">
        {icon && <span className="page-icon">{icon}</span>}
        <div>
          <h1>{title}</h1>
          {sub && <p>{sub}</p>}
        </div>
      </div>
    </header>
  )
}

export function Alert({ kind, children }: { kind: 'info' | 'error' | 'ok' | 'warn'; children: ReactNode }) {
  const cls = kind === 'ok' ? 'success' : kind
  return <div className={`alert ${cls}`}>{children}</div>
}

export function Err({ e }: { e: unknown }) {
  const msg = e instanceof Error ? e.message : String(e)
  if (!msg) return null
  return <Alert kind="error">{msg}</Alert>
}

export function Pill({ children }: { children: ReactNode }) {
  return <span className="pill">{children}</span>
}

export function LevelBadge({ level }: { level: string }) {
  const cap = level.charAt(0).toUpperCase() + level.slice(1).toLowerCase()
  const cls = cap === 'Beginner' ? 'Beginner' : cap === 'Intermediate' ? 'Intermediate' : 'Advanced'
  return <span className={`badge ${cls}`}>{cap}</span>
}
