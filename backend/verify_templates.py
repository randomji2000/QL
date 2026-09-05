"""Verify every circuit template produces the expected outcome."""

import math

from app.quantum.simulator import run_circuit
from app.templates import TEMPLATES


def probs_of(circuit, shots=8192):
    r = run_circuit(circuit, shots=shots, seed=42)
    return r, {c["state"]: c["probability"] for c in r["statevector"]["components"]}


def check_bell(t):
    r, p = probs_of({"num_qubits": 2, "gates": t["gates"]})
    assert abs(p.get("00", 0) - 0.5) < 0.01 and abs(p.get("11", 0) - 0.5) < 0.01, p
    return "00/11 ~ 0.5"


def check_ghz(t):
    r, p = probs_of({"num_qubits": 3, "gates": t["gates"]})
    assert abs(p.get("000", 0) - 0.5) < 0.01 and abs(p.get("111", 0) - 0.5) < 0.01, p
    return "000/111 ~ 0.5"


def check_w(t):
    r, p = probs_of({"num_qubits": 3, "gates": t["gates"]})
    assert abs(p.get("001", 0) - 1 / 3) < 0.02, p
    assert abs(p.get("010", 0) - 1 / 3) < 0.02, p
    assert abs(p.get("100", 0) - 1 / 3) < 0.02, p
    return "001/010/100 ~ 1/3 each"


def check_dj(t):
    r, p = probs_of({"num_qubits": 3, "gates": t["gates"]})
    top = max(p, key=lambda k: p[k])
    # label = q2 q1 q0; input register is q1 q0 -> top[1:]
    assert top[1:] in ("01", "10", "11"), p
    return f"non-zero input register {top[1:]} -> balanced"


def check_bv(t):
    r, p = probs_of({"num_qubits": 5, "gates": t["gates"]})
    top = max(p, key=lambda k: p[k])
    # label = q4 q3 q2 q1 q0; input register = top[1:] = q3 q2 q1 q0 = 0 1 0 1
    assert top[1:] == "0101", p
    return f"input register {top[1:]} (s = 101 on q0,q2)"


def check_qft(t):
    r, p = probs_of({"num_qubits": 3, "gates": t["gates"]}, shots=1)
    comps = r["statevector"]["components"]
    assert len(comps) == 8, comps
    for c in comps:
        assert abs(c["probability"] - 0.125) < 1e-6, c
    return "uniform 8-component state"


def check_grover2(t):
    r, p = probs_of({"num_qubits": 2, "gates": t["gates"]})
    assert p.get("11", 0) > 0.9, p
    return f"|11> with p={p.get('11', 0):.3f}"


def check_qpe(t):
    r, p = probs_of({"num_qubits": 3, "gates": t["gates"]})
    top = max(p, key=lambda k: p[k])
    assert top[1:] == "10", p
    return f"top outcome {top} -> phase register 10 = 0.01_bin = 1/4"


def check_teleport(t):
    r = run_circuit({"num_qubits": 3, "gates": t["gates"]}, shots=16000, seed=7)
    tot = sum(r["counts"].values())
    # count of q2 == 1 across all outcomes: key format is bits of measured qubits [0,1,2] reversed => k[0] is q2
    p1 = sum(v for k, v in r["counts"].items() if k[0] == "1") / tot
    exp = math.sin(0.5) ** 2
    assert abs(p1 - exp) < 0.03, (p1, exp)
    return f"q2 |1> p={p1:.3f} vs expected {exp:.3f}"


def check_superdense(t):
    r = run_circuit({"num_qubits": 2, "gates": t["gates"]}, shots=4096)
    top = max(r["counts"], key=lambda k: r["counts"][k])
    assert top == "11", r["counts"]
    return f"message 11 decoded ({r['counts']})"


def check_grover3(t):
    r, p = probs_of({"num_qubits": 3, "gates": t["gates"]})
    assert p.get("101", 0) > 0.75, p
    return f"|101> with p={p.get('101', 0):.3f}"


def check_swap(t):
    r, p = probs_of({"num_qubits": 2, "gates": t["gates"]})
    assert abs(p.get("10", 0) - 1.0) < 1e-6, p
    return "|10> after swap (state moved to q1)"


CHECKERS = {
    "bell": check_bell,
    "ghz": check_ghz,
    "w-state": check_w,
    "deutsch-jozsa": check_dj,
    "bernstein-vazirani": check_bv,
    "qft-3": check_qft,
    "grover-2": check_grover2,
    "qpe-2": check_qpe,
    "teleportation": check_teleport,
    "superdense-coding": check_superdense,
    "grover-3": check_grover3,
    "swap": check_swap,
}


if __name__ == "__main__":
    failed = 0
    for t in TEMPLATES:
        fn = CHECKERS.get(t["id"])
        if fn is None:
            print(f"[SKIP] {t['id']}")
            continue
        try:
            msg = fn(t)
            print(f"[PASS] {t['id']}: {msg}")
        except AssertionError as e:
            failed += 1
            print(f"[FAIL] {t['id']}: {e}")
    print("---")
    print(f"{len(TEMPLATES) - failed}/{len(TEMPLATES)} templates passed")
