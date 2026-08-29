from __future__ import annotations

import uuid
from pathlib import Path

from .checks import execute_plan
from .investigator import create_plan
from .models import RunResult
from .profiler import profile_dataset
from .reporting import write_markdown
from .trajectory import TrajectoryWriter
from .verifier import verify_evidence


def investigate(path: str | Path, goal: str, mode: str = "ollama", output_root: str | Path = "outputs") -> RunResult:
    run_id = uuid.uuid4().hex[:12]
    run_dir = Path(output_root) / run_id
    trajectory_path = run_dir / "trajectory.jsonl"
    report_path = run_dir / "report.md"
    trajectory = TrajectoryWriter(trajectory_path, run_id)

    trajectory.write("input_received", "orchestrator", {"path": str(path), "goal": goal, "mode": mode})
    frame, profile = profile_dataset(path)
    trajectory.write("profile_completed", "profiler", profile.model_dump(exclude={"sample"}))

    plan = create_plan(profile, goal, mode)
    trajectory.write("plan_created", "investigator", plan.model_dump(mode="json"))

    evidence = execute_plan(plan.checks, frame, profile)
    trajectory.write("tools_completed", "executor", {"evidence": [item.model_dump(mode="json") for item in evidence]})

    findings, verification = verify_evidence(evidence)
    trajectory.write("verification_completed", "verifier", {"summary": verification.model_dump(), "accepted": [item.model_dump(mode="json") for item in findings]})

    result = RunResult(
        run_id=run_id,
        profile=profile,
        plan=plan,
        findings=findings,
        verification=verification,
        report_path=str(report_path),
        trajectory_path=str(trajectory_path),
    )
    write_markdown(result, report_path)
    (run_dir / "result.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
    trajectory.write("run_completed", "orchestrator", {"report_path": str(report_path)})
    return result

