---
name: verification-report
description: Verify the Lab 5 implementation and report executed tests, model-free review findings, and feature evidence.
---

# Verification report

Read `docs/environment_contract.md` and inspect the implementation before testing.
Run `python3 -m unittest discover -s tests -v`, `python3 -m src.train`, and
`python3 feature_demo.py` from the repository root. Record actual commands,
exit status, test totals, evaluation metrics, and limitations; never infer success
from source code alone. Apply `.claude/skills/model-free-audit/SKILL.md` to the
learner. Check terminal targets, slip, blocked movement, seeded reproducibility,
truncation, and exploration-free evaluation.

Write `docs/verification_report.md` with PASS/FAIL/BLOCKED findings, files inspected,
actual results, and unresolved issues. Distinguish real Codex sub-agent work from
the deterministic hook demonstration. Identify which skills were read and applied.
Do not call paid APIs or claim the optional Claude runtime was exercised.
