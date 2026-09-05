"""Gate definitions and unitary matrices for the quantum circuit simulator.

Each gate entry describes:
  - aliases: accepted names in the circuit JSON
  - arity: number of target qubits
  - supports_controls: whether the gate can be controlled (CNOT, CZ, Toffoli...)
  - matrix(angle=None): returns the base 2x2 (or larger) unitary in the
    computational basis.

Angles are in radians.
"""

import cmath
import math

import numpy as np

I2 = np.eye(2, dtype=complex)

# Pauli matrices
X_M = np.array([[0, 1], [1, 0]], dtype=complex)
Y_M = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z_M = np.array([[1, 0], [0, -1]], dtype=complex)

H_M = (1 / math.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)
S_M = np.array([[1, 0], [0, 1j]], dtype=complex)
SDG_M = np.conj(S_M).T
T_M = np.array([[1, 0], [0, cmath.exp(1j * math.pi / 4)]], dtype=complex)
TDG_M = np.conj(T_M).T


def _phase(theta):
    return np.array([[1, 0], [0, cmath.exp(1j * theta)]], dtype=complex)


def _u1(theta):
    return _phase(theta)


def _u2(phi, lam):
    v = 1 / math.sqrt(2)
    return np.array(
        [[v, -cmath.exp(1j * lam) * v], [cmath.exp(1j * phi) * v, cmath.exp(1j * (phi + lam)) * v]],
        dtype=complex,
    )


def _u3(theta, phi, lam):
    ct = math.cos(theta / 2)
    st = math.sin(theta / 2)
    return np.array(
        [
            [ct, -cmath.exp(1j * lam) * st],
            [cmath.exp(1j * phi) * st, cmath.exp(1j * (phi + lam)) * ct],
        ],
        dtype=complex,
    )


def _rx(theta):
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)


def _ry(theta):
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return np.array([[c, -s], [s, c]], dtype=complex)


def _rz(theta):
    return np.array([[cmath.exp(-1j * theta / 2), 0], [0, cmath.exp(1j * theta / 2)]], dtype=complex)


def _swap():
    return np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=complex)


def _iswap():
    return np.array(
        [[1, 0, 0, 0], [0, 0, 1j, 0], [0, 1j, 0, 0], [0, 0, 0, 1]], dtype=complex
    )


def _cphase(theta):
    return np.array(
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, cmath.exp(1j * theta)]],
        dtype=complex,
    )


def _ch():
    v = 1 / math.sqrt(2)
    return np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, v, v], [0, 0, v, -v]], dtype=complex)


def _crx(theta):
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return np.array(
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, c, -1j * s], [0, 0, -1j * s, c]], dtype=complex
    )


def _cry(theta):
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, c, -s], [0, 0, s, c]], dtype=complex)


def _crz(theta):
    return np.array(
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, cmath.exp(-1j * theta / 2), 0],
         [0, 0, 0, cmath.exp(1j * theta / 2)]],
        dtype=complex,
    )


def _cy():
    m = np.eye(4, dtype=complex)
    m[1, 1], m[2, 2], m[1, 2], m[2, 1] = 0, 0, -1j, 1j
    return m


def _cz():
    return np.diag([1, 1, 1, -1]).astype(complex)


def _ccx():
    m = np.eye(8, dtype=complex)
    m[6, 6], m[7, 7], m[6, 7], m[7, 6] = 0, 0, 1, 1
    return m


def _cswap():
    m = np.eye(8, dtype=complex)
    m[5, 5], m[6, 6], m[5, 6], m[6, 5] = 0, 0, 1, 1
    return m


