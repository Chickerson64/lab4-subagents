"""Train and demonstrate the vacuum robot policy; no API or packages needed."""

import argparse
from dataclasses import dataclass

from .agent_interface import QLearningAgent
from .environment import VacuumWorldEnv


@dataclass
class EpisodeStats:
    episodes: int = 0
    positive: int = 0
    negative: int = 0
    truncated: int = 0
    total_return: float = 0.0
    total_steps: int = 0

    def summary(self):
        return (f"episodes={self.episodes}, +10={self.positive} "
                f"({self.positive / self.episodes:.1%}), -1={self.negative}, "
                f"truncated={self.truncated}, mean return={self.total_return / self.episodes:.3f}, "
                f"mean steps={self.total_steps / self.episodes:.2f}")


def run_episodes(env, agent, episodes, max_steps, training=True):
    if episodes <= 0 or max_steps <= 0:
        raise ValueError("episodes and max_steps must be positive")
    stats = EpisodeStats(episodes=episodes)
    for _ in range(episodes):
        state = env.reset()
        for _ in range(max_steps):
            action = agent.select_action(state, explore=training)
            next_state, reward, done = env.step(action)
            if training:
                # A time cap is truncation, not an MDP terminal: retain bootstrap.
                agent.update(state, action, reward, next_state, done)
            stats.total_return += reward
            stats.total_steps += 1
            state = next_state
            if done:
                stats.positive += int(reward == 10.0)
                stats.negative += int(reward == -1.0)
                break
        else:
            stats.truncated += 1
    return stats


def policy_grid(agent):
    """Presentation uses the assignment layout; learner never sees this map."""
    arrows = {"N": "↑", "E": "→", "S": "↓", "W": "←"}
    special = {(1, 1): "X", (3, 1): "-1", (3, 3): "+10"}
    rows = []
    for row in range(4):
        cells = []
        for col in range(4):
            state = (row, col)
            if state in special:
                label = special[state]
            else:
                values = agent.values(state)
                # Stable display tie break; action selection itself randomizes ties.
                label = arrows[max(agent.actions, key=values.get)]
                if state == (0, 0):
                    label = "S:" + label
            cells.append(f"{label:^5}")
        rows.append(" | ".join(cells))
    return "\n".join(rows)


def train(episodes=20000, eval_episodes=1000, max_steps=200, seed=440):
    agent = QLearningAgent(seed=seed + 1)
    training = run_episodes(VacuumWorldEnv(living_cost=-0.04, seed=seed),
                            agent, episodes, max_steps)
    # Separate action RNG and environment RNG make evaluation independent of
    # training's random stream, without changing the learned table.
    evaluator = QLearningAgent(epsilon=0.0, seed=seed + 3)
    evaluator.q = {s: dict(v) for s, v in agent.q.items()}
    evaluation = run_episodes(VacuumWorldEnv(living_cost=-0.04, seed=seed + 2),
                              evaluator, eval_episodes, max_steps, training=False)
    return agent, training, evaluation


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=positive_int, default=20000)
    parser.add_argument("--eval-episodes", type=positive_int, default=1000)
    parser.add_argument("--max-steps", type=positive_int, default=200)
    parser.add_argument("--seed", type=int, default=440)
    args = parser.parse_args()
    agent, training, evaluation = train(args.episodes, args.eval_episodes,
                                        args.max_steps, args.seed)
    print(f"seed={args.seed}, living reward=-0.04, gamma=0.95, alpha=0.10, epsilon=0.10")
    print("Training:   " + training.summary())
    print("Learned policy (S=start, X=obstacle):")
    print(policy_grid(agent))
    print("Evaluation (epsilon=0; movement remains stochastic): " + evaluation.summary())


if __name__ == "__main__":
    main()
