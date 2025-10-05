#!/usr/bin/env python3
"""
Agent Core - Main orchestration system for the reasoning and acting agent
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

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

    def __init__(self, event_cb=None):
        self.perception = PerceptionEngine()
        self.reasoning = ReasoningEngine()
        self.action = ActionEngine()
        self.memory = MemorySystem()

        # Optional callback used by agent_bridge.py to stream step updates
        self._event_cb = event_cb

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

    # -------- Event helpers --------

    def _emit(self, kind: str, **data):
        """Emit a structured step event to the bridge (safe no-op if no callback)."""
        try:
            if self._event_cb:
                self._event_cb({"kind": kind, **data})
        except Exception:
            # Never fail the run because of a progress callback
            pass

    # -------- Core steps --------

    def perceive(self, target_app: Optional[str] = None, goal: str = "") -> Dict[str, Any]:
        """
        Perceive the current environment using hybrid accessibility + visual analysis.
        """
        print("🔍 PERCEIVING: Gathering hybrid environmental signals...")

        try:
            perception_data = self.perception.get_hybrid_perception(target_app, goal)

            # If no UI and a target app is specified, try to launch then re-scan
            if len(perception_data.get("ui_signals", [])) == 0 and target_app:
                self._handle_app_launching(target_app)
                perception_data = self.perception.get_hybrid_perception(target_app, goal)

            # Add timestamp and store in memory
            perception_data["timestamp"] = time.time()
            self.memory.store_perception(
                ui_signals=perception_data.get("ui_signals", []),
                system_state=perception_data.get("system_state"),
                context=perception_data.get("context", {}),
                visual_analysis=perception_data.get("visual_analysis"),
                correlations=perception_data.get("correlations"),
                timestamp=perception_data["timestamp"],
            )

            # Logging
            ui_count = len(perception_data.get("ui_signals", []))
            visual_count = 0
            if perception_data.get("visual_analysis"):
                visual_count = len(perception_data["visual_analysis"].interactive_elements)
            perception_type = perception_data.get("perception_type", "unknown")
            matched_elements = (perception_data.get("correlations") or {}).get("matched_elements", 0)

            print(f"✅ Hybrid perception complete:")
            print(f"   📊 Accessibility: {ui_count} elements")
            print(f"   👁️  Visual: {visual_count} elements")
            print(f"   🔗 Correlated: {matched_elements} elements")
            print(f"   🎯 Type: {perception_type}")

            if perception_data.get("system_state"):
                battery = perception_data["system_state"].battery_level
                print(f"   🔋 System: {battery}% battery")

            return perception_data

        except Exception as e:
            print(f"❌ Hybrid perception error: {e}")
            return {"error": str(e)}

    def reason(self, goal: str, perception_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reason about the goal and current state to determine next actions."""
        print("🧠 REASONING: Analyzing goal and current state...")

        try:
            self.state.goal = goal
            knowledge = self.reasoning.gather_knowledge(goal, perception_data)

            reasoning_result = self.reasoning.analyze_situation(
                goal=goal,
                perception=perception_data,
                knowledge=knowledge,
                agent_state=self.state,
            )

            self.memory.store_reasoning(reasoning_result)

            conf = reasoning_result.get("confidence", 0.0)
            print(f"✅ Reasoning complete: {conf:.2f} confidence")
            return reasoning_result

        except Exception as e:
            print(f"❌ Reasoning error: {e}")
            return {"error": str(e), "plan": [], "confidence": 0.0}

    def reason_with_visual(self, goal: str, perception_data: Dict[str, Any], target_app: Optional[str]) -> Dict[str, Any]:
        """
        Combined VLM + Reasoning in a single API call.
        """
        print("   🎯 Combining visual analysis and reasoning...")

        try:
            screenshot_path = None
            if self.perception.vlm_analyzer:
                screenshot_path = self.perception.vlm_analyzer.capture_screenshot(target_app)

            return self.reasoning.analyze_with_visual(goal, perception_data, screenshot_path)

        except Exception as e:
            print(f"❌ Combined VLM+Reasoning error: {e}")
            return {"error": str(e), "plan": [], "confidence": 0.0}

    def act(self, reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute actions based on reasoning results (one step at a time to allow observe-act loops)."""
        print("🎯 ACTING: Executing planned actions...")

        try:
            plan = reasoning_result.get("plan", [])
            if not plan:
                print("⚠️  No actions to execute")
                return {"success": False, "reason": "No actions in plan"}

            results = []
            for i, action in enumerate(plan):
                # Emit step start
                self._emit(
                    "action.execute",
                    index=i + 1,
                    total=len(plan),
                    action=action.get("action"),
                    target=action.get("target"),
                    description=action.get("description") or action.get("reason"),
                )

                print(f"   Executing action {i+1}/{len(plan)}: {action.get('action')}")

                try:
                    result = self.action.execute_action(action)
                    results.append(result)

                    # Emit step result
                    self._emit(
                        "action.result",
                        index=i + 1,
                        success=bool(result.get("success")),
                        detail=str(result.get("result", ""))[:140],
                    )

                    # Update agent state
                    self.state.last_action = action.get("action", "")
                    self.state.progress = (i + 1) / max(1, len(plan))

                    # Small delay between actions
                    time.sleep(0.4)

                except Exception as e:
                    print(f"   ❌ Action failed: {e}")
                    self.state.error_count += 1
                    results.append({"success": False, "error": str(e)})
                    return {"success": False, "error": str(e), "results": results}

                # After each action, return control to the loop for observation (except last)
                if i < len(plan) - 1:
                    print(f"   🔄 Returning to main loop for observation after action {i+1}")
                    self._emit("action.partial_return", completed=i + 1, total=len(plan))
                    return {
                        "success": True,
                        "partial": True,
                        "completed_actions": i + 1,
                        "total_actions": len(plan),
                        "results": results,
                    }

            # Store all results when the last action completes
            self.memory.store_actions(results)

            success_count = sum(1 for r in results if r.get("success", False))
            print(f"✅ All actions completed: {success_count}/{len(results)} successful")

            return {
                "success": success_count > 0,
                "results": results,
                "success_rate": success_count / len(results) if results else 0,
            }

        except Exception as e:
            print(f"❌ Action error: {e}")
            return {"success": False, "error": str(e)}

    # -------- Loop --------

    def run_autonomous_loop(self, goal: str, target_app: Optional[str] = None, max_iterations: Optional[int] = None):
        """Run the complete perceive-reason-act loop autonomously."""
        if not target_app:
            target_app = self._choose_target_app(goal)

        print(f"🤖 AUTONOMOUS AGENT STARTING")
        print(f"Goal: {goal}")
        print(f"Target App: {target_app}")
        print("=" * 60)

        iterations = 0
        max_iter = max_iterations or self.max_iterations

        self._emit("loop.start", goal=goal, target_app=target_app, max_iterations=max_iter)

        # Focus target app (best effort)
        print(f"\n🎯 FOCUSING TARGET APP: {target_app}")
        focused = self._focus_target_app(target_app) if target_app else False
        print(f"✅ Successfully focused {target_app}" if focused else f"❌ Failed to focus {target_app}, continuing anyway...")
        self._emit("focus.result", app=target_app, success=bool(focused))

        # Initial perception
        self._emit("plan.start", goal=goal, app=target_app)
        print(f"\n🎯 CREATING LONG-RANGE PLAN")
        print("-" * 40)

        initial_perception = self.perceive(target_app, goal)
        if "error" in initial_perception:
            return {
                "success": False,
                "iterations": 0,
                "errors": 1,
                "progress": 0.0,
                "message": f"Initial perception failed: {initial_perception['error']}",
            }

        # Long-range plan (optional)
        ui_signals = initial_perception.get("ui_signals", [])
        system_state = initial_perception.get("system_state", {})
        plan_result = self.reasoning.create_long_range_plan(goal, target_app, ui_signals, system_state)

        if "error" in plan_result:
            print(f"❌ Long-range planning failed: {plan_result['error']}")
            print("   Continuing without long-range plan...")
        else:
            print(f"✅ Long-range plan created successfully")
            print(f"   Goal: {plan_result.get('goal', 'Unknown')}")
            print(f"   End State: {plan_result.get('end_state', 'Not defined')}")
            print(f"   Steps: {len(plan_result.get('steps', []))}")
            self._emit("plan.created",
                       steps=len(plan_result.get("steps", [])),
                       goal=plan_result.get("goal"),
                       end_state=plan_result.get("end_state"))

        # Loop
        print(f"\n🔄 STARTING PERCEIVE-REASON-ACT LOOP")
        print("-" * 40)

        try:
            while iterations < max_iter and self.state.error_count < self.max_errors:
                iterations += 1
                print(f"\n🔄 ITERATION {iterations}/{max_iter}")
                print("=" * 50)
                self._emit("loop.iteration", n=iterations, max=max_iter)

                # 1) Perceive
                self._emit("perceive.start", app=target_app)
                perception_data = self.perceive(target_app, goal)
                if "error" in perception_data:
                    print(f"❌ Perception failed: {perception_data['error']}")
                    self.state.error_count += 1
                    continue

                ui_count = len(perception_data.get("ui_signals", []))
                visual_count = len(perception_data.get("visual_analysis", {}).interactive_elements) if perception_data.get("visual_analysis") else 0
                correlated = (perception_data.get("correlations") or {}).get("matched_elements", 0)
                self._emit("perceive.end", ui=ui_count, visual=visual_count, correlated=correlated)

                # 2) Reason (visual combined)
                self._emit("reason.start")
                reasoning_result = self.reason_with_visual(goal, perception_data, target_app)
                if "error" in reasoning_result:
                    print(f"❌ Reasoning failed: {reasoning_result['error']}")
                    self.state.error_count += 1
                    continue

                actions_planned = len(reasoning_result.get("plan", []))
                self._emit("reason.end", confidence=reasoning_result.get("confidence", 0.0), actions=actions_planned)

                # 3) Act (one action)
                action_result = self.act(reasoning_result)
                if not action_result.get("success", False):
                    print(f"❌ Action failed: {action_result.get('error', 'Unknown error')}")
                    self.state.error_count += 1
                    continue
                else:
                    print(f"✅ Action completed successfully")
                    self.state.error_count = 0  # reset after success

                # 4) Observe post-action (optional)
                print(f"🔍 OBSERVING: Checking state after action...")
                post_action_perception = self.perception.get_hybrid_perception(target_app, goal)
                if post_action_perception and "error" not in post_action_perception:
                    print(f"   📊 Post-action state: {len(post_action_perception.get('ui_signals', []))} elements")
                    updated_reasoning = self.reason_with_visual(goal, post_action_perception, target_app)
                    if not updated_reasoning.get("error"):
                        print(f"   ✅ Updated reasoning: {updated_reasoning.get('confidence', 0):.2f} confidence")
                        perception_data = post_action_perception
                        reasoning_result = updated_reasoning

                # 5) Goal achieved?
                if self._is_goal_achieved(goal, perception_data, reasoning_result):
                    print(f"🎉 GOAL ACHIEVED: {goal}")
                    self._emit("goal.achieved", goal=goal)
                    return {
                        "success": True,
                        "iterations": iterations,
                        "errors": self.state.error_count,
                        "progress": 1.0,
                        "message": f"Goal achieved: {goal}",
                    }

                # Confidence guardrail
                confidence = reasoning_result.get("confidence", 0)
                if confidence < 0.1:
                    print(f"⚠️  Very low confidence ({confidence:.2f}), stopping to prevent errors")
                    self._emit("loop.low_confidence", confidence=confidence)
                    return {
                        "success": False,
                        "iterations": iterations,
                        "errors": self.state.error_count,
                        "progress": self.state.progress,
                        "message": f"Stopped early: very low confidence ({confidence:.2f})",
                    }
                elif confidence < 0.3:
                    print(f"⚠️  Low confidence ({confidence:.2f}), continuing with caution...")

                print(f"🔄 Continuing loop: confidence={confidence:.2f}, errors={self.state.error_count}/{self.max_errors}")
                time.sleep(0.8)

        except KeyboardInterrupt:
            print("\n⏹️  Agent stopped by user")
            return {
                "success": False,
                "iterations": iterations,
                "errors": self.state.error_count,
                "progress": self.state.progress,
                "message": "Stopped by user",
            }
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            self.state.error_count += 1
            return {
                "success": False,
                "iterations": iterations,
                "errors": self.state.error_count,
                "progress": self.state.progress,
                "message": f"Unexpected error: {e}",
            }

        # Max iterations reached
        print(f"\n🏁 AGENT FINISHED")
        print(f"   Iterations: {iterations}")
        print(f"   Errors: {self.state.error_count}")
        print(f"   Final Progress: {self.state.progress:.2f}")
        print(f"   ⚠️  Max iterations reached without achieving goal")
        self._emit("loop.max_iterations", iterations=iterations, max=max_iter)

        return {
            "iterations": iterations,
            "errors": self.state.error_count,
            "progress": self.state.progress,
            "success": False,
            "message": "Max iterations reached without achieving goal",
        }

    # -------- Helpers --------

    def _handle_app_launching(self, target_app: str) -> None:
        """Try to launch the app when we detect no UI signals."""
        try:
            result = self.action._execute_launch_app(target_app)
            if result.get("success"):
                print(f"   ✅ {target_app} launched")
                wait_time = self._get_app_load_time(target_app)
                print(f"   ⏳ Waiting {wait_time}s for {target_app} to load...")
                time.sleep(wait_time)
        except Exception as e:
            print(f"   ⚠️  Error during app launching: {e}")

    def _choose_target_app(self, goal: str) -> Optional[str]:
        """Pick a target app (uses LLM if available)."""
        available = self._get_available_apps()
        if not available:
            return None
        return self._ask_gemini_for_app_selection(goal, available) or available[0]

    def _get_available_apps(self) -> List[str]:
        """Get list of available applications (open and installed)."""
        available_apps: List[str] = []
        try:
            import atomacos as atomac
            try:
                running_apps = atomac.getAppRefs() if hasattr(atomac, "getAppRefs") else []
                for app in running_apps:
                    try:
                        app_name = getattr(app, "AXTitle", None) or getattr(app, "AXIdentifier", None)
                        if app_name and app_name not in available_apps:
                            # avoid VSCode if you want
                            if "visual studio code" in app_name.lower() or "vscode" in app_name.lower():
                                continue
                            available_apps.append(app_name)
                    except Exception:
                        continue
            except Exception:
                pass

            import os
            app_dirs = ["/Applications", "/System/Applications", "/Applications/Utilities", "/System/Applications/Utilities"]
            for d in app_dirs:
                if not os.path.exists(d):
                    continue
                try:
                    for item in os.listdir(d):
                        if item.endswith(".app"):
                            name = item[:-4]
                            if "visual studio code" in name.lower() or "vscode" in name.lower():
                                continue
                            if name not in available_apps:
                                available_apps.append(name)
                except PermissionError:
                    continue

            # Common system apps
            for app in ["System Settings", "Calculator", "Safari", "Mail", "Calendar", "Finder", "Terminal"]:
                if app not in available_apps:
                    available_apps.append(app)

        except Exception as e:
            print(f"   ⚠️  Error getting available apps: {e}")
            available_apps = ["System Settings", "Calculator", "Google Chrome", "Safari", "Mail", "Calendar", "Finder", "Terminal"]

        # Ensure Calculator present (handy for math goals)
        if "Calculator" not in available_apps:
            available_apps.append("Calculator")

        # Apply blacklist for non-user-facing tooling
        blacklist = {
            "Siri", "VoiceOver", "VoiceOver Utility", "Accessibility Inspector", "Console",
            "Activity Monitor", "Disk Utility", "Script Editor", "Automator", "Shortcuts",
            "Mission Control", "Launchpad", "Dock", "Menu Bar", "Control Center",
            "Notification Center", "Spotlight", "Trash", "Desktop"
        }
        filtered = [a for a in available_apps if a not in blacklist]
        print(f"   📊 App filtering: {len(available_apps)} → {len(filtered)} apps")
        return filtered

    def _ask_gemini_for_app_selection(self, goal: str, available_apps: List[str]) -> Optional[str]:
        """Let the reasoning model pick an app if it's configured."""
        try:
            if not self.reasoning.model:
                return None

            apps_list = "\n".join(f"- {a}" for a in available_apps)
            prompt = f"""
Pick the best application for this goal: "{goal}"

Available applications:
{apps_list}

Respond with just the application name.
"""

            print("\n" + "=" * 80)
            print("📝 APP SELECTION PROMPT SENT TO GEMINI:")
            print("=" * 80)
            print(prompt)
            print("=" * 80)

            response = self.reasoning.model.generate_content(prompt)
            selected = (response.text or "").strip()

            print("\n" + "=" * 80)
            print("🤖 GEMINI APP SELECTION RESPONSE:")
            print("=" * 80)
            print(f"Selected App: {selected}")
            print("=" * 80)

            return selected if selected in available_apps else None

        except Exception as e:
            print(f"   ⚠️  Error in app selection: {e}")
            return None

    def _focus_target_app(self, app_name: str) -> bool:
        """Focus the target application to ensure it's active."""
        try:
            import atomacos as atomac
            import subprocess as sp

            normalized = self._normalize_app_name(app_name)
            print(f"      🎯 Focusing {app_name} (normalized: {normalized})...")

            app = atomac.getAppRefByLocalizedName(normalized)
            if not app:
                # launch attempts
                try:
                    sp.run(["open", "-a", normalized], check=True)
                    time.sleep(3)
                    app = atomac.getAppRefByLocalizedName(normalized)
                except Exception:
                    bundle_id = self._get_bundle_id(app_name)
                    if bundle_id:
                        try:
                            sp.run(["open", "-b", bundle_id], check=True)
                            time.sleep(3)
                            app = atomac.getAppRefByLocalizedName(normalized)
                        except Exception:
                            pass
                if not app:
                    return False

            app.activate()
            time.sleep(1)
            front = atomac.getFrontmostApp()
            if front and getattr(front, "AXTitle", "") == normalized:
                print(f"      ✅ {normalized} is now focused")
                return True

            # AppleScript fallback
            try:
                sp.run(["osascript", "-e", f'tell application "{normalized}" to activate'])
                time.sleep(1)
                print(f"      ✅ {normalized} focused via osascript")
                return True
            except Exception:
                # good enough if launched
                print(f"      ✅ {normalized} launched successfully")
                return True

        except Exception as e:
            print(f"      ❌ Error focusing {app_name}: {e}")
            return False

    @staticmethod
    def _normalize_app_name(app_name: str) -> str:
        mapping = {
            "iTerm": "iTerm2",
            "iTerm2": "iTerm2",
            "Terminal": "Terminal",
            "Google Chrome": "Google Chrome",
            "Chrome": "Google Chrome",
            "Safari": "Safari",
            "Calculator": "Calculator",
            "System Settings": "System Settings",
            "System Preferences": "System Settings",
        }
        return mapping.get(app_name, app_name)

    @staticmethod
    def _get_bundle_id(app_name: str) -> str:
        bundle_ids = {
            "Calculator": "com.apple.calculator",
            "Numbers": "com.apple.iWork.Numbers",
            "Google Chrome": "com.google.Chrome",
            "Safari": "com.apple.Safari",
            "System Settings": "com.apple.systempreferences",
            "Mail": "com.apple.mail",
            "Calendar": "com.apple.iCal",
            "Finder": "com.apple.finder",
            "Cursor": "com.todesktop.230313mzl4w4u92",
            "Visual Studio Code": "com.microsoft.VSCode",
            "Terminal": "com.apple.Terminal",
        }
        return bundle_ids.get(app_name, "")

    @staticmethod
    def _get_app_load_time(app_name: str) -> int:
        name = (app_name or "").lower()
        if any(b in name for b in ["chrome", "safari", "firefox", "edge"]):
            return 5
        if any(h in name for h in ["xcode", "photoshop", "final cut", "logic"]):
            return 8
        if any(l in name for l in ["calculator", "notes", "textedit", "terminal"]):
            return 2
        return 3

    # -------- Goal achievement heuristics --------

    def _is_goal_achieved(self, goal: str, perception_data: Dict[str, Any], reasoning_result: Dict[str, Any]) -> bool:
        """Check if the goal has been achieved using long-range plan criteria and heuristics."""
        # Prefer explicit completion indicators from plan
        if self.reasoning.long_range_plan:
            plan = self.reasoning.long_range_plan
            success_criteria = plan.get("success_criteria", [])
            completion_indicators = plan.get("completion_indicators", [])
            if success_criteria or completion_indicators:
                print("   🎯 Checking goal achievement against long-range plan...")
                ui_signals = perception_data.get("ui_signals", [])
                system_state = perception_data.get("system_state")

                # system-state indicators (string containment)
                for indicator in completion_indicators:
                    s = indicator.lower()
                    if system_state:
                        state_blob = f"{system_state}".lower()
                        if s in state_blob:
                            print(f"   ✅ Found completion indicator in system state: {indicator}")
                            return True

                    # UI title/description/value checks
                    for sig in ui_signals:
                        title = str(sig.get("title", "")).lower()
                        desc = str(sig.get("description", "")).lower()
                        val_raw = sig.get("current_value", "")
                        try:
                            val = str(val_raw).lower()
                        except Exception:
                            val = str(val_raw)
                        if any(x for x in [title, desc, val] if x and x in s):
                            print(f"   ✅ Found completion indicator in UI: {indicator}")
                            return True

        # Heuristics fallback
        g = goal.lower()

        # Fast-path: calculator/math/search/terminal intents via confidence
        if any(k in g for k in ["echo", "command", "terminal", "iterm", "bash", "shell"]):
            return reasoning_result.get("confidence", 0) > 0.8
        if any(k in g for k in ["search", "find", "look for"]):
            return reasoning_result.get("confidence", 0) > 0.7
        if any(k in g for k in ["calculate", "math", "calculator", "+", "-", "*", "/"]):
            return reasoning_result.get("confidence", 0) > 0.8

        # Video playback indicator heuristic
        if any(k in g for k in ["video", "show", "watch", "play"]):
            for signal in perception_data.get("ui_signals", []):
                title = str(signal.get("title", "")).lower()
                if any(k in title for k in ["play", "pause", "full screen", "seek slider"]):
                    print(f"   ✅ Found video player element: {signal.get('title', '')}")
                    return True

        # Generic high-confidence success
        return reasoning_result.get("confidence", 0) > 0.9

    # -------- Status --------

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "state": self.state,
            "memory_size": len(self.memory.perceptions),
            "reasoning_count": len(self.memory.reasonings),
            "action_count": len(self.memory.actions),
        }


