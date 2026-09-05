"""Statevector quantum circuit simulator.

Two execution paths:
  * fast vectorized path — used when the circuit has no measurements and no
    classically-conditioned gates;
  * shot-based path — used when measurements and/or conditioned gates appear,
    so mid-circuit collapse and feed-forward are modelled correctly.

Gate JSON shape:
  {
    "gate": "h",                 # alias allowed
    "target": 0,                 # primary target wire
    "targets": [0, 1],           # for multi-target gates (swap)
    "controls": [1, 2],          # control wire indices
    "params": [3.14],            # angles in radians (or list for u2/u3)
    "condition": {"qubit": 1, "value": 1},   # apply only if qubit 1 measured as 1
  }
"""

import math
import random

import numpy as np

from .gates import GATE_DEFS, PRECONTROLLED, controlled_matrix, gate_matrix, lookup

X_M = np.array([[0, 1], [1, 0]], dtype=complex)
Y_M = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z_M = np.array([[1, 0], [0, -1]], dtype=complex)


class CircuitError(ValueError):
    """Raised when a circuit is semantically invalid."""


def normalize_circuit(circuit):
    """Validate and normalize a circuit dict into a list of gate ops."""
    num_qubits = circuit.get("num_qubits", 1)
    gates = circuit.get("gates", [])
    ops = []
    for i, g in enumerate(gates):
        if isinstance(g, str):
            g = {"gate": g}
        if not isinstance(g, dict):
            raise CircuitError(f"Gate #{i} is not a valid object")
        name = lookup(g.get("gate"))
        if name is None:
            raise CircuitError(f"Gate #{i}: unknown gate '{g.get('gate')}'")
        params = g.get("params", None)
        if params is None and "param" in g:
            params = g["param"]
        if isinstance(params, (int, float)):
            params = [float(params)]

        target = g.get("target")
        targets = g.get("targets")
        controls = g.get("controls") or []

        if name == "barrier":
            ops.append({"gate": name, "target": None, "targets": [], "controls": [],
                        "params": params, "index": i})
            continue
        if name in ("measure", "reset"):
            if target is None:
                raise CircuitError(f"Gate #{i}: {name} requires a target qubit")
            ops.append({"gate": name, "target": int(target), "targets": [], "controls": [],
                        "params": params, "index": i})
            continue

        if name in ("swap", "iswap", "cswap"):
            if g.get("targets") and len(g["targets"]) >= 2:
                targets = [int(x) for x in g["targets"]]
            elif g.get("target") is not None:
                targets = [int(target), int(g.get("target2", target + 1))]
            else:
                raise CircuitError(f"Gate #{i}: {name} requires two target qubits")
        elif targets is None:
            targets = [target]

        targets = [int(t) for t in targets]
        controls = [int(c) for c in controls]

        all_wires = targets + controls
        for w in all_wires:
            if not (0 <= w < num_qubits):
                raise CircuitError(f"Gate #{i}: qubit wire {w} out of range (0..{num_qubits - 1})")
        if len(set(all_wires)) != len(all_wires):
            raise CircuitError(f"Gate #{i}: control and target wires overlap")

        d = GATE_DEFS[name]
        if name in ("swap", "iswap"):
            if len(targets) != 2:
                raise CircuitError(f"Gate #{i}: {name} expects two target qubits")
            if len(controls) > 0:
                raise CircuitError(f"Gate #{i}: {name} cannot be controlled directly; use cswap")
        elif d["arity"] == 1 and len(targets) != 1:
            raise CircuitError(f"Gate #{i}: {name} expects exactly one target qubit")
        if name == "ccx" and len(controls) != 2:
            raise CircuitError(f"Gate #{i}: Toffoli (ccx) requires exactly 2 control qubits")
        if name == "cswap" and len(controls) != 1:
            raise CircuitError(f"Gate #{i}: Fredkin (cswap) requires exactly 1 control qubit")

        condition = None
        if "condition" in g:
            cond = g["condition"]
            if isinstance(cond, dict) and "qubit" in cond:
                condition = {"qubit": int(cond["qubit"]), "value": int(cond.get("value", 1))}
            else:
                condition = {"qubit": int(cond), "value": 1}

        ops.append({"gate": name, "target": targets[0] if targets else None,
                    "targets": targets, "controls": controls, "params": params,
                    "index": i, "condition": condition})
    return ops


