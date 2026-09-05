"""FastAPI application for the AI Quantum Learning Platform."""

import logging
import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import backends, challenges, courses, progress, quizzes, sandbox, tutor
from .analysis import analyze_circuit, generate_explanation
from .quantum.codegen import generate_code
from .quantum.simulator import CircuitError, circuit_stats, run_circuit
from .templates import get_template, list_templates

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("qstudio")

app = FastAPI(title="Quantum Studio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

START = time.time()


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------
class CircuitIn(BaseModel):
    num_qubits: int = Field(1, ge=1, le=18)
    gates: list = Field(default_factory=list)
    name: str = "untitled"


class RunRequest(BaseModel):
    circuit: CircuitIn
    backend: str = "local"
    shots: int = Field(1024, ge=1, le=100000)
    seed: int = 42


class CodeRunRequest(BaseModel):
    code: str = ""
    timeout: int = Field(30, ge=1, le=120)


class ChallengeRequest(BaseModel):
    challenge_id: str
    code: str = ""


class QuizRequest(BaseModel):
    quiz_id: str
    answers: list[int]


class ChatRequest(BaseModel):
    message: str
    circuit: CircuitIn | None = None
    progress: dict | None = None


class LessonRequest(BaseModel):
    lesson_id: str


class GenerateRequest(BaseModel):
    prompt: str = ""
    framework: str = "qiskit"
    circuit: CircuitIn | None = None


# --------------------------------------------------------------------------
# Core endpoints
# --------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok", "uptime_s": round(time.time() - START, 1),
            "backends": [b["id"] for b in backends.list_backends() if b["available"]]}


@app.get("/api/backends")
def get_backends():
    return {"backends": backends.list_backends()}


@app.post("/api/simulate")
def simulate(req: RunRequest):
    t0 = time.time()
    try:
        result = backends.run_on_backend(
            req.circuit.model_dump(), backend_id=req.backend, shots=req.shots, seed=req.seed
        )
    except CircuitError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        log.warning("simulate failed: %s", e)
        return {"ok": False, "error": f"Simulation error: {e}"}
    stats = circuit_stats(req.circuit.model_dump())
    result["ok"] = True
    result["runtime_ms"] = round((time.time() - t0) * 1000, 2)
    result["backend"] = req.backend
    result["stats"] = stats
    return result


@app.get("/api/templates")
def get_templates():
    return {"templates": list_templates()}


@app.get("/api/templates/{tid}")
def template_detail(tid: str):
    t = get_template(tid)
    if t is None:
        return {"ok": False, "error": "template not found"}
    code = {
        fw: generate_code(t, fw, with_imports=True)
        for fw in ("qiskit", "cirq", "pennylane", "braket")
    }
    return {"ok": True, "template": t, "code": code}


@app.post("/api/circuit/codegen")
def circuit_codegen(req: GenerateRequest):
    if req.circuit is None:
        return {"ok": False, "error": "circuit required"}
    return {"ok": True, "framework": req.framework,
            "code": generate_code(req.circuit.model_dump(), req.framework)}


@app.post("/api/circuit/analyze")
def circuit_analyze(req: GenerateRequest):
    if req.circuit is None:
        return {"ok": False, "error": "circuit required"}
    analysis = analyze_circuit(req.circuit.model_dump())
    analysis["ok"] = True
    analysis["steps"] = generate_explanation(req.circuit.model_dump())
    return analysis


# --------------------------------------------------------------------------
# Code lab / sandbox
# --------------------------------------------------------------------------
@app.post("/api/code/run")
def code_run(req: CodeRunRequest):
    return sandbox.run_user_code(req.code, timeout=req.timeout)


# --------------------------------------------------------------------------
# Courses / quizzes / challenges
# --------------------------------------------------------------------------
@app.get("/api/courses")
def get_courses():
    return {"modules": courses.list_modules()}


@app.get("/api/courses/{mid}")
def course_detail(mid: str):
    m = courses.get_module(mid)
    if m is None:
        return {"ok": False, "error": "module not found"}
    return {"ok": True, "module": m}


@app.get("/api/quizzes")
def get_quizzes():
    return {"quizzes": quizzes.list_quizzes()}


@app.get("/api/quizzes/{qid}")
def quiz_detail(qid: str):
    q = quizzes.get_quiz(qid)
    if q is None:
        return {"ok": False, "error": "quiz not found"}
    public = {**q, "questions": [{k: v for k, v in qq.items() if k != "answer"} for qq in q["questions"]]}
    return {"ok": True, "quiz": public}


@app.post("/api/quizzes/grade")
def quiz_grade(req: QuizRequest):
    return quizzes.grade_quiz(req.quiz_id, req.answers)


@app.get("/api/challenges")
def get_challenges():
    return {"challenges": challenges.list_challenges()}


@app.get("/api/challenges/{cid}")
def challenge_detail(cid: str):
    c = challenges.get_challenge(cid)
    if c is None:
        return {"ok": False, "error": "challenge not found"}
    return {"ok": True, "challenge": c}


@app.post("/api/challenges/run")
def challenge_run(req: ChallengeRequest):
    c = challenges.get_challenge(req.challenge_id)
    if c is None:
        return {"ok": False, "error": "challenge not found"}
    result = sandbox.run_challenge_tests(req.challenge_id, req.code, c)
    return result


# --------------------------------------------------------------------------
# AI tutor
# --------------------------------------------------------------------------
@app.post("/api/tutor/chat")
def tutor_chat(req: ChatRequest):
    circuit = req.circuit.model_dump() if req.circuit else None
    reply = tutor.handle_message(req.message, circuit=circuit, progress=req.progress)
    return reply


@app.get("/api/tutor/llm-status")
def tutor_llm_status():
    return {"llm_enabled": tutor._llm_enabled()}


# --------------------------------------------------------------------------
# Progress / dashboard
# --------------------------------------------------------------------------
def _user_id(req=None):
    return progress.new_user_id()


@app.get("/api/progress/{user_id}")
def get_progress(user_id: str):
    return progress.get_user(user_id)


@app.post("/api/progress/activity")
def record_activity(body: dict):
    user_id = body.get("user_id") or progress.new_user_id()
    return progress.record_activity(user_id, body.get("activity", "simulation"),
                                    body.get("payload", {}))


@app.get("/api/dashboard")
def dashboard():
    return progress.dashboard_stats()


@app.get("/api/dashboard/users")
def dashboard_users():
    return {"users": progress.all_users()}
