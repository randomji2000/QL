import type {
  BackendInfo, Challenge, ChallengeSummary, Circuit, CircuitAnalysis, CodeRunResult,
  CourseModule, DashboardStats, ModuleSummary, Quiz, QuizGradeResult, QuizQuestion,
  SimResult, TemplateDetail, TemplateSummary, TutorReply, UserProgress,
} from './types'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const j = await res.json()
      if (j.detail) detail = j.detail
      if (j.error) detail = j.error
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string; backends: string[] }>('/api/health'),
  backends: () => request<{ backends: BackendInfo[] }>('/api/backends'),
  simulate: (circuit: Circuit, backend: string, shots: number) =>
    request<SimResult>('/api/simulate', {
      method: 'POST',
      body: JSON.stringify({ circuit, backend, shots, seed: 42 }),
    }),
  templates: () => request<{ templates: TemplateSummary[] }>('/api/templates'),
  template: async (id: string) => {
    const raw = await request<{ ok: boolean; template: Omit<TemplateDetail, 'code'>; code: Record<string, string> }>(`/api/templates/${id}`)
    return { ...raw.template, code: raw.code } as TemplateDetail
  },
  analyzeCircuit: (circuit: Circuit) =>
    request<CircuitAnalysis>('/api/circuit/analyze', {
      method: 'POST',
      body: JSON.stringify({ circuit }),
    }),
  generateCode: (circuit: Circuit, framework: string) =>
    request<{ ok: boolean; code: string }>('/api/circuit/codegen', {
      method: 'POST',
      body: JSON.stringify({ circuit, framework }),
    }),
  runCode: (code: string, timeout = 25) =>
    request<CodeRunResult>('/api/code/run', {
      method: 'POST',
      body: JSON.stringify({ code, timeout }),
    }),
  courses: () => request<{ modules: ModuleSummary[] }>('/api/courses'),
  course: (id: string) => request<{ ok: boolean; module: CourseModule }>(`/api/courses/${id}`),
  quizzes: () => request<{ quizzes: Quiz[] }>('/api/quizzes'),
  quiz: (id: string) => request<{ ok: boolean; quiz: Quiz & { questions: QuizQuestion[] } }>(`/api/quizzes/${id}`),
  gradeQuiz: (quizId: string, answers: number[]) =>
    request<QuizGradeResult>('/api/quizzes/grade', {
      method: 'POST',
      body: JSON.stringify({ quiz_id: quizId, answers }),
    }),
  challenges: () => request<{ challenges: ChallengeSummary[] }>('/api/challenges'),
  challenge: (id: string) => request<{ ok: boolean; challenge: Challenge }>(`/api/challenges/${id}`),
  runChallenge: (challengeId: string, code: string) =>
    request<{ ok: boolean; passed: boolean; stdout: string; stderr: string }>('/api/challenges/run', {
      method: 'POST',
      body: JSON.stringify({ challenge_id: challengeId, code }),
    }),
  tutorChat: (message: string, circuit?: Circuit | null, progress?: UserProgress | null) =>
    request<TutorReply>('/api/tutor/chat', {
      method: 'POST',
      body: JSON.stringify({ message, circuit: circuit || undefined, progress: progress || undefined }),
    }),
  tutorStatus: () => request<{ llm_enabled: boolean }>('/api/tutor/llm-status'),
  getProgress: (userId: string) => request<UserProgress>(`/api/progress/${userId}`),
  recordActivity: (userId: string, activity: string, payload?: Record<string, unknown>) =>
    request<UserProgress>('/api/progress/activity', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, activity, payload: payload || {} }),
    }),
  dashboard: () => request<DashboardStats>('/api/dashboard'),
}

export const USER_KEY = 'qstudio_user_id'

export function getUserId(): string {
  let id = localStorage.getItem(USER_KEY)
  if (!id) {
    id = 'user-' + Math.random().toString(16).slice(2, 10)
    localStorage.setItem(USER_KEY, id)
  }
  return id
}
