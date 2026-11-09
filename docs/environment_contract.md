# Environment contract

This report applies `.claude/skills/environment_contract/SKILL.md` during the
Codex environment specialist's implementation. `src/environment.py` was restored
from `origin/main:src/environment.py` and adapted rather than rebuilt.

## Public interface

- `VacuumWorldEnv(living_cost=-0.04, seed=None)` constructs an episode simulator.
- Observations are hashable `(row, column)` integer tuples within the 4×4 grid.
- `actions` supplies the valid action labels: `N`, `E`, `S`, `W`.
- `reset(seed=None)` returns the initial observation. An explicit seed restarts
  the environment's independent random stream; omitted seeds continue it.
- `step(action)` returns `(next_state, reward, done)`. Invalid actions raise
  `ValueError`. `done=True` means a terminal was reached; reset starts a new episode.
- Calls after termination remain in the terminal with reward zero and `done=True`.
- The caller imposes a maximum episode length. Reaching that limit is truncation,
  not simulator termination, and must not be represented as a terminal transition.

## Learner-visible information

The learner receives observation tuples, action labels, sampled rewards and
termination flags. It can initialize Q-values lazily for observed states. It must
not inspect simulator internals to choose or update actions. Layout information
may be used outside the learner solely to display a policy grid.

## Private simulator details

Movement sampling, collision handling, reward assignment and terminal layout
belong to the simulator. Dependent learner implementation needs only the public
interface above, not these implementation details.

## Assumptions and blockers

- Coordinates mean `(row, column)` with row zero at the top.
- Terminal rewards replace the living reward on entry; subsequent calls yield zero.
- Boundaries and obstacles consume a step and receive the living reward.
- Fixed seed reproducibility uses local `random.Random`, independent of learner RNG.
- Existing public layout attributes are preserved for compatibility, but do not
  form part of the learner contract. No blockers remain.
