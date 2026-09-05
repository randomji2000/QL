"""Deterministic circuit-analysis engine used by the AI tutor.

Produces:
  * structural facts (depth, gate counts, used/unused qubits)
  * error / warning diagnostics
  * redundancy & optimization suggestions
  * identification of well-known circuit patterns
"""

import math

from .quantum.simulator import circuit_stats, normalize_circuit
from .templates import get_template

_SINGLE = {"h", "x", "y", "z", "s", "sdg", "t", "tdg", "p", "u1", "u2", "u3",
           "rx", "ry", "rz", "reset"}


def _twin_redundant(a, b):
    """Return (redundant_bool, simplified_label) for two adjacent single-qubit gates."""
    if a["gate"] != b["gate"]:
        return False, None
    g = a["gate"]
    if g in ("h", "x", "y", "z"):
        return True, f"the two {g.upper()} gates cancel (identity)"
    if g in ("s", "sdg"):
        return False, None
    if g == "t":
        return False, None
    if g in ("rx", "ry", "rz", "p"):
        pa = (a["params"] or [0])[0]
        pb = (b["params"] or [0])[0]
        if abs(pa + pb) < 1e-9:
            return True, f"{g.upper()} with opposite angles cancel"
        return False, None
    return False, None


def _pattern_heuristics(ops, n):
    """Try to identify the circuit as a known construction."""
    counts = {}
    for o in ops:
        counts[o["gate"]] = counts.get(o["gate"], 0) + 1
    seq = []
    for o in ops:
        if o["gate"] not in ("measure", "barrier"):
            seq.append((o["gate"], tuple(o["controls"]), tuple(o["targets"])))
    # Bell / EPR
    if n == 2 and seq == [("h", (), (0,)), ("cx", (0,), (1,))]:
        return {"id": "bell", "name": "Bell State preparation",
                "detail": "H then CNOT creates the maximally entangled Bell state (|00>+|11>)/sqrt(2)."}
    if n == 2 and seq == [("h", (), (1,)), ("cx", (1,), (0,))]:
        return {"id": "bell", "name": "Bell State preparation (q1 as control)",
                "detail": "This also creates a Bell state; the control/target choice only flips the label convention."}
    # GHZ
    if n >= 3 and seq == [("h", (), (0,))] + [("cx", (i - 1,), (i,)) for i in range(1, n)]:
        return {"id": "ghz", "name": f"GHZ state ({n} qubits)",
                "detail": "A Hadamard followed by a chain of CNOTs produces the n-partite GHZ state."}
    # QFT (only h + p gates, each qubit hadamarded, and controlled-phase ladders)
    if n >= 2 and set(counts.keys()) <= {"h", "p", "measure", "barrier"} and counts.get("h", 0) == n:
        gates_only = [(o["gate"], tuple(o["controls"]), tuple(o["targets"]))
                      for o in ops if o["gate"] in ("h", "p")]
        if all(g[0] == "p" for g in gates_only if g[0] == "p") and len(gates_only) == n + n * (n - 1) // 2:
            return {"id": "qft", "name": f"Quantum Fourier Transform ({n} qubits)",
                    "detail": "Ladder of Hadamard and controlled-phase gates implementing the QFT."}
    # Grover 2-qubit: H,H,CZ,H,H,X,X,CZ,X,X,H,H
    if n == 2 and seq == [("h", (), (0,)), ("h", (), (1,)), ("cz", (0,), (1,)),
                          ("h", (), (0,)), ("h", (), (1,)), ("x", (), (0,)), ("x", (), (1,)),
                          ("cz", (0,), (1,)), ("x", (), (0,)), ("x", (), (1,)),
                          ("h", (), (0,)), ("h", (), (1,))]:
        return {"id": "grover", "name": "Grover's algorithm (2 qubits)",
                "detail": "Oracle (CZ) + diffusion operator; amplifies the marked state |11>."}
    return None


