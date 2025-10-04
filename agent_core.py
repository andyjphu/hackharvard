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

            # If no UI signals found and we have a target app, try to launch it
            if len(ui_signals) == 0 and target_app:
                print(
                    f"   🚀 No UI elements found, attempting to launch {target_app}..."
                )
                launch_result = self.action._execute_launch_app(target_app)
                if launch_result.get("success", False):
                    print(f"   ✅ {launch_result.get('result', 'App launched')}")
                    # Wait longer for Chrome to fully load its UI elements
                    wait_time = 5 if target_app in ["Google Chrome", "Safari"] else 2
                    print(
                        f"   ⏳ Waiting {wait_time}s for {target_app} to fully load..."
                    )
                    time.sleep(wait_time)
                    ui_signals = self.perception.discover_ui_signals(target_app)
                    print(f"   📊 Found {len(ui_signals)} elements after launch")

                    # If still no elements for Chrome, try to navigate to a page
                    if len(ui_signals) == 0 and target_app == "Google Chrome":
                        print(
                            "   🌐 Chrome needs web content - navigating to Google..."
                        )
                        try:
                            import subprocess
                            import urllib.parse

                            # Extract search query from the goal using generalized logic
                            goal_lower = self.state.goal.lower().strip()

                            # Remove common prefixes and suffixes that don't contribute to search
                            prefixes_to_remove = [
                                "search for",
                                "search",
                                "look for",
                                "find",
                                "google",
                                "browse for",
                                "look up",
                                "find information about",
                                "search information about",
                            ]

                            suffixes_to_remove = [
                                "on google",
                                "on the web",
                                "online",
                                "on the internet",
                                "for me",
                                "please",
                                "thanks",
                                "thank you",
                                "on chrome",
                                "in chrome",
                            ]

                            # Clean up the goal by removing prefixes and suffixes
                            cleaned_goal = goal_lower
                            for prefix in prefixes_to_remove:
                                if cleaned_goal.startswith(prefix):
                                    cleaned_goal = cleaned_goal[len(prefix) :].strip()
                                    break

                            for suffix in suffixes_to_remove:
                                if cleaned_goal.endswith(suffix):
                                    cleaned_goal = cleaned_goal[: -len(suffix)].strip()
                                    break

                            # Handle special cases and clean up further
                            if not cleaned_goal or cleaned_goal in [
                                "",
                                "the",
                                "a",
                                "an",
                            ]:
                                search_query = "general search"
                            else:
                                # Remove common stop words that don't add search value
                                stop_words = {
                                    "the",
                                    "a",
                                    "an",
                                    "and",
                                    "or",
                                    "but",
                                    "in",
                                    "on",
                                    "at",
                                    "to",
                                    "for",
                                    "of",
                                    "with",
                                    "by",
                                }
                                words = cleaned_goal.split()
                                filtered_words = [
                                    word for word in words if word not in stop_words
                                ]

                                if not filtered_words:
                                    search_query = "general search"
                                else:
                                    search_query = " ".join(filtered_words)

                                    # Handle specific patterns
                                    if "youtube" in search_query:
                                        search_query = "youtube"
                                    elif "weather" in search_query:
                                        search_query = "weather"
                                    elif "news" in search_query:
                                        search_query = "news"

                            # URL encode the search query
                            encoded_query = urllib.parse.quote_plus(search_query)
                            search_url = (
                                f"https://www.google.com/search?q={encoded_query}"
                            )

                            print(f"   🔍 Searching for: {search_query}")

                            # Use Chrome's command line to open a new tab with Google search
                            subprocess.run(["open", "-a", "Google Chrome", search_url])
                            time.sleep(3)  # Wait for page to load

                            ui_signals = self.perception.discover_ui_signals(target_app)
                            print(
                                f"   📊 Found {len(ui_signals)} elements after navigation"
                            )
                        except Exception as e:
                            print(f"   ⚠️  Error navigating Chrome: {e}")

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
        # Intelligently choose target app if not specified
        if not target_app:
            target_app = self._choose_target_app(goal)

        print(f"🤖 AUTONOMOUS AGENT STARTING")
        print(f"Goal: {goal}")
        print(f"Target App: {target_app}")
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

    def _choose_target_app(self, goal: str) -> str:
        """Intelligently choose target app based on goal"""
        goal_lower = goal.lower()

        # System settings related goals
        if any(
            keyword in goal_lower
            for keyword in [
                "battery",
                "power",
                "energy",
                "low power",
                "brightness",
                "display",
                "security",
                "privacy",
                "firewall",
                "filevault",
                "touch id",
                "biometric",
                "accessibility",
                "voiceover",
                "zoom",
                "high contrast",
                "voice control",
                "settings",
                "preferences",
                "configure",
                "setup",
                "enable",
                "disable",
            ]
        ):
            return "System Settings"

        # Calculator related goals
        if any(
            keyword in goal_lower
            for keyword in [
                "calculate",
                "math",
                "add",
                "subtract",
                "multiply",
                "divide",
                "plus",
                "minus",
                "times",
                "equals",
                "sum",
                "total",
                "result",
            ]
        ):
            return "Calculator"

        # Web browser related goals
        if any(
            keyword in goal_lower
            for keyword in [
                "search",
                "google",
                "browse",
                "web",
                "internet",
                "website",
                "url",
                "chrome",
                "safari",
                "firefox",
                "browser",
                "look up",
                "find information",
            ]
        ):
            return "Google Chrome"  # Default to Chrome, but could be Safari

        # Text editor related goals
        if any(
            keyword in goal_lower
            for keyword in [
                "write",
                "edit",
                "text",
                "document",
                "note",
                "memo",
                "draft",
                "cursor",
                "vscode",
                "sublime",
                "atom",
                "editor",
            ]
        ):
            return "Cursor"  # Default to Cursor, but could be VS Code

        # Mail related goals
        if any(
            keyword in goal_lower
            for keyword in [
                "email",
                "mail",
                "send",
                "compose",
                "reply",
                "inbox",
                "message",
            ]
        ):
            return "Mail"

        # Calendar related goals
        if any(
            keyword in goal_lower
            for keyword in [
                "calendar",
                "schedule",
                "meeting",
                "appointment",
                "event",
                "reminder",
            ]
        ):
            return "Calendar"

        # Default to System Settings for general system tasks
        return "System Settings"

    def _extract_search_query(self, goal: str) -> str:
        """Extract search query from natural language goal using generalized logic"""
        goal_lower = goal.lower().strip()

        # Remove common prefixes and suffixes that don't contribute to search
        prefixes_to_remove = [
            "search for",
            "search",
            "look for",
            "find",
            "google",
            "browse for",
            "look up",
            "find information about",
            "search information about",
        ]

        suffixes_to_remove = [
            "on google",
            "on the web",
            "online",
            "on the internet",
            "for me",
            "please",
            "thanks",
            "thank you",
            "on chrome",
            "in chrome",
        ]

        # Clean up the goal by removing prefixes and suffixes
        cleaned_goal = goal_lower
        for prefix in prefixes_to_remove:
            if cleaned_goal.startswith(prefix):
                cleaned_goal = cleaned_goal[len(prefix) :].strip()
                break

        for suffix in suffixes_to_remove:
            if cleaned_goal.endswith(suffix):
                cleaned_goal = cleaned_goal[: -len(suffix)].strip()
                break

        # Handle special cases and clean up further
        if not cleaned_goal or cleaned_goal in ["", "the", "a", "an"]:
            return "general search"

        # Remove common stop words that don't add search value
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }
        words = cleaned_goal.split()
        filtered_words = [word for word in words if word not in stop_words]

        if not filtered_words:
            return "general search"

        # Join the filtered words
        search_query = " ".join(filtered_words)

        # Handle specific patterns
        if "youtube" in search_query:
            return "youtube"
        elif "weather" in search_query:
            return "weather"
        elif "news" in search_query:
            return "news"

        return search_query

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
    """Main function for running the agent with CLI arguments"""
    import sys
    import argparse

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Autonomous Agent System - Perceive, Reason, and Act",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent_core.py "save battery life"
  python agent_core.py "make my computer more secure"
  python agent_core.py "help me calculate 15 + 27"
  python agent_core.py "search for the meaning of life on Google"
  python agent_core.py "write a note about my meeting"
  python agent_core.py "schedule a meeting for tomorrow"
  python agent_core.py "optimize battery life" "System Settings" --max-iterations 10
        """,
    )

    parser.add_argument(
        "goal",
        help="The goal for the agent to achieve in natural language (e.g., 'save battery life', 'make my computer secure', 'calculate 15 + 27')",
    )
    parser.add_argument(
        "target_app",
        nargs="?",
        default=None,
        help="Target application to interact with (optional - agent will choose intelligently if not specified)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum number of iterations (default: 10)",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=5,
        help="Maximum number of errors before stopping (default: 5)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--save-results",
        action="store_true",
        default=True,
        help="Save results to JSON file (default: True)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Create agent
    agent = AgentCore()

    # Configure agent based on arguments
    agent.max_iterations = args.max_iterations
    agent.max_errors = args.max_errors

    print(f"🤖 AUTONOMOUS AGENT STARTING")
    print(f"Goal: {args.goal}")
    print(f"Target App: {args.target_app}")
    print(f"Max Iterations: {args.max_iterations}")
    print(f"Max Errors: {args.max_errors}")
    print("=" * 60)

    try:
        # Run autonomous loop
        result = agent.run_autonomous_loop(
            goal=args.goal,
            target_app=args.target_app,
            max_iterations=args.max_iterations,
        )

        # Save results if requested
        if args.save_results:
            filename = f"agent_result_{args.goal.replace(' ', '_')}.json"
            with open(filename, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\n💾 Results saved to {filename}")

        # Print final summary
        print(f"\n🏁 AGENT FINISHED")
        print(f"   Goal: {args.goal}")
        print(f"   Success: {result['success']}")
        print(f"   Iterations: {result['iterations']}")
        print(f"   Errors: {result['errors']}")
        print(f"   Final Progress: {result['progress']:.2f}")

    except KeyboardInterrupt:
        print("\n⏹️  Agent stopped by user")
    except Exception as e:
        print(f"\n❌ Agent failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
