"""AI tutor engine.

Hybrid design:
  * a deterministic, always-on reasoning core that explains concepts, analyses
    circuits, detects errors and suggests optimizations (no external service
    required);
  * an optional LLM enhancement that is only used when the *user* configures
    their own model via the USER_LLM_* environment variables.

The platform never reads the agent environment's LLM credentials.
"""

import json
import os
import re
import urllib.request
import urllib.error

from .analysis import analyze_circuit, concept_gallery, generate_explanation
from .templates import list_templates

_INTENTS = [
    (re.compile(r"(what is|explain|define|what's|describe|about)\s+(a |the )?(qubit|superposition|entanglement|measurement|hadamard|cnot|oracle|qft|grover|phase estimation|teleportation|deutsch|bernstein|decoherence|no[ -]cloning|density matrix|quantum advantage|bloch|tensor product|interference|qubit)", re.I), "concept"),
    (re.compile(r"(hello|hi|hey|help|what can you do|who are you)", re.I), "greeting"),
    (re.compile(r"(analy|check|review|debug|fix|optimize|improve|problem|wrong|error|suggestion).*(circuit|code|gate)", re.I), "circuit"),
    (re.compile(r"(circuit|analyze|my circuit|check this)", re.I), "circuit"),
]

_KEYWORDS = {
    "qubit": "qubit", "superposition": "superposition", "entanglement": "entanglement",
    "measure": "measurement", "hadamard": "hadamard", "cnot": "cnot",
    "oracle": "oracle", "qft": "qft", "fourier": "qft", "grover": "grover",
    "search": "grover", "phase estimation": "phase-estimation",
    "teleportation": "teleportation", "teleport": "teleportation",
    "deutsch": "deutsch-jozsa", "bernstein": "bernstein-vazirani",
    "decoherence": "decoherence", "no-cloning": "no-cloning", "cloning": "no-cloning",
    "density matrix": "density-matrix", "bloch": "bloch-sphere",
    "tensor": "tensor-product", "advantage": "quantum-advantage",
}


def _llm_enabled():
    return bool(os.getenv("USER_LLM_API_KEY"))


def _llm_config():
    return {
        "api_key": os.getenv("USER_LLM_API_KEY", ""),
        "base_url": os.getenv("USER_LLM_BASE_URL", "https://api.openai.com/v1"),
        "model": os.getenv("USER_LLM_MODEL", "gpt-4o-mini"),
    }


