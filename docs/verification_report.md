# Lab 5 verification report

The independent Codex reviewer read and applied
`.claude/skills/verification_report/SKILL.md` and
`.claude/skills/model-free-audit/SKILL.md`, using the public contract in
`docs/environment_contract.md`. This report records execution, not just source review.

## Scope and model-free audit

**PASS:** `src/agent_interface.py` consumes abstract hashable states, action labels,
sampled rewards and termination flags. It imports only `math` and `random`.
It neither receives the environment object nor accesses a transition/reward model.
Q-values begin at zero on first observation. The update matches
`Q += alpha * (reward + gamma * max_next_Q - Q)`, with no next-state bootstrap
for true terminal transitions. Ties are randomized and exploration is epsilon-greedy.

`src/train.py` uses `reset()` and `step()` for experience. Its policy renderer
contains the assignment's layout for display only. Reward comparisons in metrics
classify observed outcomes; they do not influence learning. Truncation retains the
bootstrap term. Evaluation makes no learning updates and uses a separate copy of
the learned table plus independent environment/action random streams.

Tests also exercise the runner with an opaque sample-only fake environment.
Source review and these tests support the model-free claim; they do not constitute
a formal proof of isolation against arbitrary future modifications.

## Executed commands and results

All commands ran from the repository root with Python 3.9.6, using only the standard
library for the learner, simulator, tests and hook demo.

- `python3 -m src.train`: exit 0. Seed 440; 20,000 training episodes, 19,712 positive
  terminals, 288 negative terminals, zero truncations, mean return 9.532 and mean
  episode length 8.73. Evaluation: 1,000/1,000 positive terminals, zero negative
  terminals/truncations, mean return 9.726, mean length 7.85. Movement remains
  stochastic during epsilon-zero evaluation. These are fixed-seed measurements,
  not a guarantee of perfect success for all seeds or proof of convergence.
- `python3 feature_demo.py`: exit 0. Audited skill read, blocked protected README
  write, permitted temporary `src/` write/read, and post/failure audit events.
- `python3 orchestrator.py --demo-hooks`: exit 0 without Claude SDK or PyYAML.
- `python3 orchestrator.py --goal 'review only'`: expected exit 1 because the
  optional Claude SDK is absent. No Claude API request was made.

## Feature evidence

- **Sub-agents:** actual Codex environment, learner and independent reviewer
  sub-agents performed implementation/review in this chat. This report was written
  by the reviewer. The chat's agent/tool history is the primary execution evidence.
  `feature_demo.py` does not impersonate a model or count as sub-agent execution.
- **Hooks:** the reviewer used `ProjectHooks.dispatch('Read', ...)` to inspect the
  two skills and learner source; actual pre/post records are in
  `artifacts/review-hooks.jsonl`. The shared guard/audit callbacks were also
  exercised by the local demo and integration tests, including a blocked write.
  These are explicit tool-wrapper hooks, not globally installed Codex hooks.
- **Skills:** environment-contract was applied by the environment specialist;
  model-free-audit and verification-report were read and applied by this reviewer.
  Merely loading a skill file in the hook demo is not itself counted as applying
  that skill. These are repository instructions explicitly used by Codex agents;
  no automatic Claude skill discovery is claimed.

## Findings and limitations

Independent review found that resolving an allowed `src/` root through a symlink
could let the optional SDK guard approve an external path. A regression test
confirmed the defect before correction. Final regression results are recorded below.
The optional Claude adapter and configuration are preserved and improved, but no
SDK execution was tested. Tool names are now consistently `Skill`; the unsupported
reviewer `Bash` permission was removed, and hooks are registered in the orchestrator.

## Final regression result

**PASS:** `python3 -m unittest discover -s tests -v` exited 0: **21 tests passed**.
The final run covered exact Q updates, terminal targets, epsilon exploration and
greedy ties, opaque environment integration, evaluation without learning,
truncation bootstrapping, repeatable training and learned behavior, simulator
layout/slip/collisions/terminal absorption/seeding, hook allowed/denied paths,
traversal, nested and root symlink escape, missing-read audit, and both demo entry
points. The symlink guard regression now passes after the parent added root
containment and fail-closed resolution. `git diff --check` also exited 0.

The README commands, measured results, feature distinctions and video outline
were inspected and agree with the executed implementation. No remaining defect
was identified in the standard-library submission path. The optional Claude
adapter remains unverified against an installed SDK/model, as disclosed above.
