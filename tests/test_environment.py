import random
import unittest
from unittest.mock import Mock

from src.environment import VacuumWorldEnv


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.env = VacuumWorldEnv(seed=440)

    def force_roll(self, roll):
        self.env._rng = Mock()
        self.env._rng.random.return_value = roll

    def test_reset_and_layout(self):
        self.assertEqual(self.env.reset(), (0, 0))
        self.assertEqual((self.env.rows, self.env.cols), (4, 4))
        self.assertEqual(self.env.obstacle, (1, 1))
        self.assertEqual(self.env.trap, (3, 1))
        self.assertEqual(self.env.recharge, (3, 3))

    def test_slip_intervals_and_turns(self):
        for action, left, right in [('N', 'W', 'E'), ('E', 'N', 'S'),
                                     ('S', 'E', 'W'), ('W', 'S', 'N')]:
            for roll, expected in [(0, action), (.799999, action), (.8, left),
                                   (.899999, left), (.9, right), (.999999, right)]:
                with self.subTest(action=action, roll=roll):
                    self.force_roll(roll)
                    self.assertEqual(self.env._get_stochastic_action(action), expected)

    def test_boundaries_and_obstacle(self):
        self.force_roll(0)
        for state, action in [((0, 0), 'N'), ((0, 0), 'W'), ((3, 0), 'S'),
                              ((0, 3), 'E'), ((1, 0), 'E'), ((0, 1), 'S'),
                              ((1, 2), 'W'), ((2, 1), 'N')]:
            with self.subTest(state=state, action=action):
                self.env.agent_pos = state
                self.assertEqual(self.env.step(action), (state, -.04, False))

    def test_terminal_entry_and_absorption(self):
        self.force_roll(0)
        for source, target, reward in [((2, 1), (3, 1), -1.),
                                        ((2, 3), (3, 3), 10.)]:
            self.env.agent_pos = source
            self.assertEqual(self.env.step('S'), (target, reward, True))
            for action in self.env.actions:
                self.assertEqual(self.env.step(action), (target, 0., True))
            self.assertEqual(self.env.reset(), (0, 0))

    def test_seed_replay_and_global_rng_isolation(self):
        state = random.getstate()
        other = VacuumWorldEnv(seed=440)
        actions = list('EESSWNNES' * 10)
        a = [self.env.step(action) for action in actions]
        b = [other.step(action) for action in actions]
        self.assertEqual(a, b)
        self.env.reset(seed=440)
        self.assertEqual(a, [self.env.step(action) for action in actions])
        self.assertEqual(state, random.getstate())

    def test_invalid_action(self):
        for action in ('UP', '', None, 1):
            with self.subTest(action=action), self.assertRaises(ValueError):
                self.env.step(action)
