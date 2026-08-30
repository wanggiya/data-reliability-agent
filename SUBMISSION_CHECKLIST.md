# Submission checklist

## Code and evidence

- [ ] `make submission-check` passes from a clean environment.
- [ ] `make evaluate` output is saved under `results/`.
- [ ] One real Ollama trajectory is copied to `trajectories/`.
- [ ] One deterministic trajectory is copied to `trajectories/`.
- [ ] The final report contains no private paths, credentials, or personal data.
- [ ] The README names the user, bottleneck, baseline and value.
- [ ] Improvement Changelog records a removed or constrained experiment.
- [ ] Satellite candidates, fallback polygons, and affected-area radius remain labeled illustrative/planning-only.

## Reproduction

- [ ] Test `pip install -e '.[all]'` in a fresh virtual environment.
- [ ] Test `docker compose up --build`.
- [ ] Record Python, Ollama and model versions.
- [ ] Record approximate runtime and cost.
- [ ] Verify fallback behavior with Ollama stopped.

## Five-minute video

- [ ] 0:00–0:30: user and bottleneck.
- [ ] 0:30–1:00: baseline limitations.
- [ ] 1:00–2:30: realistic investigation in Streamlit.
- [ ] 2:30–3:15: evidence and verifier.
- [ ] 3:15–4:00: human-approved repaired copy.
- [ ] 4:00–4:35: benchmark comparison and changelog.
- [ ] 4:35–5:00: failure mode and hot take.
- [ ] Final exported duration is five minutes or less.

## Submission package

- [ ] Repository URL and archive are accessible.
- [ ] Project source license is deliberately selected and added, or the absence of a reuse license is intentional.
- [ ] Demo video is no longer than five minutes.
- [ ] Representative trajectories exist for every logical agent role.
- [ ] No `.env`, API keys, model files, private datasets or personal identifiers are committed.
- [ ] Final commit hash and release tag are recorded.
- [ ] Repository is public and the exact submission commit is accessible in an incognito window.
- [ ] Hackathon form contains repository URL, video URL, reproduction entry point, and coding-agent trajectory evidence.