def main():
    """Main function for running the agent with CLI arguments."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Autonomous Agent System - Perceive, Reason, and Act"
    )
    parser.add_argument("goal", help="The goal for the agent to achieve in natural language")
    parser.add_argument("target_app", nargs="?", default=None, help="Target application (optional)")
    parser.add_argument("--max-iterations", type=int, default=10, help="Maximum iterations (default: 10)")
    parser.add_argument("--max-errors", type=int, default=5, help="Maximum errors before stopping (default: 5)")
    parser.add_argument("--no-save", action="store_true", help="Do not persist JSON result to disk")

    args = parser.parse_args()

    agent = AgentCore()
    agent.max_iterations = args.max_iterations
    agent.max_errors = args.max_errors

    print(f"🤖 AUTONOMOUS AGENT STARTING")
    print(f"Goal: {args.goal}")
    print(f"Target App: {args.target_app}")
    print(f"Max Iterations: {args.max_iterations}")
    print(f"Max Errors: {args.max_errors}")
    print("=" * 60)

    try:
        result = agent.run_autonomous_loop(goal=args.goal, target_app=args.target_app, max_iterations=args.max_iterations)
        if result is None:
            result = {
                "success": False,
                "iterations": 0,
                "errors": agent.state.error_count,
                "progress": 0.0,
                "message": "Agent completed without returning result",
            }

        if not args.no_save:
            filename = f"agent_result_{args.goal.replace(' ', '_')}.json"
            with open(filename, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\n💾 Results saved to {filename}")

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


if __name__ == "__main__":
    main()
