"""Multi-backend simulation support.

`local` — the built-in NumPy statevector simulator (always available, no deps).
`aer`    — Qiskit Aer statevector / qasm simulator (optional, if qiskit installed).
`cirq`   — Cirq simulator (optional, if cirq installed).

Unavailable backends are reported but return a clear error at run time so the
platform stays fully functional with only the built-in engine.
"""

import importlib
import math

from .quantum.simulator import CircuitError, run_circuit

_BACKENDS = [
    {
        "id": "local",
        "name": "QStudio Statevector (built-in)",
        "provider": "Built-in NumPy engine",
        "type": "statevector",
        "max_qubits": 18,
        "shots": [1, 10, 100, 1024, 4096, 8192],
        "available": True,
        "description": "Exact statevector simulation with per-qubit Bloch vectors, "
                       "entanglement entropies and measurement sampling.",
    },
    {
        "id": "aer_statevector",
        "name": "Qiskit Aer Statevector",
        "provider": "IBM Qiskit Aer",
        "type": "statevector",
        "max_qubits": 24,
        "shots": [1, 100, 1024, 8192],
        "available": True,
        "description": "High-performance statevector simulation from IBM's Qiskit Aer.",
    },
    {
        "id": "aer_qasm",
        "name": "Qiskit Aer QASM (sampling)",
        "provider": "IBM Qiskit Aer",
        "type": "sampling",
        "max_qubits": 24,
        "shots": [10, 100, 1024, 8192, 32768],
        "available": True,
        "description": "Qiskit Aer shot-based sampling with measurement noise options.",
    },
    {
        "id": "cirq",
        "name": "Cirq Simulator",
        "provider": "Google Cirq",
        "type": "statevector",
        "max_qubits": 20,
        "shots": [1, 100, 1024, 8192],
        "available": True,
        "description": "Google Cirq density-matrix / statevector simulation.",
    },
]


def _available_backends():
    result = []
    for b in _BACKENDS:
        b = dict(b)
        try:
            _probe_backend(b["id"])
            b["available"] = True
        except Exception:
            b["available"] = False
        result.append(b)
    return result


def _probe_backend(bid):
    if bid == "local":
        return
    if bid.startswith("aer"):
        importlib.import_module("qiskit")
        importlib.import_module("qiskit_aer")
    elif bid == "cirq":
        importlib.import_module("cirq")


def list_backends():
    return _available_backends()


def _build_qiskit_circuit(circuit, aer=True):
    """Convert circuit JSON to a Qiskit QuantumCircuit."""
    try:
        from qiskit import ClassicalRegister, QuantumCircuit
    except Exception:
        raise CircuitError("Qiskit is not installed in this environment")
    n = circuit.get("num_qubits", 1)
    qc = QuantumCircuit(n)
    measured = [False] * n
    creg = None
    from .quantum.simulator import normalize_circuit

    for op in normalize_circuit(circuit):
        name = op["gate"]
        t = op["targets"]
        c = op["controls"]
        p = op["params"]
        if name == "barrier":
            continue
        if name == "measure":
            if creg is None:
                from qiskit.circuit import ClassicalRegister as _CR
                creg = _CR(n, "meas")
                qc.add_register(creg)
            qc.measure(op["target"], creg[op["target"]])
            measured[op["target"]] = True
            continue
        if name == "reset":
            qc.reset(op["target"])
            continue
        if name == "h":
            qc.h(t[0])
        elif name == "x":
            qc.x(t[0])
        elif name == "y":
            qc.y(t[0])
        elif name == "z":
            qc.z(t[0])
        elif name == "s":
            qc.s(t[0])
        elif name == "sdg":
            qc.sdg(t[0])
        elif name == "t":
            qc.t(t[0])
        elif name == "tdg":
            qc.tdg(t[0])
        elif name == "p":
            qc.p(p[0] if p else 0, t[0])
        elif name == "rx":
            qc.rx(p[0] if p else 0, t[0])
        elif name == "ry":
            qc.ry(p[0] if p else 0, t[0])
        elif name == "rz":
            qc.rz(p[0] if p else 0, t[0])
        elif name == "u1":
            qc.p(p[0] if p else 0, t[0])
        elif name == "u2":
            qc.u2(p[0] if p else 0, p[1] if p and len(p) > 1 else 0, t[0])
        elif name == "u3":
            qc.u3(p[0] if p else 0, p[1] if p and len(p) > 1 else 0,
                  p[2] if p and len(p) > 2 else 0, t[0])
        elif name == "cx":
            qc.cx(c[0], t[0])
        elif name == "cy":
            qc.cy(c[0], t[0])
        elif name == "cz":
            qc.cz(c[0], t[0])
        elif name == "ccx":
            qc.ccx(c[0], c[1], t[0])
        elif name == "swap":
            qc.swap(t[0], t[1])
        elif name == "cswap":
            qc.cswap(c[0], t[0], t[1])
    return qc, measured