def analyze_circuit(circuit):
    """Return a structured analysis for the AI tutor / circuit lab."""
    ops = normalize_circuit(circuit)
    n = circuit.get("num_qubits", 1)
    stats = circuit_stats(circuit)

    issues = []          # errors / warnings
    suggestions = []     # optimizations
    facts = []           # educational observations

    # Per-wire gate timeline for redundancy detection
    wire_ops = [[] for _ in range(n)]
    for o in ops:
        if o["gate"] in ("barrier", "measure"):
            continue
        for w in o["controls"] + o["targets"]:
            wire_ops[w].append(o)

    # Redundant adjacent pairs on the same wire
    for w in range(n):
        lo = wire_ops[w]
        for i in range(len(lo) - 1):
            a, b = lo[i], lo[i + 1]
            if a["gate"] == b["gate"]:
                red, label = _twin_redundant(a, b)
                if red:
                    suggestions.append({
                        "type": "redundancy",
                        "severity": "info",
                        "message": f"Qubit {w}: {label}. Remove one gate to simplify the circuit.",
                        "qubit": w,
                    })

    # Missing measurements
    if "measure" not in stats["gate_counts"]:
        issues.append({
            "type": "measurement",
            "severity": "warning",
            "message": "This circuit has no measurement gates. Add measures to see sampled outcomes "
                       "(you can still inspect the statevector, Bloch spheres and probabilities).",
        })
    elif len(stats["measured"]) < n:
        issues.append({
            "type": "measurement",
            "severity": "info",
            "message": f"Only {len(stats['measured'])} of {n} qubits are measured: "
                       f"{sorted(stats['measured'])}. Unmeasured qubits are not included in sampled counts.",
        })

    # Unused qubits
    if stats["unused_qubits"]:
        facts.append({
            "type": "resource",
            "message": f"Qubit(s) {stats['unused_qubits']} are never touched. "
                       "Remove them (or add gates) to reduce the register size.",
        })

    # An H gate directly applied to |0> (fine) but an X then H (fine too) - skip.

    # Controlled gate with a control qubit that was just measured
    measured_set = set(stats["measured"])
    for o in ops:
        if o["gate"] in ("barrier", "measure", "reset"):
            continue
        for c in o["controls"]:
            if c in measured_set:
                issues.append({
                    "type": "measurement-order",
                    "severity": "error",
                    "message": f"Gate {o['gate'].upper()} uses already-measured qubit {c} as a control. "
                               "Measurement collapses the qubit; the gate no longer acts coherently.",
                })

    # Toffoli / Fredkin decomposition hints
    if "ccx" in stats["gate_counts"]:
        suggestions.append({
            "type": "decomposition",
            "severity": "info",
            "message": "The Toffoli (CCX) gate can be decomposed into single-qubit gates and CNOTs. "
                       "On noisy hardware this matters; locally it is fine.",
        })

    # Entanglement hint for single H-only circuits
    if set(stats["gate_counts"]) <= {"h"} and n >= 2:
        facts.append({
            "type": "interpretation",
            "message": "Only single-qubit Hadamard gates: the state is a product state, "
                       "not entangled. Add a CNOT to create entanglement.",
        })

    # Circuit identification
    ident = _pattern_heuristics(ops, n)
    if ident:
        facts.append({
            "type": "identification",
            "message": f"Detected pattern: {ident['name']}. {ident['detail']}",
            "pattern": ident["id"],
        })

    # Generate equivalent-code snippet for educational display
    from .quantum.codegen import generate_code
    qiskit_code = generate_code(circuit, "qiskit", with_imports=False)

    return {
        "stats": stats,
        "issues": issues,
        "suggestions": suggestions,
        "facts": facts,
        "identification": ident,
        "qiskit_code": qiskit_code,
        "num_qubits": n,
    }


def generate_explanation(circuit):
    """Human-readable walkthrough of what the circuit does, gate by gate."""
    ops = normalize_circuit(circuit)
    n = circuit.get("num_qubits", 1)
    steps = []
    for o in ops:
        g = o["gate"]
        if g == "barrier":
            continue
        if g == "measure":
            steps.append(f"Measure qubit {o['target']} — collapses it to |0> or |1> and records the classical bit.")
            continue
        if g == "reset":
            steps.append(f"Reset qubit {o['target']} to |0>.")
            continue
        if g == "h":
            steps.append(f"H on q{o['targets'][0]}: creates superposition (|0> + |1>)/sqrt(2).")
        elif g == "x":
            steps.append(f"X on q{o['targets'][0]}: flips |0>↔|1> (the quantum NOT gate).")
        elif g == "y":
            steps.append(f"Y on q{o['targets'][0]}: bit+phase flip.")
        elif g == "z":
            steps.append(f"Z on q{o['targets'][0]}: flips the phase of |1> only.")
        elif g == "s":
            steps.append(f"S on q{o['targets'][0]}: 90-degree phase gate (adds i to |1>).")
        elif g == "sdg":
            steps.append(f"S† on q{o['targets'][0]}: inverse phase gate (-90 degrees).")
        elif g == "t":
            steps.append(f"T on q{o['targets'][0]}: 45-degree phase gate.")
        elif g == "tdg":
            steps.append(f"T† on q{o['targets'][0]}: inverse of the T gate.")
        elif g in ("rx", "ry", "rz"):
            ang = (o["params"] or [0])[0]
            steps.append(f"{g.upper()}({ang:.3f}) on q{o['targets'][0]}: rotation about the "
                         f"{g[1].upper()}-axis by {math.degrees(ang):.1f} degrees.")
        elif g == "p":
            ang = (o["params"] or [0])[0]
            steps.append(f"Phase({ang:.3f}) on q{o['targets'][0]}: adds relative phase e^(i{ang:.3f}) to |1>.")
        elif g == "cx":
            steps.append(f"CNOT(c={o['controls'][0]}, t={o['targets'][0]}): flips target when control is |1> — the entangling gate.")
        elif g == "cz":
            steps.append(f"CZ(c={o['controls'][0]}, t={o['targets'][0]}): phase flip on |11>.")
        elif g == "cy":
            steps.append(f"CY(c={o['controls'][0]}, t={o['targets'][0]}): controlled-Y.")
        elif g == "ccx":
            steps.append(f"Toffoli(c={o['controls'][0]},{o['controls'][1]}, t={o['targets'][0]}): flips target when both controls are |1>.")
        elif g == "swap":
            steps.append(f"SWAP(q{o['targets'][0]}, q{o['targets'][1]}): exchanges the two qubit states.")
        elif g == "cswap":
            steps.append(f"Fredkin(c={o['controls'][0]}, t={o['targets'][0]},{o['targets'][1]}): controlled SWAP.")
        elif g in ("u1", "u2", "u3"):
            steps.append(f"U{g[1]} on q{o['targets'][0]} with params {[round(x,3) for x in (o['params'] or [])]}.")
        else:
            steps.append(f"{g.upper()} on q{o['targets'][0]}.")
    return steps


