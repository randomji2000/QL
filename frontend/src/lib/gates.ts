import type { GateOp } from '../types'

export interface GateDef {
  id: string
  label: string
  full: string
  category: 'single' | 'two' | 'three' | 'special'
  controls: number
  arity: number // number of target qubits
  params: number
  paramHint?: string
  color: string
  desc: string
}

export const GATE_PALETTE: GateDef[] = [
  { id: 'h', label: 'H', full: 'Hadamard', category: 'single', controls: 0, arity: 1, params: 0, color: '#7c6cf0', desc: 'Create superposition' },
  { id: 'x', label: 'X', full: 'Pauli-X', category: 'single', controls: 0, arity: 1, params: 0, color: '#ef5350', desc: 'Flip |0> ↔ |1>' },
  { id: 'y', label: 'Y', full: 'Pauli-Y', category: 'single', controls: 0, arity: 1, params: 0, color: '#ef6c9c', desc: 'Bit + phase flip' },
  { id: 'z', label: 'Z', full: 'Pauli-Z', category: 'single', controls: 0, arity: 1, params: 0, color: '#42a5f5', desc: 'Flip phase of |1>' },
  { id: 's', label: 'S', full: 'Phase S', category: 'single', controls: 0, arity: 1, params: 0, color: '#26c6da', desc: '90° phase' },
  { id: 'sdg', label: 'S†', full: 'Phase S†', category: 'single', controls: 0, arity: 1, params: 0, color: '#26c6da', desc: '−90° phase' },
  { id: 't', label: 'T', full: 'Phase T', category: 'single', controls: 0, arity: 1, params: 0, color: '#26c6da', desc: '45° phase' },
  { id: 'tdg', label: 'T†', full: 'Phase T†', category: 'single', controls: 0, arity: 1, params: 0, color: '#26c6da', desc: '−45° phase' },
  { id: 'p', label: 'P(θ)', full: 'Phase', category: 'single', controls: 0, arity: 1, params: 1, paramHint: 'angle (radians)', color: '#ffa726', desc: 'Arbitrary phase' },
  { id: 'rx', label: 'Rx', full: 'Rotate X', category: 'single', controls: 0, arity: 1, params: 1, paramHint: 'angle (radians)', color: '#ffa726', desc: 'Rotation about X' },
  { id: 'ry', label: 'Ry', full: 'Rotate Y', category: 'single', controls: 0, arity: 1, params: 1, paramHint: 'angle (radians)', color: '#ffa726', desc: 'Rotation about Y' },
  { id: 'rz', label: 'Rz', full: 'Rotate Z', category: 'single', controls: 0, arity: 1, params: 1, paramHint: 'angle (radians)', color: '#ffa726', desc: 'Rotation about Z' },
  { id: 'cx', label: 'CNOT', full: 'Controlled-X', category: 'two', controls: 1, arity: 1, params: 0, color: '#66bb6a', desc: 'Flip target if control = |1>' },
  { id: 'cz', label: 'CZ', full: 'Controlled-Z', category: 'two', controls: 1, arity: 1, params: 0, color: '#66bb6a', desc: 'Phase if both |1>' },
  { id: 'swap', label: 'SWAP', full: 'SWAP', category: 'two', controls: 0, arity: 2, params: 0, color: '#66bb6a', desc: 'Exchange two qubits' },
  { id: 'ccx', label: 'CCX', full: 'Toffoli', category: 'three', controls: 2, arity: 1, params: 0, color: '#8d6e63', desc: 'Flip target if both controls = |1>' },
  { id: 'measure', label: 'M', full: 'Measure', category: 'special', controls: 0, arity: 1, params: 0, color: '#78909c', desc: 'Projective measurement' },
  { id: 'reset', label: 'Rst', full: 'Reset', category: 'special', controls: 0, arity: 1, params: 0, color: '#78909c', desc: 'Reset qubit to |0>' },
]

export const GATE_MAP: Record<string, GateDef> = Object.fromEntries(
  GATE_PALETTE.map((g) => [g.id, g]),
)

export const DEFAULT_PARAMS: Record<string, number> = {
  p: Math.PI / 2,
  rx: Math.PI / 2,
  ry: Math.PI / 2,
  rz: Math.PI / 2,
}

let uidCounter = 0
export function uid(): string {
  uidCounter += 1
  return `g${uidCounter}-${Date.now().toString(36)}`
}

/** Layout gates into (row, col) grid cells. Returns map gate-id -> {row, col}. */
export function layoutGates(numQubits: number, gates: GateOp[]): Record<string, { row: number; col: number }> {
  const cells: Record<string, { row: number; col: number }> = {}
  const wireCol = new Array(numQubits).fill(0)
  for (const g of gates) {
    if (!g.id) continue
    const wires = [
      ...(g.controls || []),
      ...(g.targets !== undefined ? g.targets : g.target !== undefined ? [g.target] : []),
    ]
    let c = 1
    if (wires.length) c = Math.max(...wires.map((w) => wireCol[w])) + 1
    else c = Math.max(...wireCol) + 1
    for (const w of wires) wireCol[w] = c
    cells[g.id] = { row: g.target ?? g.targets?.[0] ?? 0, col: c }
  }
  return cells
}

export function gateWires(g: GateOp): number[] {
  const targets = g.targets !== undefined ? g.targets : g.target !== undefined ? [g.target] : []
  return [...(g.controls || []), ...targets]
}

export function maxColumns(numQubits: number, gates: GateOp[]): number {
  const cells = layoutGates(numQubits, gates)
  let m = 1
  for (const c of Object.values(cells)) m = Math.max(m, c.col)
  return m
}

export function gateLabel(g: GateOp): string {
  const def = GATE_MAP[g.gate]
  if (g.gate === 'measure') return 'M'
  if (!def) return g.gate.toUpperCase()
  if (def.params && g.params && g.params.length) {
    const v = Math.round(g.params[0] * 100) / 100
    return `${def.label.replace(/\(.*\)$/, '')}(${v})`
  }
  return def.label
}

export const fmtAngle = (r: number) =>
  r === Math.PI ? 'π' : r === Math.PI / 2 ? 'π/2' : r === -Math.PI / 2 ? '−π/2' : r === Math.PI / 4 ? 'π/4' : `${Math.round(r * 1000) / 1000}`
