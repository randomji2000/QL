"""Generate framework code (Qiskit, Cirq, PennyLane, Amazon Braket) from a
circuit JSON description."""

from .simulator import normalize_circuit

_ANGLE_LABELS = {
    "rx": "RX", "ry": "RY", "rz": "RZ", "p": "P", "u1": "P", "u2": "U2", "u3": "U3",
}


def _params_str(params):
    if not params:
        return ""
    if len(params) == 1:
        return f", {params[0]:.6f}" if params[0] else ", 0"
    parts = ", ".join(f"{p:.6f}" for p in params)
    return f", {parts}"


def qiskit_code(circuit, with_imports=True):
    n = circuit.get("num_qubits", 1)
    lines = []
    if with_imports:
        lines += ["from qiskit import QuantumCircuit, ClassicalRegister",
                  "from qiskit_aer import AerSimulator",
                  ""]
    lines += [f"qc = QuantumCircuit({n})",
              f"cr = ClassicalRegister({n})",
              "qc.add_register(cr)"]
    has_measure = False

    def emit(stmt):
        if cond:
            lines.append(f"with qc.if_test((cr[{cond['qubit']}], {cond['value']})):")
            lines.append(f"    {stmt}")
        else:
            lines.append(stmt)

    for op in normalize_circuit(circuit):
        name = op["gate"]
        if name == "barrier":
            continue
        t = op.get("targets") or ([] if op.get("target") is None else [op["target"]])
        c = op.get("controls") or []
        p = op["params"]
        cond = op.get("condition")
        if name == "measure":
            has_measure = True
            emit(f"qc.measure({t[0]}, cr[{t[0]}])")
        elif name == "reset":
            emit(f"qc.reset({t[0]})")
        elif name == "swap":
            emit(f"qc.swap({t[0]}, {t[1]})")
        elif name == "cx":
            emit(f"qc.cx({c[0]}, {t[0]})")
        elif name == "cz":
            emit(f"qc.cz({c[0]}, {t[0]})")
        elif name == "cy":
            emit(f"qc.cy({c[0]}, {t[0]})")
        elif name == "ch":
            emit(f"qc.ch({c[0]}, {t[0]})")
        elif name == "crx":
            emit(f"qc.crx({p[0]:.6f}, {c[0]}, {t[0]})" if p else f"qc.crx(0, {c[0]}, {t[0]})")
        elif name == "cry":
            emit(f"qc.cry({p[0]:.6f}, {c[0]}, {t[0]})" if p else f"qc.cry(0, {c[0]}, {t[0]})")
        elif name == "crz":
            emit(f"qc.crz({p[0]:.6f}, {c[0]}, {t[0]})" if p else f"qc.crz(0, {c[0]}, {t[0]})")
        elif name == "cr":
            emit(f"qc.cp({p[0]:.6f}, {c[0]}, {t[0]})" if p else f"qc.cp(0, {c[0]}, {t[0]})")
        elif name == "ccx":
            emit(f"qc.ccx({c[0]}, {c[1]}, {t[0]})")
        elif name == "cswap":
            emit(f"qc.cswap({c[0]}, {t[0]}, {t[1]})")
        elif name == "h":
            emit(f"qc.h({t[0]})")
        elif name in ("x", "y", "z", "s", "t"):
            emit(f"qc.{name}({t[0]})")
        elif name in ("sdg",):
            emit(f"qc.sdg({t[0]})")
        elif name in ("tdg",):
            emit(f"qc.tdg({t[0]})")
        elif name in ("rx", "ry", "rz"):
            emit(f"qc.{name}({p[0]:.6f}, {t[0]})" if p else f"qc.{name}(0, {t[0]})")
        elif name == "p":
            emit(f"qc.p({p[0]:.6f}, {t[0]})" if p else f"qc.p(0, {t[0]})")
        elif name == "u1":
            emit(f"qc.p({p[0]:.6f}, {t[0]})" if p else f"qc.p(0, {t[0]})")
        elif name == "u2":
            emit(f"qc.u2({p[0]:.6f}, {p[1]:.6f}, {t[0]})" if p and len(p) >= 2 else f"qc.u2(0, 0, {t[0]})")
        elif name == "u3":
            emit(f"qc.u3({p[0]:.6f}, {p[1]:.6f}, {p[2]:.6f}, {t[0]})" if p and len(p) >= 3 else f"qc.u3(0, 0, 0, {t[0]})")
        else:
            emit(f"# gate '{name}' not mappable")
    if with_imports:
        lines += [""]
        if has_measure:
            lines += ["counts = AerSimulator(shots=1024).run(qc).result().get_counts()",
                      "print(counts)", ""]
        else:
            lines += ["from qiskit.quantum_info import Statevector",
                      "print(Statevector(qc))", ""]
    return "\n".join(lines)


