---
name: model-free-audit
description: >-
  Review learner code for prohibited access to simulator internals,
  transition models, or reward models.
---

# Audit procedure

1. Read the task's model-free requirements and public interface contract.
2. Inspect learner imports, constructor inputs, and environment accesses.
3. Identify whether the learner:
   - Consumes sampled observations, rewards, and episode signals.
   - Reads private simulator state or implementation data.
   - Queries or constructs an explicit transition or reward model.
   - Uses environment implementation details outside the agreed contract.
4. Distinguish:
   - Observed violations.
   - Suspicious accesses requiring clarification.
   - Checks not performed.
5. Do not treat a variable name or keyword match as proof of a violation.
6. Do not claim complete isolation from source inspection alone.

# Output format

- Status: PASS, FAIL, or BLOCKED.
- Scope: files and interfaces inspected.
- Findings: file location, evidence, and impact.
- Recommended corrections.
- Limitations of the review.
