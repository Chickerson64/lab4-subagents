"""Tabular Q-learning using only sampled experience and abstract states."""

import math
import random


class QLearningAgent:
    def __init__(self, actions=("N", "E", "S", "W"), alpha=0.10,
                 gamma=0.95, epsilon=0.10, seed=0):
        self.actions = tuple(actions)
        if not self.actions or len(set(self.actions)) != len(self.actions):
            raise ValueError("actions must be nonempty and unique")
        for name, value in (("alpha", alpha), ("gamma", gamma), ("epsilon", epsilon)):
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        self.alpha, self.gamma, self.epsilon = alpha, gamma, epsilon
        self.rng = random.Random(seed)
        self.q = {}

    def values(self, state):
        """Unvisited states have zero action values (allocated on demand)."""
        return self.q.setdefault(state, dict.fromkeys(self.actions, 0.0))

    def select_action(self, state, explore=True):
        if explore and self.rng.random() < self.epsilon:
            return self.rng.choice(self.actions)
        values = self.values(state)
        best = max(values.values())
        return self.rng.choice([a for a in self.actions if values[a] == best])

    def update(self, state, action, reward, next_state, done):
        """Terminal transitions have no bootstrap term."""
        if action not in self.actions:
            raise ValueError("unknown action")
        values = self.values(state)
        target = reward if done else reward + self.gamma * max(self.values(next_state).values())
        values[action] += self.alpha * (target - values[action])
        return values[action]