def _permute_to_front(state, n, wires):
    order = list(wires) + [q for q in range(n) if q not in wires]
    return np.transpose(state, order), order


def _apply_unitary(state, n, wires, matrix):
    """Apply a square unitary over the given wires (first wires axis)."""
    k = len(wires)
    perm, order = _permute_to_front(state, n, wires)
    shape = [2] * n
    act = perm.reshape(2 ** k, -1)
    act = matrix @ act
    inv = np.argsort(order)
    return np.transpose(act.reshape(shape), inv)


def _gate_wire_matrix(op):
    """Build the operator over (controls + targets) wires for a gate."""
    name = op["gate"]
    targets = op["targets"]
    controls = op["controls"]
    params = op["params"]
    if name in ("swap", "iswap"):
        return gate_matrix(name, params), targets, []
    base = gate_matrix(name, params)
    if base is None:
        raise CircuitError(f"No matrix for gate {name}")
    if name in PRECONTROLLED:
        wires = controls + targets
        return base, wires, []
    wires = controls + targets
    if controls:
        op_matrix = controlled_matrix(base, num_controls=len(controls))
    else:
        op_matrix = base
    return op_matrix, wires, []


def apply_op(state, n, op):
    """Apply a single normalized operation to an n-qubit state (no condition)."""
    name = op["gate"]
    if name == "barrier":
        return state
    if name in ("measure",):
        return state
    if name == "reset":
        wires = [op["target"]]
        perm, order = _permute_to_front(state, n, wires)
        act = perm.reshape(2, -1)
        if np.linalg.norm(act[0]) < 1e-14:
            return state
        act = np.where(np.arange(2).reshape(-1, 1) == 0, act, 0.0)
        act = act / (np.linalg.norm(act) + 1e-15)
        inv = np.argsort(order)
        return np.transpose(act.reshape([2] * n), inv)
    matrix, wires, _ = _gate_wire_matrix(op)
    return _apply_unitary(state, n, wires, matrix)


def _sample_qubit(state, n, q, rng):
    """Sample a single qubit outcome from the state and collapse."""
    perm, order = _permute_to_front(state, n, [q])
    act = perm.reshape(2, -1)
    p0 = float((np.abs(act[0]) ** 2).sum())
    p1 = float((np.abs(act[1]) ** 2).sum())
    denom = p0 + p1 + 1e-15
    bit = 1 if rng.random() < p1 / denom else 0
    # collapse
    row = act[bit]
    nrow = np.linalg.norm(row)
    if nrow > 1e-14:
        row = row / nrow
    new = np.zeros_like(act)
    new[bit] = row
    inv = np.argsort(order)
    return bit, np.transpose(new.reshape([2] * n), inv)


def _shot_based(ops, n, shots, rng):
    """Run a circuit shot-by-shot, returning sampled outcome bitstrings."""
    from collections import Counter

    counted = Counter()
    measured_qubits = sorted({o["target"] for o in ops if o["gate"] == "measure"})
    for _ in range(shots):
        state = np.zeros([2] * n, dtype=complex)
        state[(0,) * n] = 1.0
        cbits = {}
        for op in ops:
            if op.get("condition"):
                cond = op["condition"]
                if cbits.get(cond["qubit"]) == cond["value"]:
                    state = apply_op(state, n, op)
                continue
            if op["gate"] == "measure":
                bit, state = _sample_qubit(state, n, op["target"], rng)
                cbits[op["target"]] = bit
                continue
            state = apply_op(state, n, op)
        outcome = "".join(str(cbits.get(q, 0)) for q in reversed(measured_qubits))
        counted[outcome] += 1
    return counted, measured_qubits