def _run_aer(circuit, backend_id, shots, seed):
    import numpy as np
    from qiskit_aer import AerSimulator, QasmSimulator

    qc, measured = _build_qiskit_circuit(circuit)
    is_statevector = "statevector" in backend_id

    if is_statevector:
        backend = AerSimulator(method="statevector")
        svqc = qc.copy()
        svqc.save_statevector()
        kwargs = {"shots": 1}
        if seed is not None:
            kwargs["seed_simulator"] = seed
        job = backend.run(svqc, **kwargs)
        result = job.result()
        sv = result.get_statevector(svqc)
        amps = np.asarray(sv).reshape(-1)
        probs = (np.abs(amps) ** 2).astype(float)
        probs = probs / (probs.sum() + 1e-15)
        n = len(amps).bit_length() - 1
        labels = []
        components = []
        for i in range(len(amps)):
            if probs[i] > 1e-12:
                raw = format(i, f"0{n}b")[::-1]
                labels.append(raw)
                components.append({
                    "state": raw,
                    "amplitude": f"{amps[i].real:.6f}{amps[i].imag:+.6f}j",
                    "probability": round(float(probs[i]), 6),
                })
        counts = None
        bloch = []
        ent = []
        if n <= 8:
            from .quantum.simulator import bloch_vector, partial_trace, von_neumann_entropy
            state = amps.reshape([2] * n)
            for q in range(n):
                rho = partial_trace(state, n, q)
                bloch.append(bloch_vector(rho))
                ent.append(von_neumann_entropy(rho))
        return {
            "num_qubits": n,
            "statevector": {"components": components, "dimension": 2 ** n},
            "probabilities": [round(float(p), 6) for p in probs],
            "counts": counts,
            "shots": shots,
            "bloch": bloch,
            "entanglement": ent,
            "outcome_labels": labels,
        }
    else:
        backend = QasmSimulator()
        if not any(measured):
            qc.measure_all()
        kwargs = {"shots": shots}
        if seed is not None:
            kwargs["seed_simulator"] = seed
        job = backend.run(qc, **kwargs)
        result = job.result()
        # qasm: counts
        counts = result.get_counts()
        n = circuit.get("num_qubits", 1)
        counts = {k.zfill(n)[::-1] if len(k) < n else k[::-1]: v for k, v in counts.items()}
        counts = dict(sorted(counts.items(), key=lambda kv: -kv[1]))
        total = shots or 1024
        probs = [round(counts.get(format(i, f"0{n}b")[::-1], 0) / total, 6) for i in range(2 ** n)]
        return {
            "num_qubits": n,
            "statevector": None,
            "probabilities": probs,
            "counts": counts,
            "shots": shots,
            "bloch": [],
            "entanglement": [],
            "outcome_labels": sorted(counts.keys()),
        }


