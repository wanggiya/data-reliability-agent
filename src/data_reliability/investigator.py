from __future__ import annotations

import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen

from .models import CheckName, DatasetProfile, InvestigationPlan


CORE_CHECKS = [
    CheckName.missing_values,
    CheckName.duplicate_rows,
    CheckName.negative_values,
    CheckName.suspicious_zeros,
    CheckName.numeric_outliers,
    CheckName.category_inconsistency,
]


def deterministic_plan(profile: DatasetProfile, goal: str) -> InvestigationPlan:
    checks = list(CORE_CHECKS)
    if profile.id_candidates:
        checks.append(CheckName.duplicate_ids)
    if profile.date_candidates:
        checks.append(CheckName.date_gaps)
    lower = {c.lower() for c in profile.column_names}
    if "total" in lower and len(profile.numeric_columns) >= 3:
        checks.append(CheckName.total_reconciliation)
    rationale = {check.value: "Selected from dataset schema and the user's reliability goal." for check in checks}
    return InvestigationPlan(goal=goal, checks=checks, rationale=rationale, source="deterministic")


def ollama_plan(profile: DatasetProfile, goal: str, model: str | None = None, base_url: str | None = None) -> InvestigationPlan:
    model = model or os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
    allowed = [item.value for item in CheckName]
    prompt = (
        "You are a cautious data-quality investigator. Select checks for the supplied dataset. "
        "Return JSON only with keys checks (array) and rationale (object). "
        f"Allowed checks: {allowed}. Goal: {goal}. Profile: {profile.model_dump_json(exclude={'sample'})}"
    )
    request = Request(
        f"{base_url}/api/generate",
        data=json.dumps({"model": model, "prompt": prompt, "stream": False, "format": "json"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        ollama_timeout = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "5"))
        with urlopen(request, timeout=ollama_timeout) as response:
            envelope = json.loads(response.read().decode())
        payload = json.loads(envelope["response"])
        checks = list(dict.fromkeys(CheckName(value) for value in payload["checks"]))
        if not checks:
            raise ValueError("Ollama returned an empty plan")
        return InvestigationPlan(goal=goal, checks=checks, rationale=payload.get("rationale", {}), source=f"ollama:{model}")
    except (URLError, TimeoutError, KeyError, ValueError, json.JSONDecodeError) as exc:
        fallback = deterministic_plan(profile, goal)
        fallback.source = f"deterministic-fallback:{type(exc).__name__}"
        return fallback


def create_plan(profile: DatasetProfile, goal: str, mode: str = "ollama") -> InvestigationPlan:
    return ollama_plan(profile, goal) if mode == "ollama" else deterministic_plan(profile, goal)
