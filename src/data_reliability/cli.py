from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .disaster import discover_assets
from .disaster_models import DiscoveryRequest
from .models import RunResult
from .repairs import apply_approved_repairs

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
    repair = commands.add_parser("apply-repairs")
    repair.add_argument("result", help="Path to a prior result.json")
    repair.add_argument("--approve", required=True, help="Comma-separated proposal IDs explicitly approved by a human")
    repair.add_argument("--output", required=True, help="New output path; source overwrite is forbidden")
    discover = commands.add_parser("discover-assets", help="Resolve a disaster and filter satellite candidates")
    discover.add_argument("query")
    discover.add_argument("--start", type=date.fromisoformat)
    discover.add_argument("--end", type=date.fromisoformat)
    discover.add_argument("--platforms", default="", help="Comma-separated platform names")
    discover.add_argument("--product-types", default="", help="Comma-separated product types")
    discover.add_argument("--mode", choices=["ollama", "deterministic"], default="ollama")
    discover.add_argument("--catalog")
    discover.add_argument("--gazetteer")
    discover.add_argument("--output-root", default="outputs")
    discover.add_argument("--boundary-mode", choices=["live", "offline"], default="live")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "investigate":
        result = investigate(args.path, args.goal, args.mode, args.output_root)
        print(json.dumps({"run_id": result.run_id, "findings": len(result.findings), "report": result.report_path, "trajectory": result.trajectory_path}, indent=2))
    elif args.command == "baseline":
        print(json.dumps([item.model_dump(mode="json") for item in run_baseline(args.path)], indent=2))
    elif args.command == "evaluate":
        print(json.dumps(evaluate(args.manifest, args.mode), indent=2))
    elif args.command == "apply-repairs":
        result = RunResult.model_validate_json(Path(args.result).read_text(encoding="utf-8"))
        approved = {value.strip() for value in args.approve.split(",") if value.strip()}
        repaired = apply_approved_repairs(result.profile.path, args.output, result.repair_proposals, approved)
        print(repaired.model_dump_json(indent=2))
    else:
        request = DiscoveryRequest(
            query=args.query,
            start_date=args.start,
            end_date=args.end,
            platforms=[item.strip() for item in args.platforms.split(",") if item.strip()],
            product_types=[item.strip() for item in args.product_types.split(",") if item.strip()],
        )
        kwargs = {"mode": args.mode, "output_root": args.output_root, "boundary_mode": args.boundary_mode}
        if args.catalog:
            kwargs["catalog_path"] = args.catalog
        if args.gazetteer:
            kwargs["gazetteer_path"] = args.gazetteer
        print(discover_assets(request, **kwargs).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
