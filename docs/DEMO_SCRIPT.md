# Five-minute submission video script

Target length: 4:30–4:50. Record at 1080p and enlarge terminal text before starting.

## 0:00–0:35 — user and bottleneck

Show the README title and say:

> Disaster-data analysts must decide whether unfamiliar tables and satellite metadata are usable. Manual checks are inconsistent, while unconstrained AI can produce plausible but unsupported claims. GeoReliability lets a local model plan an investigation, but deterministic tools and an independent verifier control the evidence.

## 0:35–1:05 — fair baseline

Run `make baseline`, then show `EVALUATION.md`. Explain that the baseline checks missing cells and exact duplicate rows. On the same 11 synthetic cases, it reaches 0.333 F1, while the advanced workflow reaches 1.000. State clearly that this is a controlled regression benchmark, not real-world accuracy.

## 1:05–2:05 — realistic end-to-end investigation

Run `make demo`. Open the generated report and trajectory. Point out the user goal, selected allowlisted checks, calculated evidence, verifier decision, and bounded repair proposals. Emphasize that the model never writes or executes analysis code.

## 2:05–3:30 — geospatial extension

Start `make web` before recording this segment. Search:

```text
August 2022 floods near Sukkur and Larkana, Pakistan
```

Show automatic map fit, administrative/fallback provenance, water overlay, the single dual-handle timeline, platform toggles, political-overlap `/` texture, radius-overlap `\` texture, and scene metadata. Download the evidence report. Explicitly say that satellite filenames and footprints are illustrative planning candidates rather than verified provider results.

## 3:30–4:05 — safety and human control

Show `AGENT_INSTRUCTIONS.md` and the repair command in the README. Explain that investigation is read-only, factual claims require accepted evidence, repairs are allowlisted, exact proposal IDs require human approval, and the original source cannot be overwritten.

## 4:05–4:35 — iteration evidence

Show `IMPROVEMENT_CHANGELOG.md`. Name the biggest improvement: separating model planning from deterministic evidence and verification. Name one constrained experiment: automatic repairs were moved behind explicit approval because silent mutation was too risky.

## 4:35–4:50 — limitation and hot take

Say:

> The main failure mode is missing domain context: structural anomalies do not prove a value is wrong. My hot take is that a reliable agent should have less authority than its tools, not more.

End on the map or repository URL.

## Before recording

- Run `make submission-check`.
- Use deterministic mode for the recorded core run; demonstrate Ollama separately only if latency is stable.
- Preload map tiles and the live boundary once, but keep fallback labels visible if the provider is unavailable.
- Close notifications and hide usernames, local paths, tokens, and browser bookmarks.
- Do one uninterrupted rehearsal and keep the final export below five minutes.
