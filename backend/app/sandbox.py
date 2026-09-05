"""Sandboxed execution of user-submitted Python code.

Runs user code in a subprocess with a hard timeout, a restricted import
whitelist, and stdout/stderr capture. Used by the Code Lab and the coding
challenge checker.
"""

import os
import subprocess
import sys
import textwrap

ALLOWED_IMPORTS = {
    "qiskit", "qiskit_aer", "cirq", "numpy", "math", "cmath", "itertools",
    "collections", "pennylane", "functools", "operator", "random",
    "json", "typing", "time",
}

WRAPPER = r"""
import io, contextlib, sys, traceback

_ALLOWED = {allowed!r}
_original_import = __import__
_in_progress = set()

def _guarded_import(name, *args, **kwargs):
    base = name.split('.')[0]
    if _in_progress:
        # already inside an allowed package import (its deps are needed)
        return _original_import(name, *args, **kwargs)
    if base.startswith('_'):
        return _original_import(name, *args, **kwargs)
    if base in _ALLOWED:
        _in_progress.add(True)
        try:
            return _original_import(name, *args, **kwargs)
        finally:
            _in_progress.clear()
    raise ImportError(f"Import '{name}' is not allowed in the sandbox")

import builtins
builtins.__import__ = _guarded_import

_user_ns = {}
_out = io.StringIO()
_err = io.StringIO()
try:
    with contextlib.redirect_stdout(_out), contextlib.redirect_stderr(_err):
        exec(_CODE, _user_ns)
except Exception:
    _err.write(traceback.format_exc())

# Collect structured artifacts (e.g., a qiskit circuit named `qc`)
_artifacts = {}
try:
    from qiskit import QuantumCircuit
    qc = _user_ns.get('qc')
    if isinstance(qc, QuantumCircuit):
        _artifacts['has_qc'] = True
        _artifacts['num_qubits'] = qc.num_qubits
        _artifacts['depth'] = qc.depth()
        _artifacts['gates'] = str(sum(qc.count_ops().values()))
        _artifacts['draw'] = qc.draw(output='text').__str__()
except Exception:
    pass

print("__QSTDOUT__")
print(_out.getvalue())
print("__QSTDERR__")
print(_err.getvalue())
print("__QARTIFACTS__")
import json as _json
print(_json.dumps(_artifacts))
"""


def run_user_code(code, timeout=30):
    """Run user Python code in a sandboxed subprocess."""
    allowed_repr = ", ".join(repr(x) for x in sorted(ALLOWED_IMPORTS))
    wrapper = textwrap.dedent(WRAPPER).replace("{allowed!r}", allowed_repr)
    full_code = f"_CODE = {code!r}\n" + wrapper
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(os.path.dirname(__file__))
    try:
        proc = subprocess.run(
            [sys.executable, "-c", full_code],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd="/tmp",
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": "Execution timed out ({}s).".format(timeout),
                "artifacts": {}}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": f"Sandbox error: {e}", "artifacts": {}}

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""

    def extract(marker, next_marker):
        if marker not in stdout:
            return None
        tail = stdout.split(marker, 1)[1]
        if next_marker and next_marker in tail:
            tail = tail.split(next_marker, 1)[0]
        return tail.lstrip("\n").rstrip("\n")

    user_stdout = extract("__QSTDOUT__", "__QSTDERR__")
    user_stderr = extract("__QSTDERR__", "__QARTIFACTS__")
    artifacts_raw = extract("__QARTIFACTS__", None)
    artifacts = {}
    if artifacts_raw is not None:
        try:
            import json
            artifacts = json.loads(artifacts_raw)
        except Exception:
            artifacts = {}

    if user_stdout is None:
        # Wrapper itself failed to produce markers (unlikely).
        user_stdout = stdout
        user_stderr = stderr

    ok = user_stderr.strip() == ""
    return {
        "ok": ok,
        "stdout": (user_stdout or "").rstrip("\n"),
        "stderr": (user_stderr or "").rstrip("\n"),
        "artifacts": artifacts,
        "returncode": proc.returncode,
    }


def run_challenge_tests(cid, user_code, challenge, timeout=30):
    """Run a coding-challenge submission and return pass/fail details."""
    from .challenges import check_challenge

    full = check_challenge(cid, user_code)
    result = run_user_code(full, timeout=timeout)
    if result["stderr"]:
        return {
            "ok": False,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "passed": False,
        }
    passed = "AssertionError" not in result["stderr"] and result["ok"]
    return {
        "ok": result["ok"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "passed": passed,
    }