def _no_measurement_ops(ops):
    return all(o["gate"] != "measure" and not o.get("condition") for o in ops)


def sample_counts(probabilities, shots, rng, nbits=1):
    """Sample outcome counts from a probability distribution over bitstrings."""
    probs = np.asarray(probabilities, dtype=float)
    probs = probs / (probs.sum() + 1e-15)
    if shots <= 0 or len(probs) == 0:
        return {}
    idx = rng.choice(len(probs), size=shots, p=probs)
    counts = {}
    for i in idx:
        key = format(int(i), f"0{nbits}b")[::-1] if nbits > 0 else "0"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def partial_trace(state, n, keep_wire):
    keep = [keep_wire]
    others = [q for q in range(n) if q != keep_wire]
    perm, order = _permute_to_front(state, n, keep + others)
    psi = perm.reshape(2, -1)
    return psi @ psi.conj().T


def bloch_vector(rho):
    x = float(np.real(np.trace(rho @ X_M)))
    y = float(np.real(np.trace(rho @ Y_M)))
    z = float(np.real(np.trace(rho @ Z_M)))
    r = math.sqrt(x * x + y * y + z * z)
    if r > 1e-9:
        x, y, z = x / r, y / r, z / r
    else:
        x = y = 0.0
        z = 1.0
    return {"x": round(x, 6), "y": round(y, 6), "z": round(z, 6)}


def von_neumann_entropy(rho):
    vals = np.linalg.eigvalsh(rho)
    vals = np.clip(vals, 1e-15, 1.0)
    return round(float(-np.sum(vals * np.log2(vals))), 6)


