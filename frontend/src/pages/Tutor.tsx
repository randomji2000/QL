import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { api, getUserId } from '../api'
import type { TutorReply, UserProgress } from '../types'
import { PageHead, Spinner } from '../components/ui'

const QUICK_TOPICS = [
  'What is superposition?',
  'Explain a Bell state to me like I’m a beginner',
  'How does Grover’s search work?',
  'Give me a 3-question quiz on QFT',
  'What should I learn after CNOT?',
]

export default function Tutor() {
  const loc = useLocation()
  const askState = (loc.state as { question?: string } | null)?.question
  const [replies, setReplies] = useState<{ role: string; text: string }[]>([])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const [llm, setLlm] = useState(false)
  const [prog, setProg] = useState<UserProgress | null>(null)
  const chatRef = useRef<HTMLDivElement>(null)
  const startedRef = useRef(false)

  useEffect(() => {
    api.tutorStatus().then((r) => setLlm(r.llm_enabled)).catch(() => {})
    api.getProgress(getUserId()).then(setProg).catch(() => {})
  }, [])

  useEffect(() => {
    if (askState && !startedRef.current) {
      startedRef.current = true
      ask(askState)
    }
  }, [askState])

  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: 'smooth' })
  }, [replies, thinking])

  const ask = async (msg?: string) => {
    const m = (msg ?? input).trim()
    if (!m || thinking) return
    setInput('')
    setReplies((r) => [...r, { role: 'you', text: m }])
    setThinking(true)
    try {
      const r: TutorReply = await api.tutorChat(m, null, prog)
      setReplies((x) => [...x, { role: 'tutor', text: r.text }])
    } catch (e) {
      setReplies((x) => [...x, { role: 'tutor', text: 'Sorry — the tutor could not respond right now. ' + (e instanceof Error ? e.message : '') }])
    } finally {
      setThinking(false)
    }
  }

  return (
    <div className="tutor-page">
      <PageHead
        icon="✺"
        title="AI Tutor"
        sub={
          llm
            ? 'Rule-based core with optional LLM enhancement enabled.'
            : 'Rule-based tutor — fully offline, no API key needed.'
        }
      />
      <div className="tutor-layout">
        <div className="chat-card card">
          <div className="chat-list" ref={chatRef}>
            {replies.length === 0 && (
              <div className="chat-welcome">
                <div className="tutor-avatar">✺</div>
                <h3>Hi, I’m your quantum tutor.</h3>
                <p>
                  Ask me to explain any concept, walk you through an algorithm, suggest a learning path, or quiz you.
                  I can also analyse any circuit you build in the lab.
                </p>
                <div className="welcome-chips">
                  {QUICK_TOPICS.map((q) => (
                    <button key={q} className="chip starter" onClick={() => ask(q)}>
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {replies.map((m, i) => (
              <div key={i} className={m.role === 'you' ? 'msg you' : 'msg tutor'}>
                <div className="msg-bubble">{m.text}</div>
              </div>
            ))}
            {thinking && (
              <div className="msg tutor">
                <div className="msg-bubble typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}
          </div>
          <div className="chat-composer">
            <input
              placeholder="Ask anything about quantum computing…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && ask()}
            />
            <button className="btn primary" onClick={() => ask()} disabled={thinking || !input.trim()}>
              Send
            </button>
          </div>
        </div>

        <aside className="tutor-side card">
          <h3>What can I help with?</h3>
          <div className="tutor-help-list">
            <div className="help-item">
              <b>📖 Concept explanations</b>
              <p>Superposition, entanglement, teleportation, Grover…</p>
            </div>
            <div className="help-item">
              <b>🛣️ Learning path</b>
              <p>Tell me what you know and get a tailored curriculum.</p>
            </div>
            <div className="help-item">
              <b>🔬 Circuit analysis</b>
              <p>Open any circuit in the Lab and ask me to explain it.</p>
            </div>
            <div className="help-item">
              <b>🧪 Quiz me</b>
              <p>I’ll generate quick concept checks with feedback.</p>
            </div>
            <div className="help-item">
              <b>🐞 Debugging help</b>
              <p>Paste errors from the Code Lab and I’ll diagnose them.</p>
            </div>
          </div>
          {prog && (
            <div className="tutor-prog">
              <b>Your progress</b>
              <div className="mini-stats">
                <span>🏅 {prog.xp} XP</span>
                <span>📚 {prog.completed_lessons.length} lessons</span>
                <span>⚡ {Object.keys(prog.challenges || {}).length} challenges</span>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}
