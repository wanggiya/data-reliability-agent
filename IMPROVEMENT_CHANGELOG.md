# Improvement Changelog

| Stage | What was tried and why | Evidence | Decision / learning |
|---|---|---|---|
| Baseline | Missing-value and exact-duplicate script as a reasonable basic inspection | Run `make baseline` and record benchmark metrics | Establishes the starting point |
| Iteration 1 | Added deterministic profiling and a controlled check catalog | Unit tests and benchmark output | Keep; factual evidence should come from code |
| Iteration 2 | Added Ollama planning so checks respond to schema and user goal | Planning source recorded in trajectory | Keep with deterministic fallback |
| Iteration 3 | Added independent evidence-contract verification | Accepted/rejected counts in every report | Keep; prevents unsupported claims reaching the report |
| Final Day 1 | Combined planner, tools, verifier, report, and trace into one CLI execution | `make test`, `make demo`, `make evaluate` | Complete vertical slice; expand formats and benchmark next |

## Main failure mode

Without a user-supplied data contract, the workflow can detect structural anomalies but cannot always determine whether a surprising value is genuinely incorrect.

## Hot take

The most reliable data agent is not the one allowed to write arbitrary analysis code. It is the one that chooses from transparent tools while deterministic evidence and an independent verifier control what becomes a factual claim.