def _call_llm(messages, max_tokens=700):
    """Call an OpenAI-compatible chat-completions endpoint with user credentials."""
    cfg = _llm_config()
    if not cfg["api_key"]:
        return None
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    payload = json.dumps({
        "model": cfg["model"],
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.4,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {cfg['api_key']}")
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None


def _greeting():
    return (
        "I'm your AI quantum tutor. I can:\n"
        "  • explain concepts (qubits, superposition, entanglement, QFT, Grover, QPE, ...)\n"
        "  • analyze your circuit for errors and optimizations\n"
        "  • help debug and generate Qiskit / Cirq / PennyLane code\n"
        "  • recommend a personalized learning path\n\n"
        "Try: 'explain entanglement', 'check my circuit', or 'what should I learn next?'"
    )


def _recommend_path(progress=None):
    modules = [
        ("module-1", "Quantum Fundamentals", "Beginner"),
        ("module-2", "Entanglement & Multi-Qubit Gates", "Beginner"),
        ("module-3", "Quantum Gates in Depth", "Intermediate"),
        ("module-4", "Core Quantum Algorithms", "Intermediate"),
        ("module-5", "Advanced Algorithms", "Advanced"),
    ]
    done = set((progress or {}).get("completed_lessons", []))
    for mid, title, lvl in modules:
        if not any(l.startswith(mid.split("-")[1] + "-") for l in done):
            return (f"Based on your progress, the best next step is **{title}** ({lvl}). "
                    "Start with its first lesson, then try the interactive circuit demo and quiz.")
    return ("You have covered all modules. Level up by exploring the advanced circuit "
            "templates (QPE, teleportation, Grover) in the Circuit Lab, or try the coding challenges.")


def handle_message(message, circuit=None, progress=None):
    """Entry point for the tutor chat."""
    message = (message or "").strip()
    lower = message.lower()

    # Learning path request
    if re.search(r"(what should i learn|learning path|recommend|next step|roadmap|syllabus)", lower):
        return {"kind": "text", "text": _recommend_path(progress),
                "suggestions": ["Explain superposition", "Show me a Bell state circuit", "What is Grover's algorithm?"]}

    # Circuit analysis
    if circuit is not None and any(w in lower for w in ["analy", "check", "review", "debug", "fix", "help me", "what does", "circuit"]):
        analysis = analyze_circuit(circuit)
        lines = ["**Circuit analysis**\n"]
        lines.append(f"- {analysis['stats']['num_gates']} gates, depth {analysis['stats']['depth']}, "
                     f"{analysis['num_qubits']} qubits")
        if analysis["identification"]:
            lines.append(f"- Pattern: **{analysis['identification']['name']}**")
        if analysis["issues"]:
            lines.append("\nIssues:")
            for it in analysis["issues"][:6]:
                lines.append(f"  - {it['severity'].upper()}: {it['message']}")
        if analysis["suggestions"]:
            lines.append("\nOptimizations:")
            for s in analysis["suggestions"][:4]:
                lines.append(f"  - {s['message']}")
        if analysis["facts"]:
            lines.append("\nObservations:")
            for f_ in analysis["facts"][:4]:
                lines.append(f"  - {f_['message']}")
        if not analysis["issues"] and not analysis["suggestions"]:
            lines.append("\nNo obvious errors found — the circuit looks clean.")
        return {"kind": "text", "text": "\n".join(lines),
                "suggestions": ["Explain this circuit step by step", "What concepts does this use?", "Optimize it further"]}

    # Step-by-step explanation of current circuit
    if circuit is not None and any(w in lower for w in ["step", "walk", "explain the circuit", "what does this circuit"]):
        steps = generate_explanation(circuit)
        return {"kind": "text", "text": "Here's what each operation does:\n\n- " + "\n- ".join(steps),
                "suggestions": ["Analyze this circuit", "What's the expected measurement outcome?"]}

    # Concept intent via keywords
    concept = None
    for word, c in _KEYWORDS.items():
        if word in lower:
            concept = c
            break
    if concept is None:
        for pat, intent in _INTENTS:
            if intent == "concept" and pat.search(lower):
                concept = "qubit"  # fallback to a general explanation
                break

    if concept and concept in concept_gallery():
        base = concept_gallery()[concept]
        reply = f"**{concept.replace('-', ' ').title()}**\n\n{base}"
        # add a practice suggestion
        templates = list_templates()
        related = {"entanglement": "bell", "superposition": "bell", "measurement": "bell",
                   "hadamard": "bell", "cnot": "bell", "oracle": "deutsch-jozsa",
                   "qft": "qft-3", "grover": "grover-2", "phase-estimation": "qpe-2",
                   "teleportation": "teleportation", "deutsch-jozsa": "deutsch-jozsa",
                   "bernstein-vazirani": "bernstein-vazirani"}
        if concept in related:
            reply += f"\n\nTry it hands-on: load the **{related[concept]}** template in the Circuit Lab and run it."
        return {"kind": "text", "text": reply,
                "suggestions": ["Explain " + k for k in ["entanglement", "phase estimation", "Grover's algorithm"][:3]]}

    if _INTENTS[1][0].search(lower):
        return {"kind": "text", "text": _greeting(),
                "suggestions": ["Explain superposition", "What is entanglement?", "Recommend a learning path"]}

    # LLM enhancement (only if the user configured their own key)
    if _llm_enabled():
        sys_prompt = ("You are an expert quantum computing tutor for an interactive learning platform. "
                      "Answer concisely and pedagogically. Use plain language and analogies. "
                      "Keep answers under 250 words. If the user shares code, give concrete fixes.")
        if circuit is not None:
            circ_json = json.dumps(circuit)
            sys_prompt += f"\n\nThe user also has this circuit open: {circ_json}. Relate your answer to it when relevant."
        out = _call_llm([{"role": "system", "content": sys_prompt},
                         {"role": "user", "content": message}])
        if out:
            return {"kind": "text", "text": out,
                    "suggestions": ["Explain entanglement", "Analyze my circuit", "What should I learn next?"]}

    # Fallback: local answer covering the common bases
    return {
        "kind": "text",
        "text": ("Here's a quick take on that:\n\n"
                 "Quantum computing harnesses superposition, entanglement and interference to process "
                 "information in ways classical computers cannot. The best way to build intuition is "
                 "hands-on — try loading a template in the Circuit Lab (e.g. Bell or Grover) and "
                 "watch the probabilities and Bloch spheres update.\n\n"
                 "I can explain any concept in detail, analyze your circuit, or generate code. "
                 "Ask me to 'explain entanglement' or 'analyze my circuit'."),
        "suggestions": ["Explain superposition", "Analyze my circuit", "What should I learn next?"],
    }