GATE_DEFS = {
    "h": {"aliases": ["h", "hadamard"], "arity": 1, "controls": True, "matrix": lambda a=None: H_M},
    "x": {"aliases": ["x", "not"], "arity": 1, "controls": True, "matrix": lambda a=None: X_M},
    "y": {"aliases": ["y"], "arity": 1, "controls": True, "matrix": lambda a=None: Y_M},
    "z": {"aliases": ["z"], "arity": 1, "controls": True, "matrix": lambda a=None: Z_M},
    "s": {"aliases": ["s"], "arity": 1, "controls": True, "matrix": lambda a=None: S_M},
    "sdg": {"aliases": ["sdg", "s†", "s_dg"], "arity": 1, "controls": True, "matrix": lambda a=None: SDG_M},
    "t": {"aliases": ["t"], "arity": 1, "controls": True, "matrix": lambda a=None: T_M},
    "tdg": {"aliases": ["tdg", "t†", "t_dg"], "arity": 1, "controls": True, "matrix": lambda a=None: TDG_M},
    "p": {"aliases": ["p", "phase", "cp"], "arity": 1, "controls": True, "matrix": lambda a=None: _phase(a or 0)},
    "u1": {"aliases": ["u1"], "arity": 1, "controls": True, "matrix": lambda a=None: _u1(a or 0)},
    "u2": {"aliases": ["u2"], "arity": 1, "controls": True, "matrix": lambda a=None: _u2((a or [0, 0])[0], (a or [0, 0])[1])},
    "u3": {"aliases": ["u3", "u"], "arity": 1, "controls": True, "matrix": lambda a=None: _u3((a or [0, 0, 0])[0], (a or [0, 0, 0])[1], (a or [0, 0, 0])[2])},
    "rx": {"aliases": ["rx"], "arity": 1, "controls": True, "matrix": lambda a=None: _rx(a or 0)},
    "ry": {"aliases": ["ry"], "arity": 1, "controls": True, "matrix": lambda a=None: _ry(a or 0)},
    "rz": {"aliases": ["rz"], "arity": 1, "controls": True, "matrix": lambda a=None: _rz(a or 0)},
    "swap": {"aliases": ["swap"], "arity": 2, "controls": True, "matrix": lambda a=None: _swap()},
    "iswap": {"aliases": ["iswap", "swap"], "arity": 2, "controls": True, "matrix": lambda a=None: _iswap()},
    "cy": {"aliases": ["cy"], "arity": 1, "controls": True, "matrix": lambda a=None: _cy()},
    "cz": {"aliases": ["cz"], "arity": 1, "controls": True, "matrix": lambda a=None: _cz()},
    "cx": {"aliases": ["cx", "cnot"], "arity": 1, "controls": True, "matrix": lambda a=None: controlled_matrix(X_M, 1)},
    "ccx": {"aliases": ["ccx", "toffoli", "ccnot"], "arity": 1, "controls": True, "matrix": lambda a=None: _ccx()},
    "cswap": {"aliases": ["cswap", "fredkin"], "arity": 2, "controls": True, "matrix": lambda a=None: _cswap()},
    "ch": {"aliases": ["ch"], "arity": 1, "controls": True, "matrix": lambda a=None: _ch()},
    "crx": {"aliases": ["crx"], "arity": 1, "controls": True, "matrix": lambda a=None: _crx(a or 0)},
    "cry": {"aliases": ["cry"], "arity": 1, "controls": True, "matrix": lambda a=None: _cry(a or 0)},
    "crz": {"aliases": ["crz"], "arity": 1, "controls": True, "matrix": lambda a=None: _crz(a or 0)},
    "crp": {"aliases": ["crp", "cphase"], "arity": 1, "controls": True, "matrix": lambda a=None: _cphase(a or 0)},
    "barrier": {"aliases": ["barrier"], "arity": 0, "controls": False, "matrix": None},
    "measure": {"aliases": ["measure"], "arity": 1, "controls": False, "matrix": None},
    "reset": {"aliases": ["reset"], "arity": 1, "controls": False, "matrix": None},
}

# Gates whose matrix already spans every wire (controls included).
PRECONTROLLED = {"ccx", "cswap", "ch", "crx", "cry", "crz", "crp", "cz", "cy", "cx"}

# Gates whose matrix already spans every wire (controls included).
PRECONTROLLED = {"ccx", "cswap", "ch", "crx", "cry", "crz", "crp", "cz", "cy", "cx"}

# Map every alias to its canonical name
CANONICAL = {}
for canon, d in GATE_DEFS.items():
    for a in d["aliases"]:
        CANONICAL[a] = canon

CANONICAL.setdefault("cnot", "cx")
CANONICAL.setdefault("toffoli", "ccx")
CANONICAL.setdefault("fredkin", "cswap")
CANONICAL.setdefault("swap", "swap")

CONTROLLED_PAULIS = {"cx": X_M, "cy": Y_M, "cz": Z_M}


def lookup(name):
    """Return canonical gate name (lowercased, alias-resolved) or None."""
    if name is None:
        return None
    key = str(name).lower().replace("_", "").replace(" ", "")
    # handle dagger aliases like sdg/tag from 'sdg'
    return CANONICAL.get(key)


def controlled_matrix(base, num_controls=1):
    """Build a controlled-unitary matrix from a base square unitary."""
    base = np.asarray(base, dtype=complex)
    size = base.shape[0]
    total = (2 ** num_controls) * size
    m = np.eye(total, dtype=complex)
    start = total - size
    m[start:, start:] = base
    return m


def gate_matrix(canon, params=None):
    """Return the (possibly controlled) unitary for a gate on its wires."""
    if canon in ("barrier", "measure", "reset"):
        return None
    d = GATE_DEFS[canon]
    if isinstance(params, (list, tuple)):
        if len(params) == 1:
            params = params[0]
        else:
            params = list(params)
    return d["matrix"](params)
