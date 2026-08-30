# Agent trajectory evidence

Runtime investigation trajectories are generated under `outputs/<run-id>/trajectory.jsonl`. Before submission, copy two representative, sanitized files into this directory:

1. `deterministic-investigation.jsonl` from `make demo`.
2. `ollama-investigation.jsonl` from the same case with `--mode ollama`.

Keep the matching reports beside them when practical. Each trace should make the input goal, planner source, selected tools, tool evidence, verifier decisions, retries/fallbacks, and final output easy to follow.

The coding-agent development trace is separate from these runtime traces. Export the representative conversation or trajectory supplied by the coding tool used during the hackathon and add it as `coding-agent-development.md` or in the platform's requested native format. It should include:

- the original task and agent instructions;
- meaningful tool calls and results;
- failed approaches and corrections;
- human checkpoints or decisions;
- the final tests and resulting commit.

Sanitize all traces before publishing. Remove credentials, private URLs, personal data, machine-specific home paths, and unrelated conversation. Do not invent or rewrite a trace as if it were raw evidence.
