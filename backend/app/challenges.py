"""Coding challenges with automated checks.

Each challenge ships starter code, a full solution, and a set of test
assertions that are executed against the user's submitted code in a
sandboxed subprocess.
"""

CHALLENGES = [
    {
        "id": "ch-1",
        "title": "Build a Bell State",
        "module": "module-2",
        "level": "Beginner",
        "concept": "entanglement",
        "description": "Write a function that returns a Qiskit QuantumCircuit on 2 qubits "
                       "preparing the Bell state (|00> + |11>)/sqrt(2).",
        "starter": "from qiskit import QuantumCircuit\n\n\ndef bell_state() -> QuantumCircuit:\n    qc = QuantumCircuit(2, 2)\n    # TODO: create the Bell state (|00> + |11>)/sqrt(2)\n    # Hint: H then CNOT\n    return qc\n",
        "solution": "from qiskit import QuantumCircuit\n\n\ndef bell_state() -> QuantumCircuit:\n    qc = QuantumCircuit(2, 2)\n    qc.h(0)\n    qc.cx(0, 1)\n    return qc\n",
        "tests": [
            "from qiskit import QuantumCircuit, transpile\nfrom qiskit_aer import AerSimulator\nqc = bell_state()\nassert isinstance(qc, QuantumCircuit)\nsim = AerSimulator(method='statevector')\nq = qc.copy(); q.save_statevector()\nsv = sim.run(q).result().get_statevector(q)\namp = {}\nfor i, a in enumerate(sv):\n    label = format(i, '02b')[::-1]\n    if abs(a) > 1e-9:\n        amp[label] = a\nassert set(amp.keys()) == {'00', '11'}, f'expected |00> and |11>, got {amp}'\nfor k, a in amp.items():\n    assert abs(abs(a)**2 - 0.5) < 1e-6, f'probability of {k} should be 0.5'\n",
        ],
    },
    {
        "id": "ch-2",
        "title": "Superposition Coin Flip",
        "module": "module-1",
        "level": "Beginner",
        "concept": "superposition",
        "description": "Write a function that applies a Hadamard gate to a single qubit and "
                       "returns the resulting 2-component amplitude vector using the built-in "
                       "QStudio simulator.",
        "starter": "import numpy as np\n\n\ndef hadamard_state() -> np.ndarray:\n    # Return the vector H|0> as a numpy array.\n    # H = (1/sqrt2) * [[1, 1], [1, -1]]\n    return np.zeros(2, dtype=complex)\n",
        "solution": "import numpy as np\n\n\ndef hadamard_state() -> np.ndarray:\n    H = (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)\n    return H @ np.array([1, 0], dtype=complex)\n",
        "tests": [
            "import numpy as np\nv = hadamard_state()\nassert v.shape == (2,)\nexpected = np.array([1, 1], dtype=complex) / np.sqrt(2)\nassert np.allclose(np.abs(v), np.abs(expected)), f'got {v}'\n",
        ],
    },
    {
        "id": "ch-3",
        "title": "Two-Qubit GHZ State",
        "module": "module-2",
        "level": "Beginner",
        "concept": "multi-qubit",
        "description": "Return a Qiskit circuit that prepares the GHZ state on the given "
                       "number of qubits: (|0...0> + |1...1>)/sqrt(2).",
        "starter": "from qiskit import QuantumCircuit\n\n\ndef ghz_state(n: int = 3) -> QuantumCircuit:\n    qc = QuantumCircuit(n, n)\n    # TODO: H on q0, then CNOT chain q0->q1->q2->...\n    return qc\n",
        "solution": "from qiskit import QuantumCircuit\n\n\ndef ghz_state(n: int = 3) -> QuantumCircuit:\n    qc = QuantumCircuit(n, n)\n    qc.h(0)\n    for i in range(n - 1):\n        qc.cx(i, i + 1)\n    return qc\n",
        "tests": [
            "from qiskit import QuantumCircuit\nfrom qiskit_aer import AerSimulator\nqc = ghz_state(3)\nsim = AerSimulator(method='statevector')\nq = qc.copy(); q.save_statevector()\nsv = sim.run(q).result().get_statevector(q)\namp = {}\nfor i, a in enumerate(sv):\n    label = format(i, '03b')[::-1]\n    if abs(a) > 1e-9:\n        amp[label] = a\nassert set(amp.keys()) == {'000', '111'}, f'expected 000 and 111, got {amp}'\n",
        ],
    },
    {
        "id": "ch-4",
        "title": "Grover's 2-Qubit Search",
        "module": "module-4",
        "level": "Intermediate",
        "concept": "grover",
        "description": "Complete the Grover search circuit that finds the marked state |11> "
                       "on 2 qubits. The oracle and diffusion halves are stubbed.",
        "starter": "from qiskit import QuantumCircuit\n\n\ndef grover_search() -> QuantumCircuit:\n    qc = QuantumCircuit(2, 2)\n    # Superpose\n    qc.h([0, 1])\n    # Oracle: phase flip on |11> (use cz)\n    # TODO: qc.cz(0, 1)\n    # Diffusion\n    # TODO: H X cz X H\n    return qc\n",
        "solution": "from qiskit import QuantumCircuit\n\n\ndef grover_search() -> QuantumCircuit:\n    qc = QuantumCircuit(2, 2)\n    qc.h([0, 1])\n    qc.cz(0, 1)\n    qc.h([0, 1])\n    qc.x([0, 1])\n    qc.cz(0, 1)\n    qc.x([0, 1])\n    qc.h([0, 1])\n    return qc\n",
        "tests": [
            "from qiskit import QuantumCircuit\nfrom qiskit_aer import AerSimulator\nqc = grover_search()\nqc.measure_all()\nsim = AerSimulator(method='statevector')\ncounts = sim.run(qc, shots=2000).result().get_counts()\nmost = max(counts, key=counts.get)\n# key order: q0q1 -> most should end with '11'\nassert most.endswith('11') or most == '11', f'expected |11> to dominate, got {most}: {counts}'\n",
        ],
    },
]


def list_challenges():
    return [{"id": c["id"], "title": c["title"], "module": c["module"], "level": c["level"],
             "concept": c["concept"], "description": c["description"]} for c in CHALLENGES]


def get_challenge(cid):
    for c in CHALLENGES:
        if c["id"] == cid:
            return c
    return None


def check_challenge(cid, code):
    """Evaluate user code against the challenge's tests."""
    challenge = get_challenge(cid)
    if challenge is None:
        return {"error": f"unknown challenge {cid}"}
    user_code = code or ""
    full = user_code + "\n\n# ---- challenge tests ----\n" + "\n".join(challenge["tests"])
    return full