def run_circuit(circuit, shots=1024, seed=None):
    """Execute a circuit; return a complete results dictionary."""
    rng = np.random.default_rng(seed)
    num_qubits = circuit.get("num_qubits", 1)
    if num_qubits < 1:
        raise CircuitError("num_qubits must be >= 1")
    if num_qubits > 18:
        raise CircuitError("statevector simulation limited to 18 qubits")

    ops = normalize_circuit(circuit)
    n = int(num_qubits)

    has_measure = any(o["gate"] == "measure" for o in ops)
    has_condition = any(o.get("condition") for o in ops)

    state = np.zeros([2] * n, dtype=complex)
    state[(0,) * n] = 1.0

    if not (has_measure or has_condition):
        for op in ops:
            state = apply_op(state, n, op)
        amps = state.reshape(-1)
        probs = (np.abs(amps) ** 2).astype(float)
        probs = probs / (probs.sum() + 1e-15)
        counts = sample_counts(probs, shots, rng, nbits=n)
        measured_qubits = list(range(n))
    else:
        # Forward to the last measurement boundary to compute exact probs for
        # display when there are no conditional gates.
        if has_measure and not has_condition:
            measured_qubits = sorted({o["target"] for o in ops if o["gate"] == "measure"})
            pre_state = state
            for op in ops:
                if op["gate"] == "measure":
                    continue
                pre_state = apply_op(pre_state, n, op)
            amps = pre_state.reshape(-1)
            probs = (np.abs(amps) ** 2).astype(float)
            probs = probs / (probs.sum() + 1e-15)
        else:
            measured_qubits = sorted({o["target"] for o in ops if o["gate"] == "measure"})
            probs = [1.0]

        if shots > 0:
            counts, _ = _shot_based(ops, n, shots, rng)
        else:
            counts = {}

    # Build components list
    nbits = n
    components = []
    total = max(1, len(probs))
    if len(probs) == 1 and has_condition:
        # empirical probs from counts
        out_probs = {}
        if counts:
            total_shots = sum(counts.values())
            for k, v in counts.items():
                out_probs[k] = v / total_shots
        components = [{"state": k, "amplitude": None, "probability": round(v, 6)}
                      for k, v in sorted(out_probs.items())]
        probs = [round(v, 6) for v in out_probs.values()]
        labels = sorted(out_probs.keys())
    else:
        labels = []
        for i in range(min(len(probs), 2 ** n)):
            p = float(probs[i])
            if p > 1e-12:
                raw = format(i, f"0{nbits}b")[::-1]
                labels.append(raw)
                if has_measure and not has_condition:
                    # display probability grouped by measured outcomes
                    pass
                a = amps[i]
                components.append({
                    "state": raw,
                    "amplitude": f"{a.real:.6f}{a.imag:+.6f}j",
                    "probability": round(p, 6),
                })
        if has_measure and not has_condition:
            # aggregate probabilities over measured outcomes
            m = len(measured_qubits)
            mpos = {q: idx for idx, q in enumerate(measured_qubits)}
            grouped = {}
            for i in range(len(probs)):
                raw = format(i, f"0{nbits}b")[::-1]
                key = "".join(raw[q] for q in reversed(measured_qubits))
                grouped[key] = grouped.get(key, 0.0) + probs[i]
            probs_measured = [round(grouped.get(format(j, f"0{m}b"), 0.0), 6) for j in range(2 ** m)]
            labels = sorted(grouped.keys())
            if counts:
                components = [{"state": k, "amplitude": None,
                               "probability": round(v / max(1, shots), 6)}
                              for k, v in sorted(counts.items())]
            else:
                components = [{"state": k, "amplitude": None, "probability": round(v, 6)}
                              for k, v in sorted(grouped.items())]
            probs = probs_measured
        else:
            labels = [c["state"] for c in components]

    bloch = []
    ent = []
    if not (has_measure or has_condition):
        for q in range(n):
            rho = partial_trace(state, n, q)
            bloch.append(bloch_vector(rho))
            ent.append(von_neumann_entropy(rho))

    rho_full = None
    purity = 0.0
    ent_metric = 0.0
    if not (has_measure or has_condition):
        ampsv = state.reshape(-1)
        purity = round(float(np.real((np.abs(ampsv) ** 2).sum() ** 1)), 6)
        if n >= 2:
            ent_metric = round(1.0 - float((np.abs(ampsv) ** 2).max()), 6)

    return {
        "num_qubits": n,
        "statevector": {"components": components, "dimension": 2 ** n},
        "probabilities": [round(float(p), 6) for p in probs],
        "counts": counts,
        "shots": shots,
        "bloch": bloch,
        "entanglement": ent,
        "purity": purity,
        "entanglement_metric": ent_metric,
        "outcome_labels": labels,
        "measured_qubits": measured_qubits if (has_measure or has_condition) else list(range(n)),
    }


def circuit_stats(circuit):
    """Lightweight structural stats used by the UI and analysis engine."""
    ops = normalize_circuit(circuit)
    n = circuit.get("num_qubits", 1)
    depth = 0
    wire_next = [0] * n
    for op in ops:
        if op["gate"] == "barrier":
            continue
        wires = op["controls"] + op["targets"]
        if not wires:
            continue
        col = max(wire_next[w] for w in wires)
        for w in wires:
            wire_next[w] = col + 1
    depth = max(wire_next) if n else 0
    gate_counts = {}
    for op in ops:
        if op["gate"] == "barrier":
            continue
        gate_counts[op["gate"]] = gate_counts.get(op["gate"], 0) + 1
    used = set()
    for op in ops:
        for w in op["controls"] + op["targets"]:
            used.add(w)
    return {
        "num_gates": sum(1 for o in ops if o["gate"] not in ("barrier",)),
        "depth": int(depth),
        "gate_counts": gate_counts,
        "used_qubits": sorted(used),
        "unused_qubits": [q for q in range(n) if q not in used],
        "measured": [o["target"] for o in ops if o["gate"] == "measure"],
    }
