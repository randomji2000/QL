import { useEffect, useState } from 'react'
import type { Quiz, QuizGradeResult, QuizQuestion } from '../types'
import { api, getUserId } from '../api'
import { PageHead, Spinner, Err, LevelBadge } from '../components/ui'

export default function Quizzes() {
  const [quizzes, setQuizzes] = useState<Quiz[]>([])
  const [open, setOpen] = useState<Quiz | null>(null)
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [answers, setAnswers] = useState<number[]>([])
  const [grade, setGrade] = useState<QuizGradeResult | null>(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const [xp, setXp] = useState(0)

  useEffect(() => {
    api.quizzes().then((r) => setQuizzes(r.quizzes)).catch((e) => setErr(e.message))
    api.getProgress(getUserId()).then((p) => setXp(p.xp || 0)).catch(() => {})
  }, [])

  const openQuiz = async (q: Quiz) => {
    setBusy(true)
    setErr('')
    try {
      const r = await api.quiz(q.id)
      setOpen(q)
      setQuestions(r.quiz.questions || [])
      setAnswers(new Array(r.quiz.questions.length).fill(-1))
      setGrade(null)
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  const submit = async () => {
    if (!open || answers.includes(-1)) return
    setBusy(true)
    setErr('')
    try {
      const g = await api.gradeQuiz(open.id, answers)
      setGrade(g)
      const p = await api.recordActivity(getUserId(), 'quiz', { quiz_id: open.id, score: g.score })
      setXp(p.xp)
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  if (open) {
    return (
      <div className="quiz-page">
        <PageHead
          icon="✓"
          title={open.title}
          sub={`Module · ${open.module} — ${open.question_count} questions`}
        />
        <button className="back-link" onClick={() => setOpen(null)}>
          ← All quizzes
        </button>
        {err && <Err e={err} />}
        <div className="quiz-body">
          {questions.map((q, qi) => {
            const graded = grade !== null
            const userChoice = answers[qi]
            const correct = graded ? grade.results[qi].correct_index : -1
            return (
              <div key={q.id} className="card q-card">
                <div className="q-text">
                  <span className="q-num">Q{qi + 1}</span> {q.text}
                </div>
                <div className="q-options">
                  {q.options.map((opt, oi) => {
                    let cls = ''
                    if (graded) {
                      if (oi === correct) cls = 'correct'
                      else if (oi === userChoice) cls = 'wrong'
                    } else if (oi === userChoice) cls = 'selected'
                    return (
                      <button
                        key={oi}
                        className={'q-option ' + cls}
                        disabled={graded}
                        onClick={() =>
                          setAnswers((a) => a.map((v, i) => (i === qi ? oi : v)))
                        }
                      >
                        <span className="q-opt-key">{String.fromCharCode(65 + oi)}</span>
                        {opt}
                      </button>
                    )
                  })}
                </div>
                {graded && grade.results[qi].explanation && (
                  <div className={'q-exp' + (grade.results[qi].is_correct ? ' good' : ' bad')}>
                    {grade.results[qi].is_correct ? '✓ Correct. ' : '✗ '}
                    {grade.results[qi].explanation}
                  </div>
                )}
              </div>
            )
          })}
        </div>
        <div className="quiz-footer">
          {grade ? (
            <div className={'quiz-grade ' + (grade.passed ? 'pass' : 'fail')}>
              <span className="grade-big">{grade.score * 100}%</span>
              <span>{grade.correct}/{grade.total} correct · {grade.passed ? 'Passed — +30 XP' : 'Keep going!'}</span>
              <button className="btn primary" onClick={() => setOpen(null)}>
                Back to quizzes
              </button>
            </div>
          ) : (
            <div className="quiz-footer-actions">
              <span className="faint">{answers.filter((a) => a >= 0).length}/{questions.length} answered</span>
              <button className="btn primary" disabled={answers.includes(-1) || busy} onClick={submit}>
                {busy ? 'Grading…' : 'Submit answers'}
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="quiz-page">
      <PageHead icon="✓" title="Quizzes" sub="Test your understanding. Quizzes are graded instantly with an explanation for every answer." />
      {err && <Err e={err} />}
      <div className="card xp-strip">
        <b>🏅 {xp} XP</b> · earned by completing lessons, passing challenges and quizzes
      </div>
      <div className="module-grid">
        {quizzes.map((q) => (
          <button key={q.id} className="card module-card quiz-card" onClick={() => openQuiz(q)}>
            <div className="module-meta">
              <LevelBadge level={q.level} />
              <span className="faint">{q.question_count} questions</span>
            </div>
            <h3>{q.title}</h3>
            <p>Module: {q.module}</p>
            <div className="faint go-link">Take quiz →</div>
          </button>
        ))}
      </div>
    </div>
  )
}
