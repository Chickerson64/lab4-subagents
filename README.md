# CS440 Lab 5: Q-learning vacuum robot

A standard-library Python implementation based on the team's Lab 4 environment.
Python 3.9+ is sufficient. No installation, API key, Claude subscription, or model
call is required to train, evaluate, test, or demonstrate the hooks.

## Run

From this repository directory:

```sh
python3 -m src.train
python3 -m unittest discover -s tests -v
python3 orchestrator.py --demo-hooks
```

The first command trains from scratch and prints the learned 4×4 policy and
separate evaluation results. Optional controls:

```sh
python3 -m src.train --episodes 20000 --eval-episodes 1000 --max-steps 200 --seed 440
```

## Environment and algorithm

Coordinates are `(row, column)`, starting at the top left:

```text
START   0    0    0
  0     X    0    0
  0     0    0    0
  0    -1    0   +10
```

`src/environment.py` was restored from `origin/main:src/environment.py` (the
Lab 4 implementation), preserving its 80% intended / 10% left / 10% right
movement. Added local random seeds, validation, and absorbing terminal behavior.
Walls and the obstacle keep the robot in place and consume a step. Terminal
rewards replace the living reward on entry; further terminal steps return zero.

| Setting | Initial value |
| --- | --- |
| Living reward | −0.04 |
| Discount gamma | 0.95 |
| Learning rate alpha | 0.10 |
| Exploration epsilon | 0.10 |
| Training episodes | 20,000 |
| Evaluation episodes | 1,000 |
| Maximum steps per episode | 200 |
| Seed | 440 |

The learner initializes unseen Q-values to zero, explores uniformly with
probability epsilon, and otherwise chooses a maximum Q action with random tie
breaking. It consumes sampled `(state, action, reward, next_state, done)` only:

```text
Q(s,a) += alpha * (reward + gamma * max Q(next_state,·) - Q(s,a))
```

Terminal targets use only `reward`. A time limit is truncation, so its final
nonterminal transition still bootstraps. Environment and learner use independent
random streams. Evaluation uses a copy of the table, a separate seed, no learning,
and epsilon zero; movement still slips. The display alone knows the grid layout.
This is tabular experience-based learning, with no transition/reward model or
planning algorithm in the learner.

## Observed result

On Python 3.9.6 with the default seed, training reached +10 in 19,712/20,000
episodes. Evaluation reached +10 in 1,000/1,000, with zero negative terminals or
truncations, mean return 9.726, and mean length 7.85 steps. These are finite seeded
measurements, not a guarantee for every seed or proof of an optimal policy.
The printed arrows show the greedy policy, `S:` marks the start, `X` the obstacle,
and `-1`/`+10` the terminals.

## Three AI coding features: actual use

The compatible agent runtime used for this implementation was the existing Codex
chat. The original Claude architecture is retained as an optional adapter. No paid
API calls were made and no additional frameworks were installed.

1. **Sub-agents:** the parent delegated environment restoration to `environment`,
   learner implementation to `learner`, and independent testing/review to `review`
   using Codex's real sub-agent tools. They returned implementation and execution
   results to the parent. These were model-driven workers, not Python functions
   renamed as agents. The original role definitions remain in `.claude/subagents/`.
2. **Hooks:** `agent_hooks.py` provides shared pre-tool edit guards and post-tool /
   failure audit callbacks. The reviewer uses its audited Read tool during actual
   source inspection. `--demo-hooks` also executes this dispatch path: blocks a
   protected README write and permits a write/read in a temporary `src/` directory.
   Real JSONL events append to `artifacts/hooks.jsonl` and
   `artifacts/review-hooks.jsonl`; logs are ignored by Git. This local dispatcher
   is explicit application hook middleware, not a claim about native Codex hooks.
3. **Skills:** the environment specialist read and applied `environment-contract`
   to produce `docs/environment_contract.md`. The reviewer reads and applies
   `model-free-audit` and the completed `verification-report` procedure to inspect
   code, execute commands, and write `docs/verification_report.md`. Their reports
   record actual application; just reading a Markdown file in the demo is not
   presented as AI skill execution.

For a new live coding-feature demo, open this project in Codex and ask:

> Use real sub-agents to verify Lab 5. Have the environment specialist apply
> `.claude/skills/environment_contract/SKILL.md`, and the reviewer apply
> `.claude/skills/verification_report/SKILL.md` and
> `.claude/skills/model-free-audit/SKILL.md`. Have the reviewer read source through
> `ProjectHooks.dispatch` and show its audit log. Run the tests and training,
> report actual results, and do not commit or call paid APIs.

The Python commands alone do not launch AI sub-agents. Repeating model-driven
work requires an available Codex session (or another configured agent runtime).
The existing Codex chat contains the original delegation evidence; the checked-in
reports summarize it rather than impersonating a raw runtime transcript.

## Optional Claude adapter

`orchestrator.py --goal '...'` retains the original Claude Agent SDK workflow,
registers shared hooks, and loads `.claude/subagents/*.md`. Fixed mismatched
`Skill` tool casing, removed the reviewer's unsupported shell tool, and completed
the empty verification skill. Shell execution remains disabled in this adapter;
the parent runs tests. It needs separately installed `claude-agent-sdk`, PyYAML,
and configured Claude access. This route was **not executed against a model**:
dependency preflight reported the absent SDK. The SDK adapter is unverified here;
use the demonstrated Codex workflow and local hook command for this submission.
Do not run the optional API-backed route unless you intend to use that service.

## Structure

```text
src/environment.py       restored stochastic Lab 4 simulator
src/agent_interface.py   model-free QLearningAgent
src/train.py             training, evaluation, policy display, CLI
agent_hooks.py           reusable guards/audit and optional SDK adapter
feature_demo.py          dependency-free hook exercise
orchestrator.py          original optional Claude orchestration + hook demo
.claude/subagents/       three specialist role definitions
.claude/skills/          environment contract, model-free audit, verification
tests/                  standard-library unittest suite
docs/                   contract and actual verification report
```

## Three-minute video

- **0:00–0:35:** show the layout, stochastic motion, and four hyperparameters here.
- **0:35–1:15:** show the Codex delegations and specialist reports; open the skill
  procedures and explain their applied outputs. Show the reviewer's hook log.
- **1:15–1:40:** run `python3 orchestrator.py --demo-hooks`; show the blocked edit,
  allowed temporary edit, and `artifacts/hooks.jsonl` events.
- **1:40–2:25:** run `python3 -m src.train`; explain epsilon-greedy sampling,
  terminal Q targets, the policy arrows, and evaluation without exploration.
- **2:25–3:00:** run the unittest command, show the verification report, and explain
  that Python execution needs no API credits; the Claude adapter was not tested.
