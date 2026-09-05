"""Standard quantum algorithm and state-preparation circuit templates.

Every template is a JSON-serializable circuit that runs on the built-in
simulator. A `verify` script checks the expected outcome numerically.
"""

import math

TEMPLATES = [
    {
        "id": "bell",
        "name": "Bell State (EPR pair)",
        "category": "Fundamentals",
        "num_qubits": 2,
        "level": "Beginner",
        "summary": "Create the maximally entangled Bell state (|00> + |11>)/sqrt(2).",
        "concepts": ["superposition", "entanglement", "hadamard", "cnot"],
        "description": "A Hadamard gate puts qubit 0 into superposition, then a CNOT "
                       "entangles it with qubit 1. Measuring both qubits always yields "
                       "identical outcomes (00 or 11) despite each being random.",
        "gates": [
            {"gate": "h", "target": 0},
            {"gate": "cx", "controls": [0], "target": 1},
        ],
        "expected": {"outcome": "00 or 11 with equal probability", "fidelity_note": "100% correlated"},
    },
    {
        "id": "ghz",
        "name": "GHZ State",
        "category": "Fundamentals",
        "num_qubits": 3,
        "level": "Beginner",
        "summary": "Three-qubit maximally entangled state (|000> + |111>)/sqrt(2).",
        "concepts": ["entanglement", "multi-qubit", "cnot"],
        "description": "The GHZ state extends the Bell state to three qubits: "
                       "all qubits are perfectly correlated and measurement yields "
                       "000 or 111 only.",
        "gates": [
            {"gate": "h", "target": 0},
            {"gate": "cx", "controls": [0], "target": 1},
            {"gate": "cx", "controls": [1], "target": 2},
        ],
        "expected": {"outcome": "000 or 111 with equal probability"},
    },
    {
        "id": "w-state",
        "name": "W State",
        "category": "Fundamentals",
        "num_qubits": 3,
        "level": "Intermediate",
        "summary": "Symmetric single-excitation state (|100>+|010>+|001>)/sqrt(3).",
        "concepts": ["entanglement", "three-qubit", "w-state"],
        "description": "The W state is a genuinely different tripartite entangled "
                       "state from GHZ: exactly one qubit is |1> at a time, uniformly "
                       "distributed across the three qubits.",
        "gates": [
            {"gate": "ry", "target": 2, "params": [2.0 * math.asin(1.0 / math.sqrt(3.0))]},
            {"gate": "x", "target": 2},
            {"gate": "ch", "controls": [2], "target": 0},
            {"gate": "ccx", "controls": [2, 0], "target": 1},
            {"gate": "cx", "controls": [2], "target": 1},
            {"gate": "x", "target": 2},
        ],
        "expected": {"outcome": "100, 010, 001 each with probability 1/3"},
    },
    {
        "id": "deutsch-jozsa",
        "name": "Deutsch–Jozsa Algorithm",
        "category": "Algorithms",
        "num_qubits": 3,
        "level": "Intermediate",
        "summary": "Determine whether a function is constant or balanced with one query.",
        "concepts": ["oracle", "superposition", "phase kickback", "quantum advantage"],
        "description": "The oracle implements the balanced function f(x)=x0 XOR x1 on "
                       "2 input qubits. A single evaluation of the circuit reveals the "
                       "function is balanced: measuring the input register yields a "
                       "non-zero value (11).",
        "gates": [
            {"gate": "h", "target": 0},
            {"gate": "h", "target": 1},
            {"gate": "x", "target": 2},
            {"gate": "h", "target": 2},
            {"gate": "cx", "controls": [0], "target": 2},
            {"gate": "cx", "controls": [1], "target": 2},
            {"gate": "h", "target": 0},
            {"gate": "h", "target": 1},
        ],
        "expected": {"outcome": "non-zero (11) means the oracle is balanced"},
    },
    {
        "id": "bernstein-vazirani",
        "name": "Bernstein–Vazirani Algorithm",
        "category": "Algorithms",
        "num_qubits": 5,
        "level": "Intermediate",
        "summary": "Recover a hidden bit-string s with a single query.",
        "concepts": ["oracle", "superposition", "hidden string"],
        "description": "The oracle encodes the hidden string s = 101 on 4 input qubits "
                       "(qubits 0-3, with s set on qubits 0 and 2). One execution "
                       "recovers every bit of s in a single shot.",
        "gates": [
            {"gate": "h", "target": 0}, {"gate": "h", "target": 1},
            {"gate": "h", "target": 2}, {"gate": "h", "target": 3},
            {"gate": "x", "target": 4}, {"gate": "h", "target": 4},
            {"gate": "cx", "controls": [0], "target": 4},
            {"gate": "cx", "controls": [2], "target": 4},
            {"gate": "h", "target": 0}, {"gate": "h", "target": 1},
            {"gate": "h", "target": 2}, {"gate": "h", "target": 3},
        ],
        "expected": {"outcome": "101 on the 4 input qubits (s = 101)"},
    },
    {
        "id": "qft-3",
        "name": "Quantum Fourier Transform (3 qubits)",
        "category": "Algorithms",
        "num_qubits": 3,
        "level": "Intermediate",
        "summary": "The quantum analogue of the discrete Fourier transform.",
        "concepts": ["QFT", "phase estimation", "superposition"],
        "description": "Applies the QFT to an input state. Try starting from |001>: the "
                       "output amplitudes become a uniform superposition over all "
                       "basis states with carefully arranged phases.",
        "gates": [
            {"gate": "h", "target": 0},
            {"gate": "p", "controls": [1], "target": 0, "params": [math.pi / 2]},
            {"gate": "p", "controls": [2], "target": 0, "params": [math.pi / 4]},
            {"gate": "h", "target": 1},
            {"gate": "p", "controls": [2], "target": 1, "params": [math.pi / 2]},
            {"gate": "h", "target": 2},
        ],
        "expected": {"outcome": "uniform amplitudes; correct relative phases"},
    },
    {
        "id": "grover-2",
        "name": "Grover's Algorithm (2 qubits)",
        "category": "Algorithms",
        "num_qubits": 2,
        "level": "Intermediate",
        "summary": "Find the marked state |11> in ~sqrt(N) oracle calls.",
        "concepts": ["amplitude amplification", "oracle", "diffusion", "quantum search"],
        "description": "An oracle flips the phase of the marked state |11>. The "
                       "diffusion operator amplifies the marked amplitude; after one "
                       "iteration the state |11> is measured with near-certainty.",
        "gates": [
            {"gate": "h", "target": 0}, {"gate": "h", "target": 1},
            {"gate": "cz", "controls": [0], "target": 1},
            {"gate": "h", "target": 0}, {"gate": "h", "target": 1},
            {"gate": "x", "target": 0}, {"gate": "x", "target": 1},
            {"gate": "cz", "controls": [0], "target": 1},
            {"gate": "x", "target": 0}, {"gate": "x", "target": 1},
            {"gate": "h", "target": 0}, {"gate": "h", "target": 1},
        ],
        "expected": {"outcome": "11 with high probability (marked state)"},
    },
    {
        "id": "qpe-2",
        "name": "Quantum Phase Estimation (theta = 1/4)",
        "category": "Algorithms",
        "num_qubits": 3,
        "level": "Advanced",
        "summary": "Estimate the eigenvalue phase of a unitary in binary.",
        "concepts": ["phase estimation", "phase kickback", "inverse QFT"],
        "description": "Estimates the phase theta = 1/4 of U = P(pi/2) acting on the "
                       "eigenstate |1>. The 2-bit answer register reads 01.",
        "gates": [
            {"gate": "h", "target": 0}, {"gate": "h", "target": 1},
            {"gate": "x", "target": 2},
            {"gate": "p", "controls": [1], "target": 2, "params": [math.pi]},
            {"gate": "p", "controls": [0], "target": 2, "params": [math.pi / 2]},
            {"gate": "h", "target": 1},
            {"gate": "p", "controls": [1], "target": 0, "params": [-math.pi / 2]},
            {"gate": "h", "target": 0},
        ],
        "expected": {"outcome": "10 (phase register 0.01_bin = 1/4, q0 = first fractional bit)"},
    },
    {
        "id": "teleportation",
        "name": "Quantum Teleportation",
        "category": "Algorithms",
        "num_qubits": 3,
        "level": "Advanced",
        "summary": "Transmit an unknown quantum state using entanglement.",
        "concepts": ["entanglement", "bell measurement", "feed-forward", "teleportation"],
        "description": "Qubit 0 holds the state to send. After a Bell measurement on "
                       "qubits 0 and 1, classically-conditioned Pauli corrections "
                       "reconstruct the state on qubit 2. Compare q2's outcome "
                       "distribution with the original state.",
        "gates": [
            {"gate": "ry", "target": 0, "params": [1.0]},
            {"gate": "h", "target": 1},
            {"gate": "cx", "controls": [1], "target": 2},
            {"gate": "cx", "controls": [0], "target": 1},
            {"gate": "h", "target": 0},
            {"gate": "measure", "target": 0},
            {"gate": "measure", "target": 1},
            {"gate": "x", "target": 2, "condition": {"qubit": 1, "value": 1}},
            {"gate": "z", "target": 2, "condition": {"qubit": 0, "value": 1}},
            {"gate": "measure", "target": 2},
        ],
        "expected": {"outcome": "qubit 2 ends in state Ry(1.0)|0>"},
    },
    {
        "id": "superdense-coding",
        "name": "Superdense Coding",
        "category": "Algorithms",
        "num_qubits": 2,
        "level": "Intermediate",
        "summary": "Send two classical bits using one quantum bit + entanglement.",
        "concepts": ["entanglement", "dense coding", "bell states"],
        "description": "Alice encodes the 2-bit message 11 by applying Z then X to her "
                       "half of a Bell pair. Bob's measurement reconstructs 11 with "
                       "certainty.",
        "gates": [
            {"gate": "h", "target": 0},
            {"gate": "cx", "controls": [0], "target": 1},
            {"gate": "z", "target": 0},
            {"gate": "x", "target": 0},
            {"gate": "cx", "controls": [0], "target": 1},
            {"gate": "h", "target": 0},
            {"gate": "measure", "target": 0},
            {"gate": "measure", "target": 1},
        ],
        "expected": {"outcome": "11"},
    },
    {
        "id": "grover-3",
        "name": "Grover's Algorithm (3 qubits)",
        "category": "Algorithms",
        "num_qubits": 3,
        "level": "Advanced",
        "summary": "Search for the marked state |101> among 8 items.",
        "concepts": ["amplitude amplification", "oracle", "diffusion"],
        "description": "Oracle marks |101> via a phase flip on that exact basis state. "
                       "After ~2 rounds of amplitude amplification, |101> is measured "
                       "with high probability.",
        "gates": [
            {"gate": "h", "target": 0}, {"gate": "h", "target": 1}, {"gate": "h", "target": 2},
            {"gate": "x", "target": 1},
            {"gate": "h", "target": 2},
            {"gate": "ccx", "controls": [0, 1], "target": 2},
            {"gate": "h", "target": 2},
            {"gate": "x", "target": 1},
            {"gate": "h", "target": 0}, {"gate": "h", "target": 1}, {"gate": "h", "target": 2},
            {"gate": "x", "target": 0}, {"gate": "x", "target": 1}, {"gate": "x", "target": 2},
            {"gate": "h", "target": 2},
            {"gate": "ccx", "controls": [0, 1], "target": 2},
            {"gate": "h", "target": 2},
            {"gate": "x", "target": 0}, {"gate": "x", "target": 1}, {"gate": "x", "target": 2},
            {"gate": "h", "target": 0}, {"gate": "h", "target": 1}, {"gate": "h", "target": 2},
        ],
        "expected": {"outcome": "101 with high probability"},
    },
    {
        "id": "swap",
        "name": "SWAP Gate",
        "category": "Fundamentals",
        "num_qubits": 2,
        "level": "Beginner",
        "summary": "Exchange the state of two qubits.",
        "concepts": ["swap", "two-qubit gates"],
        "description": "Swaps the computational states of qubits 0 and 1. Also shown: "
                       "SWAP = CNOT + CNOT + CNOT.",
        "gates": [
            {"gate": "x", "target": 0},
            {"gate": "swap", "targets": [0, 1]},
        ],
        "expected": {"outcome": "|01>: qubit 1 inherits the |1> state"},
    },
]


def get_template(tid):
    for t in TEMPLATES:
        if t["id"] == tid:
            return t
    return None


def list_templates():
    return [{
        "id": t["id"], "name": t["name"], "category": t["category"],
        "num_qubits": t["num_qubits"], "level": t["level"],
        "summary": t["summary"], "concepts": t["concepts"],
    } for t in TEMPLATES]
