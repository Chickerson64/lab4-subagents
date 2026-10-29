import random
from typing import Tuple

class VacuumWorldEnv:
    """
    4x4 Grid Simulation for Model-Free Reinforcement Learning.
    
    Grid Layout:
      [ Start(0,0),    0    ,    0   ,    0    ]
      [     0     ,  X(1,1) ,    0   ,    0    ]
      [     0     ,    0    ,    0   ,    0    ]
      [     0     , -1(3,1) ,    0   , 10(3,3) ]
    """
    def __init__(self, living_cost: float = -0.04):
        self.rows = 4
        self.cols = 4
        self.living_cost = living_cost
        
        # Grid points
        self.start_pos = (0, 0)
        self.obstacle = (1, 1)
        self.trap = (3, 1)
        self.recharge = (3, 3)
        
        self.agent_pos = self.start_pos
        self.actions = ['N', 'E', 'S', 'W']
        self.delta = {
            'N': (-1, 0),
            'E': (0, 1),
            'S': (1, 0),
            'W': (0, -1)
        }

    def reset(self) -> Tuple[int, int]:
        self.agent_pos = self.start_pos
        return self.agent_pos

    def _get_stochastic_action(self, action: str) -> str:
        idx = self.actions.index(action)
        left = self.actions[(idx - 1) % 4]
        right = self.actions[(idx + 1) % 4]
        
        roll = random.random()
        if roll < 0.8:
            return action
        elif roll < 0.9:
            return left
        else:
            return right

    def step(self, action: str) -> Tuple[Tuple[int, int], float, bool]:
    
        #Executes action with 80% intended, 10% left, 10% right slip.
        #Returns: (next_state, reward, done)
    
        actual_action = self._get_stochastic_action(action)
        dr, dc = self.delta[actual_action]
        target = (self.agent_pos[0] + dr, self.agent_pos[1] + dc)

        if 0 <= target[0] < self.rows and 0 <= target[1] < self.cols:
            if target != self.obstacle:
                self.agent_pos = target

        if self.agent_pos == self.recharge:
            return self.agent_pos, 10.0, True
        elif self.agent_pos == self.trap:
            return self.agent_pos, -1.0, True
        else:
            return self.agent_pos, self.living_cost, False