def _run_cirq(circuit, shots, seed):
    try:
        import cirq
    except Exception:
        raise CircuitError("Cirq is not installed in this environment")
    import numpy as np

    from .quantum.simulator import normalize_circuit

    n = circuit.get("num_qubits", 1)
    qubits = cirq.LineQubit.range(n)
    ops = []
    measured = [False] * n
    for op in normalize_circuit(circuit):
        name = op["gate"]
        t = op["targets"]
        c = op["controls"]
        p = op["params"]
        if name in ("barrier", "reset"):
            continue
        if name == "measure":
            ops.append(cirq.measure(qubits[op["target"]], key=f"m{op['target']}"))
            measured[op["target"]] = True
            continue
        q = qubits[t[0]]
        if name == "h":
            ops.append(cirq.H(q))
        elif name == "x":
            ops.append(cirq.X(q))
        elif name == "y":
            ops.append(cirq.Y(q))
        elif name == "z":
            ops.append(cirq.Z(q))
        elif name == "s":
            ops.append(cirq.S(q))
        elif name == "sdg":
            ops.append(cirq.S(q) ** -1)
        elif name == "t":
            ops.append(cirq.T(q))
        elif name == "tdg":
            ops.append(cirq.T(q) ** -1)
        elif name == "rx":
            ops.append(cirq.rx(p[0] if p else 0)(q))
        elif name == "ry":
            ops.append(cirq.ry(p[0] if p else 0)(q))
        elif name == "rz":
            ops.append(cirq.rz(p[0] if p else 0)(q))
        elif name == "p":
            ops.append(cirq.ZPowGate(exponent=(p[0] if p else 0) / math.pi)(q))
        elif name == "cx":
            ops.append(cirq.CNOT(qubits[c[0]], q))
        elif name == "cz":
            ops.append(cirq.CZ(qubits[c[0]], q))
        elif name == "ccx":
            ops.append(cirq.TOFFOLI(qubits[c[0]], qubits[c[1]], q))
        elif name == "swap":
            ops.append(cirq.SWAP(qubits[t[0]], qubits[t[1]]))
        elif name == "cswap":
            ops.append(cirq.FREDKIN(qubits[c[0]], qubits[t[0]], qubits[t[1]]))
    circuit_cirq = cirq.Circuit(ops)

    if all(measured):
        sim = cirq.Simulator(seed=seed)
        res = sim.run(circuit_cirq, repetitions=shots)
        counts = {}
        for i in range(shots):
            key = "".join(str(res.measurements[f"m{q}"][i][0]) for q in range(n))
            counts[key] = counts.get(key, 0) + 1
        counts = dict(sorted(counts.items(), key=lambda kv: -kv[1]))
        return {"counts": counts, "shots": shots}
    else:
        sim = cirq.Simulator(seed=seed)
        res = sim.simulate(circuit_cirq)
        amps = np.asarray(res.final_state_vector).reshape(-1)
        probs = (np.abs(amps) ** 2).astype(float)
        probs = probs / (probs.sum() + 1e-15)
        components = []
        for i in range(len(amps)):
            if probs[i] > 1e-12:
                raw = format(i, f"0{n}b")[::-1]
                components.append({
                    "state": raw,
                    "amplitude": f"{amps[i].real:.6f}{amps[i].imag:+.6f}j",
                    "probability": round(float(probs[i]), 6),
                })
        return {
            "statevector": {"components": components, "dimension": 2 ** n},
            "probabilities": [round(float(p), 6) for p in probs],
            "counts": None,
            "shots": None,
            "bloch": [],
            "entanglement": [],
            "outcome_labels": [c["state"] for c in components],
        }


def run_on_backend(circuit, backend_id="local", shots=1024, seed=42):
    """Dispatch a circuit to the requested backend."""
    shots = int(shots or 1024)
    if backend_id == "local":
        return run_circuit(circuit, shots=shots, seed=seed)
    if backend_id.startswith("aer"):
        return _run_aer(circuit, backend_id, shots, seed)
    if backend_id == "cirq":
        result = _run_cirq(circuit, shots, seed)
        if "counts" in result and result["statevector"] is None and result.get("bloch") is None:
            base = run_circuit(circuit, shots=shots, seed=seed)
            result["num_qubits"] = base["num_qubits"]
            result["probabilities"] = base["probabilities"]
            result["bloch"] = base["bloch"]
            result["entanglement"] = base["entanglement"]
            result["statevector"] = None
            result["outcome_labels"] = sorted(result["counts"].keys())
            return result
        return result
    raise CircuitError(f"Unknown backend: {backend_id}")