def concept_gallery():
    """Short AI-friendly concept explanations used by the tutor chat."""
    return {
        "qubit": ("A qubit is a two-level quantum system, |ψ> = α|0> + β|1> with |α|²+|β|²=1. "
                  "Unlike a classical bit it can exist in a superposition of both states."),
        "superposition": ("Superposition is the ability of a qubit to be in a combination of |0> and |1> "
                          "simultaneously. The Hadamard gate H puts |0> into (|0>+|1>)/√2."),
        "entanglement": ("Entanglement is a correlation between qubits that cannot be explained classically. "
                         "The Bell state (|00>+|11>)/√2 is maximally entangled: measuring one qubit "
                         "instantly determines the other."),
        "measurement": ("Measurement projects the quantum state onto the computational basis. Outcome |0> "
                        "occurs with probability |α|², |1> with |β|², after which the state collapses."),
        "hadamard": ("The Hadamard gate H maps |0> → (|0>+|1>)/√2 and |1> → (|0>−|1>)/√2. It creates "
                     "superposition and is self-inverse (H·H = I)."),
        "cnot": ("The CNOT gate flips the target qubit only when the control qubit is |1>. It is the "
                 "prototypical entangling gate."),
        "phase": ("A phase gate (S, T, P, or Rz) changes the relative phase between |0> and |1> but not "
                  "the measurement probabilities."),
        "bloch-sphere": ("The Bloch sphere represents a single-qubit state as a point: north pole = |0>, "
                         "south pole = |1>, equator = equal superpositions."),
        "oracle": ("In quantum algorithms an oracle is a black-box subroutine encoding a classical function "
                   "as a reversible unitary."),
        "qft": ("The Quantum Fourier Transform maps computational basis states to a Fourier basis. "
                "It is the core of phase estimation and Shor's algorithm."),
        "grover": ("Grover's search amplifies the amplitude of marked states via repeated "
                   "oracle + diffusion iterations, achieving a quadratic speedup."),
        "phase-estimation": ("Quantum Phase Estimation extracts the eigenvalue phase of a unitary using "
                             "superposition, controlled operations, and the inverse QFT."),
        "teleportation": ("Quantum teleportation transfers an unknown quantum state using a shared Bell "
                          "pair and two classical bits of communication (LOCC)."),
        "deutsch-jozsa": ("The Deutsch–Jozsa algorithm determines if a function is constant or balanced "
                          "with a single quantum query instead of the classical 2^(n−1)+1."),
        "bernstein-vazirani": ("The Bernstein–Vazirani algorithm learns every bit of a hidden string in one "
                               "quantum query using superposition and phase kickback."),
        "tensor-product": ("The state of multiple qubits is the tensor product of single-qubit states: "
                           "|01> = |0>⊗|1>. The space grows exponentially as 2^n."),
        "decoherence": ("Decoherence is the loss of quantum coherence due to interaction with the "
                        "environment, degrading superposition and entanglement over time."),
        "no-cloning": ("The no-cloning theorem states an unknown quantum state cannot be copied exactly, "
                       "a fundamental difference from classical information."),
        "density-matrix": ("A density matrix ρ describes mixed states and subsystems; the reduced density "
                           "matrix of a qubit allows computing its Bloch vector."),
        "quantum-advantage": ("Quantum advantage is the point at which quantum computers outperform "
                              "classical ones for specific, useful tasks."),
    }
