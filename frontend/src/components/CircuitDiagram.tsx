import { useMemo } from 'react'
import type { GateOp } from '../types'
import { gateLabel, layoutGates, GATE_MAP } from '../lib/gates'

const ROW_H = 56
const CELL_W = 76
const LABEL_W = 56
const RAIL_W = 34
const BOX_W = 46
const BOX_H = 34

interface Cell {
  row: number
  col: number
}

interface Props {
  numQubits: number
  gates: GateOp[]
  readOnly?: boolean
  activeGate?: boolean
  pendingTarget?: number | null
  onWireClick?: (wire: number) => void
  onGateSelect?: (gateId: string | null) => void
  selectedGateId?: string | null
  highlightWires?: number[]
}

export default function CircuitDiagram({
  numQubits,
  gates,
  readOnly = true,
  activeGate = false,
  pendingTarget = null,
  onWireClick,
  onGateSelect,
  selectedGateId = null,
  highlightWires = [],
}: Props) {
  const ops = useMemo(
    () => gates.map((g, i) => (g.id ? g : ({ ...g, id: `auto-${i}` } as GateOp))),
    [gates],
  )
  const cells = useMemo(() => layoutGates(numQubits, ops), [numQubits, ops])
  const maxCol = useMemo(() => {
    let m = 0
    for (const c of Object.values(cells)) m = Math.max(m, c.col)
    return m
  }, [cells])

  const height = numQubits * ROW_H + 24
  const width = LABEL_W + (maxCol + 1) * CELL_W + (readOnly || !activeGate ? RAIL_W * 0.5 : RAIL_W)
  const isAdding = !!activeGate
  const targetWire = pendingTarget

  const renderGateCell = (g: GateOp, cell: Cell) => {
    const def = GATE_MAP[g.gate]
    const isSelected = g.id === selectedGateId
    const controls = g.controls || []
    const targets = g.targets !== undefined ? g.targets : g.target !== undefined ? [g.target] : []
    const anchor = targets[0]
    const centerX = LABEL_W + cell.col * CELL_W
    const color = def ? def.color : '#7c6cf0'

    // control dots + connecting vertical lines
    return (
      <g key={g.id} onClick={() => onGateSelect && onGateSelect(isSelected ? null : g.id ?? null)} className="diag-gate-hover">
        {controls.length > 0 && (
          <>
            {controls.map((cw) => (
              <line
                key={'ctl' + cw}
                x1={centerX}
                y1={cw * ROW_H + 12}
                x2={centerX}
                y2={anchor * ROW_H + 12 + BOX_H}
                stroke={color}
                strokeWidth={isSelected ? 3 : 1.6}
              />
            ))}
            {controls.map((cw) => (
              <circle key={'dot' + cw} cx={centerX} cy={cw * ROW_H + 12} r={isSelected ? 6 : 4.5} fill={color} />
            ))}
          </>
        )}

        {g.gate === 'swap' && targets.length === 2 ? (
          <>
            {[targets[0], targets[1]].map((t) => (
              <g key={'sw' + t}>
                <line x1={centerX - 7} y1={t * ROW_H - 5} x2={centerX + 7} y2={t * ROW_H + 19} stroke={color} strokeWidth={2.2} />
                <line x1={centerX - 7} y1={t * ROW_H + 19} x2={centerX + 7} y2={t * ROW_H - 5} stroke={color} strokeWidth={2.2} />
              </g>
            ))}
          </>
        ) : (
          <>
            {g.gate === 'measure' ? (
              <>
                <rect x={centerX - BOX_W / 2} y={anchor * ROW_H + 12} width={BOX_W} height={BOX_H} rx={8} fill="none" stroke="#8ea0c9" strokeWidth={1.4} strokeDasharray="4 3" />
                <text x={centerX} y={anchor * ROW_H + 34} textAnchor="middle" fontSize={15} fill="#cbd5ef" fontWeight={700}>
                  M
                </text>
              </>
            ) : (
              <>
                <rect x={centerX - BOX_W / 2} y={anchor * ROW_H + 12} width={BOX_W} height={BOX_H} rx={8} fill={color} opacity={0.16} stroke={isSelected ? '#ffffff' : color} strokeWidth={isSelected ? 2.4 : 1.5} />
                <text x={centerX} y={anchor * ROW_H + 33} textAnchor="middle" fontSize={15} fill={color} fontWeight={700}>
                  {gateLabel(g)}
                </text>
              </>
            )}
          </>
        )}
      </g>
    )
  }

  const highlightSet = new Set(highlightWires)

  return (
    <div className="diagram-scroll">
      <svg width={width} height={height} style={{ minWidth: width }}>
        <defs>
          <pattern id="dotGrid" width="16" height="16" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="0.8" fill="#1c2547" />
          </pattern>
        </defs>

        <rect width={width} height={height} fill="url(#dotGrid)" />

        {Array.from({ length: numQubits }).map((_, w) => (
          <g key={'wire' + w}>
            <line x1={LABEL_W - 14} y1={w * ROW_H + 12 + BOX_H / 2} x2={width} y2={w * ROW_H + 12 + BOX_H / 2} stroke="#333f6b" strokeWidth={1.6} opacity={0.8} />
            <text x={LABEL_W - 34} y={w * ROW_H + 33} fontSize={14} fill="#8ea0c9" fontFamily="ui-monospace, monospace">
              q{w}
            </text>
            {isAdding && !readOnly && (highlightWires.length ? highlightSet.has(w) : true) && (
              <>
                <rect
                  x={LABEL_W + (maxCol + 1) * CELL_W - 8}
                  y={w * ROW_H + 12}
                  width={RAIL_W - 8}
                  height={BOX_H}
                  rx={7}
                  fill={targetWire === w ? '#5c6ff0' : '#232c52'}
                  stroke={targetWire === w ? '#93a4ff' : '#3d4a7c'}
                  strokeWidth={1.4}
                  cursor="pointer"
                  onClick={(e) => {
                    e.stopPropagation()
                    onWireClick && onWireClick(w)
                  }}
                >
                  <title>{targetWire === w ? 'target chosen' : 'place gate here'}</title>
                </rect>
                <text
                  x={LABEL_W + (maxCol + 1) * CELL_W - 4 + 7}
                  y={w * ROW_H + 34}
                  fontSize={16}
                  fill={targetWire === w ? '#fff' : '#7f8fc0'}
                  textAnchor="middle"
                  cursor="pointer"
                  onClick={(e) => {
                    e.stopPropagation()
                    onWireClick && onWireClick(w)
                  }}
                >
                  {targetWire === w ? '★' : '+'}
                </text>
              </>
            )}
          </g>
        ))}

        {ops.map((g) => (g.id && cells[g.id] ? renderGateCell(g, cells[g.id]) : null))}
      </svg>
    </div>
  )
}
