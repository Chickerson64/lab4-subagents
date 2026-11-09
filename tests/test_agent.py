import copy
import unittest

from src.agent_interface import QLearningAgent
from src.train import run_episodes, train


class AgentTests(unittest.TestCase):
    def test_standard_update(self):
        agent = QLearningAgent()
        agent.values("next")["N"] = 4
        self.assertAlmostEqual(agent.update("state", "E", 1, "next", False), .48)

    def test_terminal_has_no_bootstrap(self):
        agent = QLearningAgent()
        agent.values("terminal")["N"] = 1000
        self.assertEqual(agent.update("state", "E", -1, "terminal", True), -.1)

    def test_exploration_and_ties(self):
        explorer = QLearningAgent(epsilon=1, seed=3)
        explorer.values("state")["N"] = 100
        self.assertEqual(set(explorer.select_action("state") for _ in range(100)),
                         set(explorer.actions))
        greedy = QLearningAgent(epsilon=0, seed=3)
        self.assertEqual(set(greedy.select_action("state") for _ in range(100)),
                         set(greedy.actions))
        greedy.values("state")["E"] = 1
        self.assertEqual({greedy.select_action("state") for _ in range(100)}, {"E"})

    def test_model_free_fake_env_and_evaluation(self):
        class SampleOnlyEnv:
            def reset(self):
                return "opaque observation"

            def step(self, action):
                return "end", 10.0, True

        agent = QLearningAgent(seed=1)
        stats = run_episodes(SampleOnlyEnv(), agent, 20, 3)
        self.assertEqual(stats.positive, 20)
        before = copy.deepcopy(agent.q)
        run_episodes(SampleOnlyEnv(), agent, 20, 3, training=False)
        self.assertEqual(agent.q, before)

    def test_truncation_keeps_bootstrap(self):
        class NonterminalEnv:
            def reset(self):
                return "start"

            def step(self, action):
                return "next", 0.0, False

        agent = QLearningAgent(seed=1)
        agent.values("next")["N"] = 10
        stats = run_episodes(NonterminalEnv(), agent, 1, 1)
        self.assertEqual(stats.truncated, 1)
        self.assertAlmostEqual(max(agent.q["start"].values()), .95)

    def test_reproducibility_and_learned_behavior(self):
        agent, training, evaluation = train()
        again, training_again, evaluation_again = train()
        self.assertEqual(agent.q, again.q)
        self.assertEqual(training, training_again)
        self.assertEqual(evaluation, evaluation_again)
        self.assertGreaterEqual(evaluation.positive, 950)
        self.assertEqual(evaluation.truncated, 0)

    def test_invalid_parameters(self):
        for kwargs in ({"alpha": -1}, {"epsilon": 2}, {"gamma": float("nan")},
                       {"actions": []}, {"actions": ["N", "N"]}):
            with self.assertRaises(ValueError):
                QLearningAgent(**kwargs)


if __name__ == "__main__":
    unittest.main()
