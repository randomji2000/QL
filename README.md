# Quantum Studio — AI-Based Interactive Quantum Algorithm Learning Platform

An interactive, full-stack learning platform for quantum computing. Learners build circuits on a visual
wire grid or write real quantum Python, run them against multiple simulation backends (local statevector
engine, Qiskit Aer, Cirq), inspect rich visualizations (probability bars, counts, state vectors, three.js
Bloch spheres, entanglement entropy), and follow structured courses, auto-graded challenges and quizzes —
with a deterministic AI tutor and circuit analyst that work fully offline.

## Quick start

Backend (FastAPI, port 8010):

```bash
cd backend
pip install -r requirements.txt        # if not already installed
uvicorn app.main:app --port 8010
```

Frontend (Vite dev server, port 5173, proxies `/api` to the backend):

```bash
cd frontend
npm install
npm run dev
```

Open the frontend URL. Simulating and running code does not need any API key — the rule-based engine is
always available. To *enhance* tutor answers with an LLM, provide your own key to the backend via the
environment variables documented in `backend/app/tutor.py` (`USER_LLM_API_KEY`, `USER_LLM_BASE_URL`,
`USER_LLM_MODEL`). The platform never reads agent-environment keys.

## Repository layout

| Path | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI wiring for all 26 `/api` routes, CORS |
| `backend/app/quantum/gates.py` | Gate matrices, aliases, controlled-gate builders |
| `backend/app/quantum/simulator.py` | Deterministic simulator (≤18 qubits), stats, partial trace, Bloch, entropy |
| `backend/app/quantum/codegen.py` | Circuit → Qiskit / Cirq / PennyLane / Braket code generation |
| `backend/app/backends.py` | Backend registry/probes and Aer/Cirq dispatch |
| `backend/app/templates.py` | 12 verified standard-algorithm templates |
| `backend/app/analysis.py` | Circuit diagnostics, redundancy detection, step-by-step explanations |
| `backend/app/tutor.py` | Rule-based tutor core (concept / learning-path / circuit intents) + optional LLM |
| `backend/app/courses.py`, `quizzes.py`, `challenges.py` | Learning content and assessments |
| `backend/app/sandbox.py` | Subprocess code runner with import whitelist and timeouts |
| `backend/app/progress.py` | JSON user store, XP rewards, dashboard aggregation |
| `frontend/` | React + TypeScript + Vite single-page application |

## Delivery Table (Expected Deliverables)

The table below maps each requirement from the platform specification to where it is implemented and how it
was verified.

| # | Requirement | Implementation | Verified |
|---|-------------|----------------|----------|
| 1 | Interactive circuit designer (drag & drop / graphical) | `Circuit Lab`: gate palette (single/two/three/special), wire/cell grid with target + control click-to-place, param editor modal, delete, live re-layout (`frontend/src/pages/CircuitLab.tsx`, `components/CircuitDiagram.tsx`) | Build + manual UI walkthrough |
| 2 | Code-based circuit designer | `Code Lab`: sandboxed Python editor with Qiskit, Cirq, PennyLane, Braket modes; template insertion; `Circuit Lab → Code` export for the same JSON circuit (`/api/circuit/codegen`) | `verify_templates.py`; `/api/code/run` smoke tests |
| 3 | Multiple execution backends | `local` (built-in statevector), `aer_statevector`, `aer_qasm`, `cirq`, selectable per run with live availability probe (`backend/app/backends.py`) | All four backends tested against the 12 templates |
| 4 | Built-in quantum simulator | `backend/app/quantum/simulator.py` — pure NumPy, 18-qubit cap, vectorized no-measure path + shot path for measurement/conditioned gates | 12/12 templates PASS |
| 5 | Standard algorithm library (templates) | Deutsch–Jozsa, Bernstein–Vazirani, QFT(3), Grover(2,3), QPE(2), Teleportation, Superdense Coding, SWAP, Bell, GHZ, W-state (`backend/app/templates.py`) | Numerical verification script + API |
| 6 | AI assistant (explain / generate / debug / recommend) | `/api/tutor/chat` intent engine + `/api/circuit/analyze` step-by-step walkthrough; concept shortcuts embedded in lessons; error debugging wired into Code Lab; learning-path suggestions | API smoke tests for concept + analyze intents |
| 7 | Personalized learning paths / recommendations | Tutor recommends next steps from `UserProgress`; Home page “suggested path”; module-progress tracking in Learn | Progress API round-trip |
| 8 | Structured, interactive course content | 5 modules / 16 lessons, each lesson embeds live runnable demo circuits with “Open in Lab” (`backend/app/courses.py`, `frontend/src/pages/Learn.tsx`) | Lesson content parsed by frontend; demos simulate |
| 9 | Quizzes with instant feedback | 3 graded quizzes; per-question explanations shown after grading (`backend/app/quizzes.py`, `Quizzes.tsx`) | `/api/quizzes/grade` smoke tests (100% and failing cases) |
| 10 | Challenges with hidden-test judging | 4 challenges (Bell, GHZ, Teleport, Grover) executed in the sandbox against hidden assertions (`backend/app/challenges.py`, `Challenges.tsx`) | Correct/wrong solution tests |
| 11 | Progress tracking per learner | `UserProgress` (lessons, quiz scores, challenges, simulations, XP) keyed by stable per-browser user id (`backend/app/progress.py`, `frontend/src/api.ts`) | `GET/POST /api/progress/*` tested |
| 12 | Instructor dashboard (aggregate analytics) | `/api/dashboard` aggregates learners, completions, simulations, XP, quiz averages, module completions, active today; UI at `Dashboard.tsx` | Aggregation endpoint tested |
| 13 | Visualizations (incl. Bloch sphere) | three.js Bloch spheres, probability bars, counts histograms, state-vector/amplitude table, entanglement entropy panel (`frontend/src/components/ResultsPanel.tsx`, `BlochSphere.tsx`) | API returns bloch/probabilities/counts; UI renders |
| 14 | Sandboxed user-code execution (safety) | Subprocess runner with import whitelist, wall-clock timeout, stdout/stderr capture, `__Q*__` marker protocol (`backend/app/sandbox.py`) | `/api/code/run` tested incl. disallowed imports |
| 15 | Deliverable documentation incl. delivery table | This README | — |

## Conventions used across the stack

- JSON circuit format: `{"num_qubits": N, "gates": [{"gate", "target"/"targets", "controls", "params", "condition"}]}`
- Bit ordering follows the text-book convention **q0 is the rightmost (least-significant) bit** — used
  consistently in templates, simulators, code generation, and outcome labels.
- 12 templates are verified by `backend/verify_templates.py` (numerical expectations), so lessons,
  examples and the AI analyst share one source of truth.
