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
                    # Wait for app to fully load (dynamic timing based on app type)
                    wait_time = self._get_app_load_time(target_app)
                    print(
                        f"   ⏳ Waiting {wait_time}s for {target_app} to fully load..."
                    )
                    time.sleep(wait_time)
                    ui_signals = self.perception.discover_ui_signals(target_app)
                    print(f"   📊 Found {len(ui_signals)} elements after launch")

                    # If still no elements found, let the reasoning engine handle app-specific initialization
                    if len(ui_signals) == 0:
                        print(
                            "   🤖 No elements found - letting reasoning engine handle initialization..."
                        )

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

        # CRITICAL: Focus the target app before starting
        print(f"\n🎯 FOCUSING TARGET APP: {target_app}")
        focus_result = self._focus_target_app(target_app)
        if not focus_result:
            print(f"❌ Failed to focus {target_app}, continuing anyway...")
        else:
            print(f"✅ Successfully focused {target_app}")

        iterations = 0
        max_iter = max_iterations or self.max_iterations

        # Execute the task directly - no iterations needed
        print(f"\n🎯 EXECUTING TASK DIRECTLY")
        print("-" * 40)

        try:
            # 1. Perceive
            perception_data = self.perceive(target_app)
            if "error" in perception_data:
                print(f"❌ Perception failed: {perception_data['error']}")
                return

            # 2. Reason
            reasoning_result = self.reason(goal, perception_data)
            if "error" in reasoning_result:
                print(f"❌ Reasoning failed: {reasoning_result['error']}")
                return

            # 3. Act
            print(f"🎯 EXECUTING ACTIONS...")
            action_result = self.act(reasoning_result)
            if not action_result.get("success", False):
                print(
                    f"❌ Actions failed: {action_result.get('error', 'Unknown error')}"
                )
                print(f"   Error count: {self.state.error_count + 1}/{self.max_errors}")
                self.state.error_count += 1
            else:
                print(f"✅ Actions completed successfully")
                self.state.error_count = 0  # Reset on success

            # Check if goal is achieved
            if self._is_goal_achieved(goal, perception_data, reasoning_result):
                print(f"🎉 GOAL ACHIEVED: {goal}")
                return

            # Check confidence (only stop if very low confidence)
            confidence = reasoning_result.get("confidence", 0)
            if confidence < 0.1:  # Only stop if confidence is extremely low
                print(
                    f"⚠️  Very low confidence ({confidence:.2f}), stopping to prevent errors"
                )
                return
            elif confidence < 0.3:
                print(f"⚠️  Low confidence ({confidence:.2f}), but continuing...")

        except KeyboardInterrupt:
            print("\n⏹️  Agent stopped by user")
            return
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
        """Let Gemini intelligently choose target app from available options"""
        # Get available apps (both open and installed)
        available_apps = self._get_available_apps()

        if not available_apps:
            return None

        # Let Gemini choose the best app for the goal
        return self._ask_gemini_for_app_selection(goal, available_apps)

    def _get_available_apps(self) -> List[str]:
        """Get list of available applications (open and installed)"""
        available_apps = []

        try:
            # Get currently open applications
            import atomacos as atomac

            try:
                # Try to get all running apps
                running_apps = (
                    atomac.getAppRefs() if hasattr(atomac, "getAppRefs") else []
                )
                for app in running_apps:
                    try:
                        app_name = getattr(app, "AXTitle", None) or getattr(
                            app, "AXIdentifier", None
                        )
                        if app_name and app_name not in available_apps:
                            available_apps.append(app_name)
                    except:
                        continue
            except:
                pass

            # Get installed applications from multiple directories
            import os

            app_directories = [
                "/Applications",
                "/System/Applications",
                "/Applications/Utilities",
                "/System/Applications/Utilities",
            ]
            for applications_dir in app_directories:
                if os.path.exists(applications_dir):
                    try:
                        for item in os.listdir(applications_dir):
                            if item.endswith(".app"):
                                app_name = item[:-4]  # Remove .app extension
                                if app_name not in available_apps:
                                    available_apps.append(app_name)
                    except PermissionError:
                        # Skip directories we can't access
                        continue

            # Add common system apps
            system_apps = [
                "System Settings",
                "Calculator",
                "Safari",
                "Mail",
                "Calendar",
                "Finder",
                "Terminal",
                "Activity Monitor",
                "Disk Utility",
            ]
            for app in system_apps:
                if app not in available_apps:
                    available_apps.append(app)

        except Exception as e:
            print(f"   ⚠️  Error getting available apps: {e}")
            # Fallback to common apps
            available_apps = [
                "System Settings",
                "Calculator",
                "Google Chrome",
                "Safari",
                "Mail",
                "Calendar",
                "Finder",
                "Terminal",
            ]

        # Ensure Calculator is always included for math tasks
        if "Calculator" not in available_apps:
            available_apps.append("Calculator")

        return available_apps  # Return all available apps

    def _ask_gemini_for_app_selection(
        self, goal: str, available_apps: List[str]
    ) -> str:
        """Ask Gemini to choose the best app for the goal"""
        try:
            if not self.reasoning.model:
                # Fallback to first available app if Gemini not available
                return available_apps[0] if available_apps else None

            # Create prompt for app selection
            apps_list = "\n".join([f"- {app}" for app in available_apps])
            prompt = f"""
            Choose the best application to achieve this goal: "{goal}"
            
            Available applications:
            {apps_list}
            
            Consider:
            - Which app is most suitable for this specific goal?
            - Is the app likely to be installed and accessible?
            - Will the app provide the necessary functionality?
            
            Respond with just the application name (e.g., "Google Chrome" or "Calculator").
            """

            # VERBOSE: Show app selection prompt and response
            print("\n" + "=" * 80)
            print("📝 APP SELECTION PROMPT SENT TO GEMINI:")
            print("=" * 80)
            print(prompt)
            print("=" * 80)

            response = self.reasoning.model.generate_content(prompt)
            selected_app = response.text.strip()

            # VERBOSE: Show Gemini's response
            print("\n" + "=" * 80)
            print("🤖 GEMINI APP SELECTION RESPONSE:")
            print("=" * 80)
            print(f"Selected App: {selected_app}")
            print("=" * 80)

            # Validate the selection
            if selected_app in available_apps:
                return selected_app
            else:
                # Fallback to first available app
                return available_apps[0] if available_apps else None

        except Exception as e:
            print(f"   ⚠️  Error in app selection: {e}")
            return available_apps[0] if available_apps else None

    def _get_app_load_time(self, app_name: str) -> int:
        """Get appropriate load time for different app types"""
        # Browser apps need more time
        if any(
            browser in app_name.lower()
            for browser in ["chrome", "safari", "firefox", "edge"]
        ):
            return 5
        # Heavy applications
        elif any(
            heavy in app_name.lower()
            for heavy in ["xcode", "photoshop", "final cut", "logic"]
        ):
            return 8
        # Light applications
        elif any(
            light in app_name.lower()
            for light in ["calculator", "notes", "textedit", "terminal"]
        ):
            return 2
        # Default for unknown apps
        else:
            return 3

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
