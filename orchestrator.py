"""
Orchestrator for Context Engineering Strategy 4 (Context Isolation via Sub-Agents).
Dispatches isolated tasks to specialized agents and synthesizes the outputs.
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class SubAgentTask:
    description: str
    prompt: str
    subagent_type: str

class AgentOrchestrator:
    def __init__(self):
        self.subagents = {
            "env-architect": ".claude/subagents/env_architect.md",
            "q-learning-architect": ".claude/subagents/q_learning_agent.md",
            "code-reviewer": ".claude/subagents/code_reviewer.md"
        }

    def filter_context(self, task: SubAgentTask) -> Dict[str, Any]:
        """
        Context Filter: Strips global conversation history and supplies 
        only task-specific instructions to avoid context confusion.
        """
        return {
            "subagent": task.subagent_type,
            "system_spec": self.subagents[task.subagent_type],
            "isolated_prompt": task.prompt
        }

    def run_pipeline(self):
        env_task = SubAgentTask(
            description="Build Model-Free 4x4 Grid Environment",
            prompt="Generate src/environment.py with a Gym-style step() method for the 4x4 grid.",
            subagent_type="env-architect"
        )
        filtered_env_context = self.filter_context(env_task)
        print(f"[*] Dispatched to {filtered_env_context['subagent']} with isolated context.")

        agent_task = SubAgentTask(
            description="Scaffold Q-Learning Algorithm",
            prompt="Generate src/agent_interface.py with Q-table initialization and epsilon-greedy update logic.",
            subagent_type="q-learning-architect"
        )
        filtered_agent_context = self.filter_context(agent_task)
        print(f"[*] Dispatched to {filtered_agent_context['subagent']} with isolated context.")

        review_task = SubAgentTask(
            description="Audit Model-Free Invariants",
            prompt="Audit src/environment.py and src/agent_interface.py to guarantee no leakage of T or R.",
            subagent_type="code-reviewer"
        )
        filtered_review_context = self.filter_context(review_task)
        print(f"[*] Dispatched to {filtered_review_context['subagent']} with isolated context.")

if __name__ == "__main__":
    orchestrator = AgentOrchestrator()
    orchestrator.run_pipeline()