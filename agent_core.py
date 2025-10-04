#!/usr/bin/env python3
"""
Agent Core - Main orchestration system for the reasoning and acting agent
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

from perception import PerceptionEngine
from reasoning import ReasoningEngine
from action import ActionEngine
from memory import MemorySystem


@dataclass
class AgentState:
    """Current state of the agent"""

    goal: str
    current_task: str
    progress: float
    confidence: float
    last_action: str
    error_count: int
    session_id: str


class AgentCore:
    """
    Main agent that orchestrates perception, reasoning, and action
    Implements the perceive-reason-act loop for autonomous operation
    """

    def __init__(self):
        self.perception = PerceptionEngine()
        self.reasoning = ReasoningEngine()
        self.action = ActionEngine()
        self.memory = MemorySystem()

        self.state = AgentState(
            goal="",
            current_task="",
            progress=0.0,
            confidence=0.0,
            last_action="",
            error_count=0,
            session_id=time.strftime("%Y%m%d_%H%M%S"),
        )

        self.max_errors = 5
        self.max_iterations = 50

    def perceive(self, target_app: str = None) -> Dict[str, Any]:
        """Perceive the current environment and system state"""
        print("🔍 PERCEIVING: Gathering environmental signals...")

        try:
            # Get UI signals
            ui_signals = self.perception.discover_ui_signals(target_app)

            # Get system state
            system_state = self.perception.get_system_state()

            # Get context
            context = self.perception.get_context(target_app)

            # Store in memory
            perception_data = {
                "ui_signals": ui_signals,
                "system_state": system_state,
                "context": context,
                "timestamp": time.time(),
            }

            self.memory.store_perception(perception_data)

            print(
                f"✅ Perceived {len(ui_signals)} UI elements, system state: {system_state.battery_level}% battery"
            )
            return perception_data

        except Exception as e:
            print(f"❌ Perception error: {e}")
            return {"error": str(e)}

    def reason(self, goal: str, perception_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reason about the goal and current state to determine next actions"""
        print("🧠 REASONING: Analyzing goal and current state...")

        try:
            # Update agent state
            self.state.goal = goal

            # Get knowledge context
            knowledge = self.reasoning.gather_knowledge(goal, perception_data)

            # Generate reasoning
            reasoning_result = self.reasoning.analyze_situation(
                goal=goal,
                perception=perception_data,
                knowledge=knowledge,
                agent_state=self.state,
            )

            # Store reasoning in memory
            self.memory.store_reasoning(reasoning_result)

            print(
                f"✅ Reasoning complete: {reasoning_result['confidence']:.2f} confidence"
            )
            return reasoning_result

        except Exception as e:
            print(f"❌ Reasoning error: {e}")
            return {"error": str(e), "plan": [], "confidence": 0.0}

    def act(self, reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute actions based on reasoning results"""
        print("🎯 ACTING: Executing planned actions...")

        try:
            plan = reasoning_result.get("plan", [])
            if not plan:
                print("⚠️  No actions to execute")
                return {"success": False, "reason": "No actions in plan"}

            # Execute each action in the plan
            results = []
            for i, action in enumerate(plan):
                print(f"   Executing action {i+1}/{len(plan)}: {action['action']}")

                try:
                    result = self.action.execute_action(action)
                    results.append(result)

                    # Update agent state
                    self.state.last_action = action["action"]
                    self.state.progress = (i + 1) / len(plan)

                    # Small delay between actions
                    time.sleep(0.5)

                except Exception as e:
                    print(f"   ❌ Action failed: {e}")
                    self.state.error_count += 1
                    results.append({"success": False, "error": str(e)})

            # Store action results in memory
            self.memory.store_actions(results)

            success_count = sum(1 for r in results if r.get("success", False))
            print(f"✅ Actions completed: {success_count}/{len(results)} successful")

            return {
                "success": success_count > 0,
                "results": results,
                "success_rate": success_count / len(results) if results else 0,
            }

        except Exception as e:
            print(f"❌ Action error: {e}")
            return {"success": False, "error": str(e)}

    def run_autonomous_loop(
        self, goal: str, target_app: str = None, max_iterations: int = None
    ):
        """Run the complete perceive-reason-act loop autonomously"""
        print(f"🤖 AUTONOMOUS AGENT STARTING")
        print(f"Goal: {goal}")
        print(f"Target App: {target_app or 'All Apps'}")
        print("=" * 60)

        iterations = 0
        max_iter = max_iterations or self.max_iterations

        while iterations < max_iter and self.state.error_count < self.max_errors:
            iterations += 1
            print(f"\n🔄 ITERATION {iterations}/{max_iter}")
            print("-" * 40)

            try:
                # 1. Perceive
                perception_data = self.perceive(target_app)
                if "error" in perception_data:
                    print(f"❌ Perception failed: {perception_data['error']}")
                    break

                # 2. Reason
                reasoning_result = self.reason(goal, perception_data)
                if "error" in reasoning_result:
                    print(f"❌ Reasoning failed: {reasoning_result['error']}")
                    break

                # 3. Act
                action_result = self.act(reasoning_result)
                if not action_result.get("success", False):
                    print(
                        f"❌ Actions failed: {action_result.get('error', 'Unknown error')}"
                    )
                    self.state.error_count += 1
                else:
                    self.state.error_count = 0  # Reset on success

                # Check if goal is achieved
                if self._is_goal_achieved(goal, perception_data, reasoning_result):
                    print(f"🎉 GOAL ACHIEVED: {goal}")
                    break

                # Check confidence
                if reasoning_result.get("confidence", 0) < 0.3:
                    print("⚠️  Low confidence, stopping to prevent errors")
                    break

            except KeyboardInterrupt:
                print("\n⏹️  Agent stopped by user")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                self.state.error_count += 1

        print(f"\n🏁 AGENT FINISHED")
        print(f"   Iterations: {iterations}")
        print(f"   Errors: {self.state.error_count}")
        print(f"   Final Progress: {self.state.progress:.2f}")

        return {
            "iterations": iterations,
            "errors": self.state.error_count,
            "progress": self.state.progress,
            "success": self.state.error_count < self.max_errors,
        }

    def _is_goal_achieved(
        self,
        goal: str,
        perception_data: Dict[str, Any],
        reasoning_result: Dict[str, Any],
    ) -> bool:
        """Check if the goal has been achieved"""
        # Simple goal achievement checking
        # In a real system, this would be more sophisticated

        if "battery" in goal.lower() and "optimize" in goal.lower():
            # Check if Low Power Mode is enabled
            ui_signals = perception_data.get("ui_signals", [])
            for signal in ui_signals:
                if "low_power" in signal.get("id", "").lower():
                    current_value = signal.get("current_value", "")
                    if current_value.lower() in ["on", "always", "only on battery"]:
                        return True

        return False

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "state": self.state,
            "memory_size": len(self.memory.perceptions),
            "reasoning_count": len(self.memory.reasonings),
            "action_count": len(self.memory.actions),
        }


def main():
    """Main function for testing the agent"""
    import sys

    agent = AgentCore()

    if len(sys.argv) > 1:
        goal = sys.argv[1]
        target_app = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        goal = "optimize battery life"
        target_app = "System Settings"

    # Run autonomous loop
    result = agent.run_autonomous_loop(goal, target_app)

    # Save results
    with open("agent_result.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n💾 Results saved to agent_result.json")


if __name__ == "__main__":
    main()
