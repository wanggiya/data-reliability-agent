from __future__ import annotations

import argparse
import json

from .baseline import run_baseline
from .evaluation import evaluate
from .orchestrator import investigate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="data-reliability", description="Evidence-first data reliability investigation")
    commands = parser.add_subparsers(dest="command", required=True)
    inv = commands.add_parser("investigate")
    inv.add_argument("path")
    inv.add_argument("--goal", default="Determine whether this dataset is reliable for analysis")
    inv.add_argument("--mode", choices=["ollama", "deterministic"], default="ollama")
    inv.add_argument("--output-root", default="outputs")
    base = commands.add_parser("baseline")
    base.add_argument("path")
    ev = commands.add_parser("evaluate")
    ev.add_argument("manifest")
    ev.add_argument("--mode", choices=["ollama", "deterministic"], default="deterministic")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "investigate":
        result = investigate(args.path, args.goal, args.mode, args.output_root)
        print(json.dumps({"run_id": result.run_id, "findings": len(result.findings), "report": result.report_path, "trajectory": result.trajectory_path}, indent=2))
    elif args.command == "baseline":
        print(json.dumps([item.model_dump(mode="json") for item in run_baseline(args.path)], indent=2))
    else:
        print(json.dumps(evaluate(args.manifest, args.mode), indent=2))


if __name__ == "__main__":
    main()