def cirq_code(circuit, with_imports=True):
    n = circuit.get("num_qubits", 1)
    lines = []
    if with_imports:
        lines.append("import cirq")
        lines.append("")
    lines.append(f"qubits = cirq.LineQubit.range({n})")
    lines.append("circuit = cirq.Circuit()")
    for op in normalize_circuit(circuit):
        name = op["gate"]
        if name in ("barrier", "reset"):
            continue
        t = op.get("targets") or ([] if op.get("target") is None else [op["target"]])
        c = op.get("controls") or []
        p = op["params"]
        qrefs = [f"qubits[{q}]" for q in t]
        crefs = [f"qubits[{q}]" for q in c]
        cond = op.get("condition")
        if cond and name != "measure":
            cond_suffix = f".with_classical_controls('m{cond['qubit']}')" if cond["value"] == 1 else ""
            if cond["value"] != 1:
                cond_suffix = ""  # conditioned-on-0 is uncommon; keep it simple
        else:
            cond_suffix = ""
        if name == "measure":
            lines.append(f"circuit.append(cirq.measure({qrefs[0]}, key='m{t[0]}'))")
        elif name == "h":
            lines.append(f"circuit.append(cirq.H({qrefs[0]}){cond_suffix})")
        elif name in ("x", "y", "z"):
            lines.append(f"circuit.append(cirq.{name.upper()}({qrefs[0]}){cond_suffix})")
        elif name == "s":
            lines.append(f"circuit.append(cirq.S({qrefs[0]}){cond_suffix})")
        elif name == "sdg":
            lines.append(f"circuit.append(cirq.S({qrefs[0]})**-1{cond_suffix})")
        elif name == "t":
            lines.append(f"circuit.append(cirq.T({qrefs[0]}){cond_suffix})")
        elif name == "tdg":
            lines.append(f"circuit.append(cirq.T({qrefs[0]})**-1{cond_suffix})")
        elif name == "rx":
            lines.append(f"circuit.append(cirq.rx({p[0]:.6f})({qrefs[0]}){cond_suffix})" if p else f"circuit.append(cirq.rx(0)({qrefs[0]}){cond_suffix})")
        elif name == "ry":
            lines.append(f"circuit.append(cirq.ry({p[0]:.6f})({qrefs[0]}){cond_suffix})" if p else f"circuit.append(cirq.ry(0)({qrefs[0]}){cond_suffix})")
        elif name == "rz":
            lines.append(f"circuit.append(cirq.rz({p[0]:.6f})({qrefs[0]}){cond_suffix})" if p else f"circuit.append(cirq.rz(0)({qrefs[0]}){cond_suffix})")
        elif name == "p":
            lines.append(f"circuit.append(cirq.ZPowGate(exponent={p[0]:.6f}/math.pi)({qrefs[0]}){cond_suffix})" if p else "")
        elif name == "cx":
            lines.append(f"circuit.append(cirq.CNOT({crefs[0]}, {qrefs[0]}){cond_suffix})")
        elif name == "cz":
            lines.append(f"circuit.append(cirq.CZ({crefs[0]}, {qrefs[0]}){cond_suffix})")
        elif name == "ccx":
            lines.append(f"circuit.append(cirq.TOFFOLI({crefs[0]}, {crefs[1]}, {qrefs[0]}){cond_suffix})")
        elif name == "swap":
            lines.append(f"circuit.append(cirq.SWAP({qrefs[0]}, {qrefs[1]}){cond_suffix})")
        else:
            lines.append(f"# gate '{name}' not mappable")
    if with_imports:
        lines += ["", "simulator = cirq.Simulator()",
                  "results = simulator.simulate(circuit)",
                  "print(results.final_state_vector)", ""]
    return "\n".join(lines)


