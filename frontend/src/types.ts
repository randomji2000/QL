export interface GateOp {
  gate: string
  target?: number
  targets?: number[]
  controls?: number[]
  params?: number[]
  condition?: { qubit: number; value: number }
  id?: string
}

export interface Circuit {
  num_qubits: number
  gates: GateOp[]
  name?: string
}

export interface BackendInfo {
  id: string
  name: string
  provider: string
  type: string
  max_qubits: number
  available: boolean
  description: string
}

export interface SimResult {
  ok?: boolean
  error?: string
  num_qubits?: number
  statevector?: {
    components: { state: string; amplitude?: string | null; probability: number }[]
    dimension: number
  }
  probabilities?: number[]
  counts?: Record<string, number> | null
  shots?: number
  bloch?: { x: number; y: number; z: number }[]
  entanglement?: number[]
  purity?: number
  entanglement_metric?: number
  outcome_labels?: string[]
  measured_qubits?: number[]
  runtime_ms?: number
  backend?: string
  stats?: CircuitStats
}

export interface CircuitStats {
  num_gates: number
  depth: number
  gate_counts: Record<string, number>
  used_qubits: number[]
  unused_qubits: number[]
  measured: number[]
}

export interface CircuitAnalysis {
  ok: boolean
  steps: string[]
  issues: { type: string; severity: string; message: string; qubit?: number }[]
  suggestions: { type: string; severity: string; message: string; qubit?: number }[]
  facts: { type: string; message: string }[]
  identification: { id: string; name: string; detail: string } | null
  stats: CircuitStats
  num_qubits: number
}

export interface TemplateSummary {
  id: string
  name: string
  category: string
  num_qubits: number
  level: string
  summary: string
  concepts: string[]
}

export interface TemplateDetail {
  id: string
  name: string
  category: string
  num_qubits: number
  level: string
  summary: string
  concepts: string[]
  description: string
  gates: GateOp[]
  expected: Record<string, string>
  code: Record<string, string>
}

export interface ModuleSummary {
  id: string
  title: string
  level: string
  description: string
  icon: string
  lesson_count: number
}

export interface LessonContentBlock {
  type: 'p' | 'code'
  text?: string
  title?: string
  circuit?: string | Circuit
}

export interface Lesson {
  id: string
  title: string
  duration: string
  concept: string
  content: LessonContentBlock[]
}

export interface CourseModule {
  id: string
  title: string
  level: string
  description: string
  icon: string
  lessons: Lesson[]
}

export interface QuizQuestion {
  id: string
  text: string
  options: string[]
}

export interface Quiz {
  id: string
  title: string
  module: string
  level: string
  question_count: number
  questions?: QuizQuestion[]
}

export interface QuizGradeResult {
  quiz_id: string
  total: number
  correct: number
  score: number
  passed: boolean
  results: {
    question: string
    selected: number
    correct_index: number
    is_correct: boolean
    explanation: string
  }[]
}

export interface Challenge {
  id: string
  title: string
  module: string
  level: string
  concept: string
  description: string
  starter: string
  solution: string
  tests: string[]
}

export interface ChallengeSummary {
  id: string
  title: string
  module: string
  level: string
  concept: string
  description: string
}

export interface CodeRunResult {
  ok: boolean
  stdout: string
  stderr: string
  artifacts: Record<string, unknown>
  returncode?: number
}

export interface UserProgress {
  user_id: string
  completed_lessons: string[]
  quiz_scores: Record<string, number>
  challenges: Record<string, { passed: boolean }>
  simulations: number
  circuits_built: number
  templates_used: string[]
  xp: number
  created_at?: number
  last_active?: number
}

export interface DashboardStats {
  total_users: number
  total_lessons_completed: number
  total_simulations: number
  total_circuits_built: number
  total_xp: number
  total_quiz_attempts: number
  avg_quiz_score: number
  total_challenges_passed: number
  module_completions: Record<string, number>
  active_today: number
}

export interface TutorReply {
  kind: string
  text: string
  suggestions?: string[]
}
