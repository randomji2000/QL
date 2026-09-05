"""Per-user progress tracking with a JSON-file backend."""

import json
import os
import threading
import time
import uuid

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")

_lock = threading.Lock()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "w") as f:
            json.dump({}, f)


def _load():
    _ensure()
    try:
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data):
    _ensure()
    tmp = PROGRESS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, PROGRESS_FILE)


def get_user(user_id):
    with _lock:
        data = _load()
        return data.get(user_id, _blank(user_id))


def _blank(user_id):
    return {
        "user_id": user_id,
        "completed_lessons": [],
        "quiz_scores": {},
        "challenges": {},
        "simulations": 0,
        "circuits_built": 0,
        "templates_used": [],
        "xp": 0,
        "created_at": time.time(),
        "last_active": time.time(),
    }


def touch(user_id, **fields):
    with _lock:
        data = _load()
        rec = data.get(user_id)
        if rec is None:
            rec = _blank(user_id)
        rec.update(fields)
        rec["last_active"] = time.time()
        data[user_id] = rec
        _save(data)
        return rec


def record_activity(user_id, activity_type, payload=None):
    with _lock:
        data = _load()
        rec = data.get(user_id) or _blank(user_id)
        if activity_type == "lesson":
            lid = payload.get("lesson_id")
            if lid and lid not in rec["completed_lessons"]:
                rec["completed_lessons"].append(lid)
                rec["xp"] += 20
        elif activity_type == "quiz":
            qid = payload.get("quiz_id")
            score = payload.get("score", 0)
            old = rec["quiz_scores"].get(qid)
            if old is None or score > old:
                rec["quiz_scores"][qid] = score
                rec["xp"] += 30
        elif activity_type == "challenge":
            cid = payload.get("challenge_id")
            if not rec["challenges"].get(cid):
                rec["challenges"][cid] = {"passed": True, "ts": time.time()}
                rec["xp"] += 50
        elif activity_type == "simulation":
            rec["simulations"] = rec.get("simulations", 0) + 1
        elif activity_type == "circuit":
            rec["circuits_built"] = rec.get("circuits_built", 0) + 1
        rec["last_active"] = time.time()
        data[user_id] = rec
        _save(data)
        return rec


def all_users():
    with _lock:
        data = _load()
        return data


def dashboard_stats():
    """Aggregate analytics for the instructor dashboard."""
    with _lock:
        data = _load()
    total_users = len(data)
    completed_lessons = 0
    simulations = 0
    circuits_built = 0
    xp_total = 0
    quiz_attempts = 0
    quiz_scores = []
    challenges_passed = 0
    per_module = {}
    for rec in data.values():
        completed_lessons += len(rec.get("completed_lessons", []))
        simulations += rec.get("simulations", 0)
        circuits_built += rec.get("circuits_built", 0)
        xp_total += rec.get("xp", 0)
        for qid, sc in rec.get("quiz_scores", {}).items():
            quiz_attempts += 1
            quiz_scores.append(sc)
        challenges_passed += len(rec.get("challenges", {}))
        for lid in rec.get("completed_lessons", []):
            mod = lid.split("-")[0]
            per_module[mod] = per_module.get(mod, 0) + 1
    return {
        "total_users": total_users,
        "total_lessons_completed": completed_lessons,
        "total_simulations": simulations,
        "total_circuits_built": circuits_built,
        "total_xp": xp_total,
        "total_quiz_attempts": quiz_attempts,
        "avg_quiz_score": round(sum(quiz_scores) / len(quiz_scores), 1) if quiz_scores else 0,
        "total_challenges_passed": challenges_passed,
        "module_completions": dict(sorted(per_module.items())),
        "active_today": sum(1 for r in data.values()
                            if time.time() - r.get("last_active", 0) < 86400),
    }


def new_user_id():
    return "user-" + uuid.uuid4().hex[:8]
