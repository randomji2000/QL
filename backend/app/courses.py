"""Structured learning modules for the platform."""

MODULES = [
    {
        "id": "module-1",
        "title": "Quantum Fundamentals",
        "level": "Beginner",
        "description": "Qubits, superposition, measurement and the Bloch sphere — the foundation of all quantum computing.",
        "icon": "atom",
        "lessons": [
            {
                "id": "l1-1",
                "title": "What is a Qubit?",
                "duration": "10 min",
                "concept": "qubit",
                "content": [
                    {"type": "p", "text": "A classical bit is either 0 or 1. A qubit is a two-level quantum system described by "
                                          "|ψ⟩ = α|0⟩ + β|1⟩, where α and β are complex numbers with |α|² + |β|² = 1."},
                    {"type": "p", "text": "The state can be any point on the unit sphere (the Bloch sphere). The north pole is |0⟩, "
                                          "the south pole is |1⟩, and everywhere else is a superposition."},
                    {"type": "code", "title": "Visualize a qubit", "circuit": "bell"},
                    {"type": "p", "text": "Measurement collapses the qubit to |0⟩ with probability |α|² or |1⟩ with probability |β|². "
                                          "You cannot read a superposition directly."},
                ],
            },
            {
                "id": "l1-2",
                "title": "Superposition & the Hadamard Gate",
                "duration": "12 min",
                "concept": "superposition",
                "content": [
                    {"type": "p", "text": "The Hadamard gate H is the quintessential superposition gate: H|0⟩ = (|0⟩ + |1⟩)/√2 and "
                                          "H|1⟩ = (|0⟩ − |1⟩)/√2."},
                    {"type": "p", "text": "Because H is self-inverse, H·H = I: applying it twice returns the original state. "
                                          "Try it in the circuit lab and watch the Bloch vector move."},
                    {"type": "code", "title": "Try: H then H", "circuit": {"num_qubits": 1, "gates": [{"gate": "h", "target": 0}]}},
                    {"type": "p", "text": "The equal superposition (|0⟩+|1⟩)/√2 sits on the equator of the Bloch sphere and yields "
                                          "50/50 measurement outcomes."},
                ],
            },
            {
                "id": "l1-3",
                "title": "Measurement & Probability",
                "duration": "8 min",
                "concept": "measurement",
                "content": [
                    {"type": "p", "text": "Measurement is probabilistic and destructive. Given |ψ⟩ = α|0⟩ + β|1⟩, measuring "
                                          "returns 0 with probability |α|² and collapses the state to |0⟩."},
                    {"type": "p", "text": "With N shots, the empirical histogram of outcomes approximates the true probabilities. "
                                          "More shots = better statistics."},
                    {"type": "code", "title": "Measure a superposition", "circuit": {"num_qubits": 1, "gates": [{"gate": "h", "target": 0}]}},
                ],
            },
        ],
    },
    {
        "id": "module-2",
        "title": "Entanglement & Multi-Qubit Gates",
        "level": "Beginner",
        "description": "CNOT, Bell states and the correlations that make quantum computing powerful.",
        "icon": "link",
        "lessons": [
            {
                "id": "l2-1",
                "title": "The CNOT Gate",
                "duration": "12 min",
                "concept": "cnot",
                "content": [
                    {"type": "p", "text": "CNOT has a control and a target. If the control is |1⟩, the target is flipped; "
                                          "otherwise nothing happens. It is reversible and its own inverse."},
                    {"type": "code", "title": "CNOT on |10⟩", "circuit": {"num_qubits": 2, "gates": [
                        {"gate": "x", "target": 0}, {"gate": "cx", "controls": [0], "target": 1}]}},
                    {"type": "p", "text": "When the control is in superposition, CNOT creates entanglement: the two qubits "
                                          "become correlated in a way impossible classically."},
                ],
            },
            {
                "id": "l2-2",
                "title": "Bell States & Entanglement",
                "duration": "12 min",
                "concept": "entanglement",
                "content": [
                    {"type": "p", "text": "H then CNOT produces the Bell state (|00⟩ + |11⟩)/√2. Both qubits are individually "
                                          "random, yet perfectly correlated: measuring one determines the other."},
                    {"type": "code", "title": "Create a Bell pair", "circuit": "bell"},
                    {"type": "p", "text": "Run the circuit and inspect the entanglement entropy (1.0 = maximally entangled) and "
                                          "the correlated counts."},
                ],
            },
            {
                "id": "l2-3",
                "title": "GHZ & W States",
                "duration": "14 min",
                "concept": "multi-qubit",
                "content": [
                    {"type": "p", "text": "The GHZ state (|000⟩ + |111⟩)/√2 extends entanglement to three qubits: all qubits "
                                          "collapse together to 000 or 111."},
                    {"type": "code", "title": "GHZ state", "circuit": "ghz"},
                    {"type": "p", "text": "The W state (|100⟩ + |010⟩ + |001⟩)/√3 is a different, inequivalent kind of "
                                          "three-qubit entanglement where exactly one qubit is |1⟩."},
                    {"type": "code", "title": "W state", "circuit": "w-state"},
                ],
            },
        ],
    },
    {
        "id": "module-3",
        "title": "Quantum Gates in Depth",
        "level": "Intermediate",
        "description": "Phase gates, rotations, Toffoli, SWAP and building universal gate sets.",
        "icon": "gate",
        "lessons": [
            {
                "id": "l3-1",
                "title": "Phase & Rotation Gates",
                "duration": "12 min",
                "concept": "phase",
                "content": [
                    {"type": "p", "text": "Phase gates (S, T, P, Rz) rotate the state around the Z axis of the Bloch sphere, "
                                          "changing relative phase but not measurement probabilities."},
                    {"type": "p", "text": "S = 90° phase, T = 45°. Together with H and CNOT they are universal for quantum computing."},
                    {"type": "code", "title": "Phase rotations", "circuit": {"num_qubits": 1, "gates": [
                        {"gate": "h", "target": 0}, {"gate": "p", "target": 0, "params": [1.5708]}]}},
                ],
            },
            {
                "id": "l3-2",
                "title": "Toffoli & SWAP Gates",
                "duration": "10 min",
                "concept": "multi-qubit",
                "content": [
                    {"type": "p", "text": "The Toffoli (CCX) gate flips the target only when both controls are |1⟩. It is "
                                          "universal for classical reversible computation."},
                    {"type": "code", "title": "SWAP via CNOTs", "circuit": "swap"},
                    {"type": "p", "text": "A SWAP can be built from three CNOTs: CNOT(a,b), CNOT(b,a), CNOT(a,b)."},
                ],
            },
        ],
    },
    {
        "id": "module-4",
        "title": "Core Quantum Algorithms",
        "level": "Intermediate",
        "description": "Deutsch–Jozsa, Bernstein–Vazirani, QFT, Grover and superdense coding.",
        "icon": "algorithm",
        "lessons": [
            {
                "id": "l4-1",
                "title": "Deutsch–Jozsa Algorithm",
                "duration": "15 min",
                "concept": "deutsch-jozsa",
                "content": [
                    {"type": "p", "text": "Classically, distinguishing a constant from a balanced function needs up to 2^(n−1)+1 "
                                          "queries. Quantumly, one evaluation suffices."},
                    {"type": "code", "title": "Deutsch–Jozsa (balanced oracle)", "circuit": "deutsch-jozsa"},
                    {"type": "p", "text": "The input register reads a non-zero value iff the function is balanced."},
                ],
            },
            {
                "id": "l4-2",
                "title": "Bernstein–Vazirani Algorithm",
                "duration": "12 min",
                "concept": "bernstein-vazirani",
                "content": [
                    {"type": "p", "text": "Recover the hidden string s from the oracle f(x) = s·x in a single query. "
                                          "The circuit encodes s in the CNOT controls."},
                    {"type": "code", "title": "Recover s = 101", "circuit": "bernstein-vazirani"},
                ],
            },
            {
                "id": "l4-3",
                "title": "Quantum Fourier Transform",
                "duration": "15 min",
                "concept": "qft",
                "content": [
                    {"type": "p", "text": "The QFT maps |x⟩ → Σ e^(2πi x k / 2^n)|k⟩. It is the building block of phase "
                                          "estimation, period finding, and Shor's algorithm."},
                    {"type": "code", "title": "3-qubit QFT", "circuit": "qft-3"},
                ],
            },
            {
                "id": "l4-4",
                "title": "Grover's Search",
                "duration": "15 min",
                "concept": "grover",
                "content": [
                    {"type": "p", "text": "Grover's algorithm searches an unstructured database of N items in O(√N) queries via "
                                          "amplitude amplification: oracle + diffusion, repeated."},
                    {"type": "code", "title": "Grover (2 qubits, mark |11⟩)", "circuit": "grover-2"},
                ],
            },
            {
                "id": "l4-5",
                "title": "Superdense Coding",
                "duration": "10 min",
                "concept": "entanglement",
                "content": [
                    {"type": "p", "text": "With a pre-shared Bell pair, Alice sends 2 classical bits by manipulating only 1 qubit "
                                          "(X, Z, or both). Bob decodes by measuring in the Bell basis."},
                    {"type": "code", "title": "Send 11", "circuit": "superdense-coding"},
                ],
            },
        ],
    },
    {
        "id": "module-5",
        "title": "Advanced Algorithms",
        "level": "Advanced",
        "description": "Phase estimation, quantum teleportation and the physics of noise.",
        "icon": "rocket",
        "lessons": [
            {
                "id": "l5-1",
                "title": "Quantum Phase Estimation",
                "duration": "18 min",
                "concept": "phase-estimation",
                "content": [
                    {"type": "p", "text": "QPE estimates the eigenvalue phase of a unitary U. It combines superposition, "
                                          "controlled powers of U, and the inverse QFT."},
                    {"type": "code", "title": "QPE for θ = 1/4", "circuit": "qpe-2"},
                ],
            },
            {
                "id": "l5-2",
                "title": "Quantum Teleportation",
                "duration": "18 min",
                "concept": "teleportation",
                "content": [
                    {"type": "p", "text": "Teleportation moves an unknown quantum state using entanglement plus two classical "
                                          "bits — without transferring any physical particle."},
                    {"type": "code", "title": "Teleport Ry(1.0)|0⟩", "circuit": "teleportation"},
                    {"type": "p", "text": "Notice the classically-conditioned X and Z gates applied after the Bell measurement — "
                                          "this feed-forward is the 'classical' half of teleportation."},
                ],
            },
            {
                "id": "l5-3",
                "title": "Noise & Decoherence",
                "duration": "12 min",
                "concept": "decoherence",
                "content": [
                    {"type": "p", "text": "Real qubits decohere: superposition and entanglement decay through interaction with "
                                          "the environment. Error correction is required for fault tolerance."},
                    {"type": "p", "text": "In this simulator you can compare ideal results (statevector) against sampled "
                                          "outcomes to build intuition for statistical noise."},
                ],
            },
        ],
    },
]


def list_modules():
    return [{
        "id": m["id"], "title": m["title"], "level": m["level"],
        "description": m["description"], "icon": m["icon"],
        "lesson_count": len(m["lessons"]),
    } for m in MODULES]


def get_module(mid):
    for m in MODULES:
        if m["id"] == mid:
            return m
    return None
