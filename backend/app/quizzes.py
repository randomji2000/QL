"""Assessment quizzes with auto-grading."""

QUIZZES = [
    {
        "id": "quiz-1",
        "title": "Quantum Fundamentals",
        "module": "module-1",
        "level": "Beginner",
        "questions": [
            {
                "id": "q1-1",
                "text": "Which of the following best describes a qubit?",
                "options": [
                    "A two-level system that can be in a superposition of |0⟩ and |1⟩",
                    "A binary digit that is always 0 or 1",
                    "A probabilistic classical bit",
                    "A physical object that stores only |1⟩",
                ],
                "answer": 0,
                "explanation": "A qubit is a two-level quantum system |ψ⟩ = α|0⟩ + β|1⟩ that can exist in superposition.",
            },
            {
                "id": "q1-2",
                "text": "What is the probability of measuring |1⟩ for the state |ψ⟩ = (|0⟩ + |1⟩)/√2?",
                "options": ["0", "0.25", "0.5", "1"],
                "answer": 2,
                "explanation": "The coefficient of |1⟩ is 1/√2, so probability = |1/√2|² = 1/2.",
            },
            {
                "id": "q1-3",
                "text": "Applying the Hadamard gate twice in a row (H·H) to a qubit gives:",
                "options": ["The zero state |0⟩", "The original state (H is self-inverse)", "|1⟩ with certainty", "A maximally entangled state"],
                "answer": 1,
                "explanation": "H is its own inverse: H·H = I, so the qubit returns to its original state.",
            },
            {
                "id": "q1-4",
                "text": "What does a measurement do to a superposition state?",
                "options": [
                    "It amplifies the amplitudes",
                    "It collapses the state to one basis state with some probability",
                    "It leaves the state untouched",
                    "It always returns |0⟩",
                ],
                "answer": 1,
                "explanation": "Measurement projects onto the computational basis and destroys the superposition.",
            },
            {
                "id": "q1-5",
                "text": "The Bloch sphere represents a single-qubit state as:",
                "options": [
                    "A point on the surface of a unit sphere",
                    "A line segment between 0 and 1",
                    "A probability distribution",
                    "A complex number",
                ],
                "answer": 0,
                "explanation": "Every pure single-qubit state maps to a unique point on the unit sphere.",
            },
        ],
    },
    {
        "id": "quiz-2",
        "title": "Entanglement & Multi-Qubit Systems",
        "module": "module-2",
        "level": "Beginner",
        "questions": [
            {
                "id": "q2-1",
                "text": "What does a CNOT gate do?",
                "options": [
                    "Flips the target qubit only when the control is |1⟩",
                    "Flips both qubits always",
                    "Creates superposition on both qubits",
                    "Measures both qubits",
                ],
                "answer": 0,
                "explanation": "CNOT applies X to the target conditioned on the control being |1⟩.",
            },
            {
                "id": "q2-2",
                "text": "Which circuit produces the Bell state (|00⟩ + |11⟩)/√2 from |00⟩?",
                "options": [
                    "X on both qubits",
                    "H on q0 then CNOT(q0 → q1)",
                    "H on both qubits",
                    "CNOT(q0 → q1) then H on q1",
                ],
                "answer": 1,
                "explanation": "H puts q0 in superposition, then CNOT entangles it with q1.",
            },
            {
                "id": "q2-3",
                "text": "For the Bell state (|00⟩ + |11⟩)/√2, what happens when you measure q0 and find |1⟩?",
                "options": [
                    "q1 is |0⟩ with 50% probability",
                    "q1 is guaranteed |1⟩",
                    "q1 is guaranteed |0⟩",
                    "The state becomes unentangled with equal probability",
                ],
                "answer": 1,
                "explanation": "Perfect correlation: if q0 collapses to |1⟩, q1 must also be |1⟩.",
            },
            {
                "id": "q2-4",
                "text": "The entanglement entropy of a maximally entangled qubit pair (Bell state) is:",
                "options": ["0", "0.5", "1", "2"],
                "answer": 2,
                "explanation": "The reduced density matrix of each qubit is maximally mixed with von Neumann entropy = 1 bit.",
            },
            {
                "id": "q2-5",
                "text": "Which state has exactly one qubit equal to |1⟩, uniformly distributed?",
                "options": ["GHZ state", "W state", "Bell state", "Product state"],
                "answer": 1,
                "explanation": "The W state is (|100⟩ + |010⟩ + |001⟩)/√3 — a single excitation shared among three qubits.",
            },
        ],
    },
    {
        "id": "quiz-3",
        "title": "Quantum Algorithms",
        "module": "module-4",
        "level": "Intermediate",
        "questions": [
            {
                "id": "q3-1",
                "text": "How many oracle queries does the Deutsch–Jozsa algorithm need to classify a function as constant or balanced?",
                "options": ["One", "Two", "n", "2^n"],
                "answer": 0,
                "explanation": "A single quantum query suffices, versus up to 2^(n−1)+1 classically.",
            },
            {
                "id": "q3-2",
                "text": "In Grover's algorithm, the oracle:",
                "options": [
                    "Flips the phase of the marked state(s)",
                    "Measures the database",
                    "Sorts the items",
                    "Encodes all answers classically",
                ],
                "answer": 0,
                "explanation": "The oracle applies a phase flip (typically −1) to the marked basis state(s).",
            },
            {
                "id": "q3-3",
                "text": "The Quantum Fourier Transform is a core subroutine of:",
                "options": [
                    "Quantum Phase Estimation",
                    "Teleportation",
                    "Bell state preparation",
                    "Superdense coding",
                ],
                "answer": 0,
                "explanation": "QPE uses the inverse QFT to read out the phase stored in a register.",
            },
            {
                "id": "q3-4",
                "text": "Quantum teleportation transmits:",
                "options": [
                    "An unknown quantum state using entanglement + 2 classical bits",
                    "Two classical bits using one qubit",
                    "Energy over distance",
                    "The Bell state itself",
                ],
                "answer": 0,
                "explanation": "Teleportation transfers an unknown state via a shared Bell pair and two classical bits (LOCC).",
            },
            {
                "id": "q3-5",
                "text": "Superdense coding sends:",
                "options": [
                    "2 classical bits using 1 qubit + shared entanglement",
                    "1 qubit using 2 classical bits",
                    "A quantum state without entanglement",
                    "Infinite information",
                ],
                "answer": 0,
                "explanation": "With a pre-shared Bell pair, one qubit carries two bits of classical information.",
            },
        ],
    },
]


def list_quizzes():
    return [{"id": q["id"], "title": q["title"], "module": q["module"], "level": q["level"],
             "question_count": len(q["questions"])} for q in QUIZZES]


def get_quiz(qid):
    for q in QUIZZES:
        if q["id"] == qid:
            return q
    return None


def grade_quiz(qid, answers):
    """answers: list of selected option indices, in question order."""
    quiz = get_quiz(qid)
    if quiz is None:
        return None
    questions = quiz["questions"]
    if len(answers) != len(questions):
        return {"error": f"expected {len(questions)} answers, got {len(answers)}"}
    correct = 0
    results = []
    for i, q in enumerate(questions):
        ok = int(answers[i]) == q["answer"]
        correct += 1 if ok else 0
        results.append({
            "question": q["text"],
            "selected": answers[i],
            "correct_index": q["answer"],
            "is_correct": ok,
            "explanation": q["explanation"],
        })
    score = round(100.0 * correct / len(questions), 1)
    return {"quiz_id": qid, "total": len(questions), "correct": correct,
            "score": score, "passed": score >= 70, "results": results}