def pennylane_code(circuit, with_imports=True):
    n = circuit.get("num_qubits", 1)
    body = []
    has_measure = False
    for op in normalize_circuit(circuit):
        name = op["gate"]
        if name == "barrier":
            continue
        if name == "measure":
            has_measure = True
            continue
        if name == "reset":
            continue
        t = op.get("targets") or ([] if op.get("target") is None else [op["target"]])
        c = op.get("controls") or []
        p = op["params"]
        if name == "h":
            body.append(f"qml.Hadamard(wires={t[0]})")
        elif name == "x":
            body.append(f"qml.PauliX(wires={t[0]})")
        elif name == "y":
            body.append(f"qml.PauliY(wires={t[0]})")
        elif name == "z":
            body.append(f"qml.PauliZ(wires={t[0]})")
        elif name == "s":
            body.append(f"qml.S(wires={t[0]})")
        elif name == "sdg":
            body.append(f"qml.S(wires={t[0]}, adjoint=True)")
        elif name == "t":
            body.append(f"qml.T(wires={t[0]})")
        elif name == "tdg":
            body.append(f"qml.T(wires={t[0]}, adjoint=True)")
        elif name == "rx":
            body.append(f"qml.RX({p[0]:.6f}, wires={t[0]})" if p else f"qml.RX(0.0, wires={t[0]})")
        elif name == "ry":
            body.append(f"qml.RY({p[0]:.6f}, wires={t[0]})" if p else f"qml.RY(0.0, wires={t[0]})")
        elif name == "rz":
            body.append(f"qml.RZ({p[0]:.6f}, wires={t[0]})" if p else f"qml.RZ(0.0, wires={t[0]})")
        elif name == "p":
            body.append(f"qml.PhaseShift({p[0]:.6f}, wires={t[0]})" if p else f"qml.PhaseShift(0.0, wires={t[0]})")
        elif name == "cx":
            body.append(f"qml.CNOT(wires=[{c[0]}, {t[0]}])")
        elif name == "cz":
            body.append(f"qml.CZ(wires=[{c[0]}, {t[0]}])")
        elif name == "cy":
            body.append(f"qml.CY(wires=[{c[0]}, {t[0]}])")
        elif name == "ccx":
            body.append(f"qml.Toffoli(wires=[{c[0]}, {c[1]}, {t[0]}])")
        elif name == "swap":
            body.append(f"qml.SWAP(wires=[{t[0]}, {t[1]}])")
        elif name == "cswap":
            body.append(f"qml.CSWAP(wires=[{c[0]}, {t[0]}, {t[1]}])")
        else:
            body.append(f"# gate '{name}' not mappable")
    return_stat = "qml.counts()" if has_measure else "qml.state()"
    lines = []
    if with_imports:
        lines += ["import pennylane as qml", "import numpy as np", "",
                  f"dev = qml.device('default.qubit', wires={n}, shots={'1024' if has_measure else 'None'})",
                  "", "@qml.qnode(dev)", "def run_circuit():"]
    else:
        lines += ["@qml.qnode(qml.device('default.qubit', wires=1, shots=None))",
                  "def run_circuit():"]
    for b in body:
        lines.append(f"    {b}")
    lines.append(f"    return {return_stat}")
    lines += ["", "print(run_circuit())", ""]
    return "\n".join(lines)


def braket_code(circuit, with_imports=True):
    n = circuit.get("num_qubits", 1)
    lines = []
    if with_imports:
        lines.append("from braket.circuits import Circuit")
        lines.append("")
    lines.append("qc = Circuit()")
    for op in normalize_circuit(circuit):
        name = op["gate"]
        if name in ("barrier", "reset"):
            continue
        t = op.get("targets") or ([] if op.get("target") is None else [op["target"]])
        c = op.get("controls") or []
        p = op["params"]
        if name == "measure":
            lines.append(f"qc.measure({t[0]})")
        elif name == "h":
            lines.append(f"qc.h({t[0]})")
        elif name in ("x", "y", "z"):
            lines.append(f"qc.{name}({t[0]})")
        elif name == "s":
            lines.append(f"qc.s({t[0]})")
        elif name == "sdg":
            lines.append(f"qc.si({t[0]})")
        elif name == "t":
            lines.append(f"qc.t({t[0]})")
        elif name == "tdg":
            lines.append(f"qc.ti({t[0]})")
        elif name == "rx":
            lines.append(f"qc.rx({t[0]}, {p[0]:.6f})" if p else f"qc.rx({t[0]}, 0)")
        elif name == "ry":
            lines.append(f"qc.ry({t[0]}, {p[0]:.6f})" if p else f"qc.ry({t[0]}, 0)")
        elif name == "rz":
            lines.append(f"qc.rz({t[0]}, {p[0]:.6f})" if p else f"qc.rz({t[0]}, 0)")
        elif name == "cx":
            lines.append(f"qc.cnot(control={c[0]}, target={t[0]})")
        elif name == "cz":
            lines.append(f"qc.cz(control={c[0]}, target={t[0]})")
        elif name == "ccx":
            lines.append(f"qc.ccnot(control={c[0]}, control2={c[1]}, target={t[0]})")
        elif name == "swap":
            lines.append(f"qc.swap({t[0]}, {t[1]})")
        else:
            lines.append(f"# gate '{name}' not mappable")
    if with_imports:
        lines += ["", "# Local simulator (from amazon-braket-sdk):",
                  "# from braket.devices import LocalSimulator",
                  "# print(LocalSimulator().run(qc, shots=1000).result().measurement_counts)", ""]
    return "\n".join(lines)


def generate_code(circuit, framework="qiskit", with_imports=True):
    """Generate framework code from a circuit description."""
    circuit = circuit if isinstance(circuit, dict) else {"num_qubits": 1, "gates": circuit}
    if framework == "qiskit":
        return qiskit_code(circuit, with_imports)
    if framework == "cirq":
        return cirq_code(circuit, with_imports)
    if framework == "pennylane":
        return pennylane_code(circuit, with_imports)
    if framework == "braket":
        return braket_code(circuit, with_imports)
    return qiskit_code(circuit, with_imports)
