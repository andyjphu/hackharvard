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

    def perceive(self, target_app: str = None, goal: str = "") -> Dict[str, Any]:
        """
        Perceive the current environment using hybrid accessibility + visual analysis.

        This method combines traditional accessibility API scanning with visual language model
        analysis to provide comprehensive environmental understanding.

        Args:
            target_app: Target application to focus on
            goal: User goal for context-aware visual analysis

        Returns:
            Dictionary containing hybrid perception data with both accessibility and visual elements
        """
        print("🔍 PERCEIVING: Gathering hybrid environmental signals...")

        try:
            # Use hybrid perception that combines accessibility and visual analysis
            perception_data = self.perception.get_hybrid_perception(target_app, goal)

            # Handle app launching if no UI signals found
            if len(perception_data.get("ui_signals", [])) == 0 and target_app:
                self._handle_app_launching(target_app, perception_data)
                # Re-run hybrid perception after potential launch
                perception_data = self.perception.get_hybrid_perception(
                    target_app, goal
                )

            # Add timestamp for tracking
            perception_data["timestamp"] = time.time()

            # Store comprehensive perception data in memory
            self.memory.store_perception(
                ui_signals=perception_data.get("ui_signals", []),
                system_state=perception_data.get("system_state"),
                context=perception_data.get("context", {}),
                visual_analysis=perception_data.get("visual_analysis"),
                correlations=perception_data.get("correlations"),
                timestamp=perception_data["timestamp"],
            )

            # Enhanced logging with hybrid data
            ui_count = len(perception_data.get("ui_signals", []))
            visual_count = 0
            if perception_data.get("visual_analysis"):
                visual_count = len(
                    perception_data["visual_analysis"].interactive_elements
                )

            perception_type = perception_data.get("perception_type", "unknown")
            matched_elements = 0
            if perception_data.get("correlations"):
                matched_elements = perception_data["correlations"].get(
                    "matched_elements", 0
                )

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
            import traceback

            traceback.print_exc()
            return {"error": str(e)}

    def _handle_app_launching(
        self, target_app: str, perception_data: Dict[str, Any]
    ) -> None:
        """
        Handle app launching logic with comprehensive error handling.

        This method manages the complex process of launching applications when no UI elements
        are initially found, including proper error handling and timing considerations.

        Args:
            target_app: Application to potentially launch
            perception_data: Current perception data to update
        """
        try:
            import atomacos as atomac

            # Check if app is already running
            app = atomac.getAppRefByLocalizedName(target_app)
            if app:
                print(f"   ⚠️  {target_app} is already running but no UI elements found")
                print(
                    f"   🤖 Letting reasoning engine handle app-specific initialization..."
                )
            else:
                print(f"   🚀 {target_app} not running, attempting to launch...")
                launch_result = self.action._execute_launch_app(target_app)

                if launch_result.get("success", False):
                    print(f"   ✅ {launch_result.get('result', 'App launched')}")

                    # Dynamic wait time based on app type for optimal loading
                    wait_time = self._get_app_load_time(target_app)
                    print(
                        f"   ⏳ Waiting {wait_time}s for {target_app} to fully load..."
                    )
                    time.sleep(wait_time)

                    # Re-scan for elements after launch
                    new_ui_signals = self.perception.discover_ui_signals(target_app)
                    print(f"   📊 Found {len(new_ui_signals)} elements after launch")

                    # Update perception data with new elements
                    perception_data["ui_signals"] = new_ui_signals

        except Exception as e:
            print(f"   ⚠️  Error during app launching: {e}")
            print(f"   🤖 Letting reasoning engine handle initialization...")

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

    def reason_with_visual(
        self, goal: str, perception_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combined VLM + Reasoning in a single API call.

        This method combines visual analysis and reasoning into one step,
        reducing API calls and improving efficiency.
        """
        print("   🎯 Combining visual analysis and reasoning...")

        try:
            # Get screenshot for visual analysis
            screenshot_path = None
            if (
                hasattr(self.perception, "vlm_analyzer")
                and self.perception.vlm_analyzer
            ):
                screenshot_path = self.perception.vlm_analyzer.capture_screenshot(
                    perception_data.get("target_app", "")
                )

            # Use reasoning engine with visual context
            return self.reasoning.analyze_with_visual(
                goal, perception_data, screenshot_path
            )

        except Exception as e:
            print(f"❌ Combined VLM+Reasoning error: {e}")
            return {"error": str(e), "plan": [], "confidence": 0.0}

    def act(self, reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute actions based on reasoning results"""
        print("🎯 ACTING: Executing planned actions...")

        try:
            plan = reasoning_result.get("plan", [])
            if not plan:
                print("⚠️  No actions to execute")
                return {"success": False, "reason": "No actions in plan"}

            # Execute actions one at a time for continuous observation
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
                    return {"success": False, "error": str(e), "results": results}

                # After each action, return control to main loop for observation
                if i < len(plan) - 1:  # Not the last action
                    print(
                        f"   🔄 Returning to main loop for observation after action {i+1}"
                    )
                    return {
                        "success": True,
                        "partial": True,
                        "completed_actions": i + 1,
                        "total_actions": len(plan),
                        "results": results,
                    }

            # Store action results in memory
            self.memory.store_actions(results)

            success_count = sum(1 for r in results if r.get("success", False))
            print(
                f"✅ All actions completed: {success_count}/{len(results)} successful"
            )

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

        # Create long-range plan before starting the loop
        print(f"\n🎯 CREATING LONG-RANGE PLAN")
        print("-" * 40)

        # Get initial perception for planning
        initial_perception = self.perceive(target_app, goal)
        if "error" in initial_perception:
            print(f"❌ Initial perception failed: {initial_perception['error']}")
            return {
                "success": False,
                "iterations": 0,
                "errors": 1,
                "progress": 0.0,
                "message": f"Initial perception failed: {initial_perception['error']}",
            }

        # Create long-range plan
        ui_signals = initial_perception.get("ui_signals", [])
        system_state = initial_perception.get("system_state", {})
        plan_result = self.reasoning.create_long_range_plan(
            goal, target_app, ui_signals, system_state
        )

        if "error" in plan_result:
            print(f"❌ Long-range planning failed: {plan_result['error']}")
            print("   Continuing without long-range plan...")
        else:
            print(f"✅ Long-range plan created successfully")
            print(f"   Goal: {plan_result.get('goal', 'Unknown')}")
            print(f"   End State: {plan_result.get('end_state', 'Not defined')}")
            print(f"   Steps: {len(plan_result.get('steps', []))}")

        # Execute the task with continuous perceive-reason-act loop
        print(f"\n🔄 STARTING PERCEIVE-REASON-ACT LOOP")
        print("-" * 40)

        try:
            while iterations < max_iter and self.state.error_count < self.max_errors:
                iterations += 1
                print(f"\n🔄 ITERATION {iterations}/{max_iter}")
                print("=" * 50)

                # 1. Perceive (observe current state)
                print(f"🔍 PERCEIVING: Gathering environmental signals...")
                perception_data = self.perceive(target_app, goal)
                if "error" in perception_data:
                    print(f"❌ Perception failed: {perception_data['error']}")
                    self.state.error_count += 1
                    continue

                # 2. Combined VLM + Reasoning in single step
                print(
                    f"🧠 COMBINED VLM + REASONING: Analyzing goal and visual state..."
                )
                reasoning_result = self.reason_with_visual(goal, perception_data)
                if "error" in reasoning_result:
                    print(f"❌ Reasoning failed: {reasoning_result['error']}")
                    self.state.error_count += 1
                    continue

                # 3. Act (execute one action)
                print(f"🎯 ACTING: Executing planned action...")
                action_result = self.act(reasoning_result)
                if not action_result.get("success", False):
                    print(
                        f"❌ Action failed: {action_result.get('error', 'Unknown error')}"
                    )
                    print(
                        f"   Error count: {self.state.error_count + 1}/{self.max_errors}"
                    )
                    self.state.error_count += 1
                    # Don't check goal achievement if action failed
                    continue
                else:
                    print(f"✅ Action completed successfully")
                    self.state.error_count = 0  # Reset on success

                # 4. Continuous Observation: Observe state after action
                print(f"🔍 OBSERVING: Checking state after action...")
                post_action_perception = self.perceive(target_app, goal)
                if post_action_perception and not post_action_perception.get("error"):
                    print(
                        f"   📊 Post-action state: {len(post_action_perception.get('ui_signals', []))} elements"
                    )

                    # Generate new reasoning based on updated state
                    print(f"🧠 REASONING: Analyzing updated state...")
                    updated_reasoning = self.reason_with_visual(
                        goal, post_action_perception
                    )
                    if not updated_reasoning.get("error"):
                        print(
                            f"   ✅ Updated reasoning: {updated_reasoning.get('confidence', 0):.2f} confidence"
                        )
                        # Update perception data for goal checking
                        perception_data = post_action_perception
                        reasoning_result = updated_reasoning
                    else:
                        print(
                            f"   ⚠️  Updated reasoning failed: {updated_reasoning.get('error')}"
                        )

                # Only check goal achievement if action succeeded
                goal_achieved = self._is_goal_achieved(
                    goal, perception_data, reasoning_result
                )
                if goal_achieved:
                    print(f"🎉 GOAL ACHIEVED: {goal}")
                    return {
                        "success": True,
                        "iterations": iterations,
                        "errors": self.state.error_count,
                        "progress": 1.0,
                        "message": f"Goal achieved: {goal}",
                    }

                # Check confidence (only stop if very low confidence)
                confidence = reasoning_result.get("confidence", 0)
                if confidence < 0.1:  # Only stop if confidence is extremely low
                    print(
                        f"⚠️  Very low confidence ({confidence:.2f}), stopping to prevent errors"
                    )
                    return
                elif confidence < 0.3:
                    print(f"⚠️  Low confidence ({confidence:.2f}), but continuing...")

                # Debug: Show why agent continues
                print(
                    f"🔄 Continuing loop: goal_achieved={goal_achieved}, confidence={confidence:.2f}, errors={self.state.error_count}/{self.max_errors}"
                )

                # Brief pause between iterations
                time.sleep(1)

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

        # If we reach here, we hit max iterations without achieving the goal
        print(f"\n🏁 AGENT FINISHED")
        print(f"   Iterations: {iterations}")
        print(f"   Errors: {self.state.error_count}")
        print(f"   Final Progress: {self.state.progress:.2f}")
        print(f"   ⚠️  Max iterations reached without achieving goal")

        return {
            "iterations": iterations,
            "errors": self.state.error_count,
            "progress": self.state.progress,
            "success": False,  # Goal was NOT achieved if we hit max iterations
            "message": "Max iterations reached without achieving goal",
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
                        # BLACKLIST: Filter out VSCode from running apps
                        if (app_name and app_name not in available_apps and
                            "visual studio code" not in app_name.lower() and
                            "vscode" not in app_name.lower()):
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
                                # BLACKLIST: Filter out VSCode
                                if (app_name not in available_apps and 
                                    "visual studio code" not in app_name.lower() and 
                                    "vscode" not in app_name.lower()):
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

        # Apply blacklist to filter out unwanted apps
        available_apps = self._apply_app_blacklist(available_apps)

        return available_apps  # Return all available apps

    def _apply_app_blacklist(self, apps: List[str]) -> List[str]:
        """Apply blacklist to filter out unwanted applications"""
        # Define blacklisted apps that should never be selected
        # CUSTOMIZE THIS LIST TO YOUR PREFERENCES:
        blacklisted_apps = {
            "Siri",  # Voice assistant - not suitable for automation
            "VoiceOver",  # Accessibility tool - not for automation
            "VoiceOver Utility",  # Accessibility tool
            "Accessibility Inspector",  # Developer tool
            "Console",  # System log viewer - not user-facing
            "Activity Monitor",  # System monitor - not for user tasks
            "Disk Utility",  # System utility - not for user tasks
            # "Terminal",  # REMOVED: You want Terminal available for automation
            "Script Editor",  # Developer tool
            "Automator",  # Automation tool - conflicts with our agent
            "Shortcuts",  # iOS automation - conflicts with our agent
            "Mission Control",  # System UI - not an app
            "Launchpad",  # App launcher - not an app
            "Dock",  # System UI - not an app
            "Menu Bar",  # System UI - not an app
            "Control Center",  # System UI - not an app
            "Notification Center",  # System UI - not an app
            "Spotlight",  # System search - not an app
            "Finder",  # File manager - limited automation value
            "Trash",  # System UI - not an app
            "Desktop",  # System UI - not an app
        }

        # Filter out blacklisted apps
        filtered_apps = []
        for app in apps:
            if app not in blacklisted_apps:
                filtered_apps.append(app)
            else:
                print(f"   🚫 Blacklisted app: {app}")

        print(f"   📊 App filtering: {len(apps)} → {len(filtered_apps)} apps")
        return filtered_apps

    def _normalize_app_name(self, app_name: str) -> str:
        """Normalize app names to handle common variations"""
        # Common app name mappings
        name_mappings = {
            "iTerm": "iTerm2",
            "iTerm2": "iTerm2",
            "Terminal": "Terminal",
            "Google Chrome": "Google Chrome",
            "Chrome": "Google Chrome",
            "Safari": "Safari",
            "Calculator": "Calculator",
            "System Settings": "System Settings",
            "System Preferences": "System Settings",  # Old name
        }

        # Return mapped name or original if no mapping exists
        return name_mappings.get(app_name, app_name)

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

    def _focus_target_app(self, app_name: str) -> bool:
        """Focus the target application to ensure it's active"""
        try:
            import atomacos as atomac
            import subprocess
            import time

            # Normalize the app name to handle common variations
            normalized_name = self._normalize_app_name(app_name)
            print(f"      🎯 Focusing {app_name} (normalized: {normalized_name})...")

            # Try to get the app reference with normalized name
            app = atomac.getAppRefByLocalizedName(normalized_name)

            if not app:
                print(
                    f"      🚀 App not running, attempting to launch {normalized_name}..."
                )
                # Try multiple launch methods
                launch_success = False

                # Method 1: Try with normalized name
                try:
                    subprocess.run(["open", "-a", normalized_name], check=True)
                    time.sleep(3)  # Wait for app to start
                    app = atomac.getAppRefByLocalizedName(normalized_name)
                    if app:
                        launch_success = True
                except subprocess.CalledProcessError:
                    pass

                # Method 2: Try with bundle ID
                if not launch_success:
                    bundle_id = self._get_bundle_id(app_name)
                    if bundle_id:
                        try:
                            subprocess.run(["open", "-b", bundle_id], check=True)
                            time.sleep(3)
                            app = atomac.getAppRefByLocalizedName(normalized_name)
                            if app:
                                launch_success = True
                        except:
                            pass

                # Method 3: Try with original name
                if not launch_success:
                    try:
                        subprocess.run(["open", "-a", app_name], check=True)
                        time.sleep(3)
                        app = atomac.getAppRefByLocalizedName(app_name)
                        if app:
                            launch_success = True
                    except:
                        pass

                if not launch_success:
                    print(f"      ❌ Failed to launch {normalized_name}")
                    return False

            if app:
                # Focus the app
                app.activate()
                time.sleep(1)  # Wait for focus

                # Verify the app is focused
                frontmost_app = atomac.getFrontmostApp()
                if (
                    frontmost_app
                    and getattr(frontmost_app, "AXTitle", "") == normalized_name
                ):
                    print(f"      ✅ {normalized_name} is now focused")
                    return True
                else:
                    print(
                        f"      ⚠️  {normalized_name} focus verification failed, trying alternative method"
                    )
                    # Try using osascript to focus
                    try:
                        subprocess.run(
                            [
                                "osascript",
                                "-e",
                                f'tell application "{normalized_name}" to activate',
                            ]
                        )
                        time.sleep(1)
                        print(f"      ✅ {normalized_name} focused via osascript")
                        return True
                    except:
                        # Final fallback - just return True if we have the app reference
                        print(f"      ✅ {normalized_name} launched successfully")
                        return True
            else:
                print(f"      ❌ Could not get reference to {app_name}")
                return False

        except Exception as e:
            print(f"      ❌ Error focusing {app_name}: {e}")
            return False

    def _get_bundle_id(self, app_name: str) -> str:
        """Get bundle ID for common apps"""
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
        """Check if the goal has been achieved using long-range plan criteria"""

        # First, check if we have a long-range plan with success criteria
        if self.reasoning.long_range_plan:
            plan = self.reasoning.long_range_plan
            success_criteria = plan.get("success_criteria", [])
            completion_indicators = plan.get("completion_indicators", [])

            if success_criteria or completion_indicators:
                print(f"   🎯 Checking goal achievement against long-range plan...")
                print(f"   📋 Success criteria: {success_criteria}")
                print(f"   ✅ Completion indicators: {completion_indicators}")

                # Check if any completion indicators are present in current state
                ui_signals = perception_data.get("ui_signals", [])
                system_state = perception_data.get("system_state")

                for indicator in completion_indicators:
                    indicator_lower = indicator.lower()

                    # Check system state indicators (more reliable)
                    if system_state:
                        # Check if indicator mentions a system state attribute
                        system_attrs = [
                            "network_status",
                            "battery_level",
                            "power_source",
                            "memory_usage",
                            "cpu_usage",
                        ]
                        for attr in system_attrs:
                            if attr in indicator_lower:
                                current_value = getattr(system_state, attr, "unknown")
                                # Check if the indicator matches the current
                                # system state
                                # Only return True if the indicator describes the CURRENT state, not the desired state
                                # Convert to string first, then lowercase (handles numbers and strings)
                                try:
                                    current_state_str = str(current_value).lower()
                                except AttributeError:
                                    # If it's a number or other type without .lower(), just convert to string
                                    current_state_str = str(current_value)

                                # For network_status, check if indicator describes the DESIRED end state
                                if attr == "network_status":
                                    # Indicators often describe changes like "changes from X to Y"
                                    # We need to check if current state matches the END state (Y), not the start state (X)

                                    # Parse "changes from X to Y" or "changes to Y" patterns
                                    if (
                                        "changes" in indicator_lower
                                        or "change" in indicator_lower
                                    ):
                                        # Look for the target state after "to"
                                        if " to " in indicator_lower:
                                            parts = indicator_lower.split(" to ")
                                            if len(parts) >= 2:
                                                target_state = (
                                                    parts[-1].strip().strip("'\".,")
                                                )
                                                # Check if current state matches the target state
                                                if (
                                                    target_state in current_state_str
                                                    or current_state_str in target_state
                                                ):
                                                    print(
                                                        f"   ✅ Found completion indicator: {indicator} (system state: {attr}={current_value})"
                                                    )
                                                    return True
                                    else:
                                        # For non-change indicators, use exact matching
                                        if current_state_str in indicator_lower:
                                            print(
                                                f"   ✅ Found completion indicator: {indicator} (system state: {attr}={current_value})"
                                            )
                                            return True
                                else:
                                    # For other attributes, use exact matching
                                    if current_state_str in indicator_lower:
                                        print(
                                            f"   ✅ Found completion indicator: {indicator} (system state: {attr}={current_value})"
                                        )
                                        return True

                    # Check UI element indicators with state verification
                    for signal in ui_signals:
                        # Safely convert to lowercase, handling non-string types
                        title = str(signal.get("title", "")).lower()
                        current_value_raw = signal.get("current_value", "")
                        try:
                            current_value = str(current_value_raw).lower()
                        except AttributeError:
                            current_value = str(current_value_raw)
                        description = str(signal.get("description", "")).lower()

                        # Check if indicator matches element title/description
                        if (
                            indicator_lower in title
                            or indicator_lower in description
                            or any(
                                keyword in title for keyword in indicator_lower.split()
                            )
                        ):
                            # For toggles/switches, verify the actual state
                            if (
                                "toggle" in indicator_lower
                                or "switch" in indicator_lower
                                or "off" in indicator_lower
                                or "on" in indicator_lower
                            ):
                                # Verify the state matches the indicator
                                if "off" in indicator_lower and current_value in [
                                    "off",
                                    "disabled",
                                    "false",
                                ]:
                                    print(
                                        f"   ✅ Found completion indicator: {indicator} (state: {current_value})"
                                    )
                                    return True
                                elif "on" in indicator_lower and current_value in [
                                    "on",
                                    "enabled",
                                    "true",
                                ]:
                                    print(
                                        f"   ✅ Found completion indicator: {indicator} (state: {current_value})"
                                    )
                                    return True
                            else:
                                # For non-state indicators, use text matching
                                print(f"   ✅ Found completion indicator: {indicator}")
                                return True

                # Don't declare success just based on confidence
                # High confidence means we know what to do, not that we've done it
                # The goal is only achieved if we find actual completion indicators

        # Fallback to original logic if no long-range plan
        goal_lower = goal.lower()

        # Terminal/command execution goals
        if any(
            keyword in goal_lower
            for keyword in ["echo", "command", "terminal", "iterm", "bash", "shell"]
        ):
            return reasoning_result.get("confidence", 0) > 0.8

        # Battery optimization goals
        if "battery" in goal_lower and "optimize" in goal_lower:
            ui_signals = perception_data.get("ui_signals", [])
            for signal in ui_signals:
                if "low_power" in str(signal.get("id", "")).lower():
                    current_value = signal.get("current_value", "")
                    current_value_str = (
                        str(current_value).lower()
                        if isinstance(current_value, str)
                        else str(current_value)
                    )
                    if current_value_str in ["on", "always", "only on battery"]:
                        return True

        # Search goals
        if any(keyword in goal_lower for keyword in ["search", "find", "look for"]):
            return reasoning_result.get("confidence", 0) > 0.7

        # Calculator goals
        if any(
            keyword in goal_lower
            for keyword in ["calculate", "math", "calculator", "+", "-", "*", "/"]
        ):
            return reasoning_result.get("confidence", 0) > 0.8

        # Video goals - check for YouTube video player elements
        if any(keyword in goal_lower for keyword in ["video", "show", "watch", "play"]):
            ui_signals = perception_data.get("ui_signals", [])
            for signal in ui_signals:
                title = str(signal.get("title", "")).lower()
                if any(
                    keyword in title
                    for keyword in ["play", "pause", "full screen", "seek slider"]
                ):
                    print(
                        f"   ✅ Found video player element: {signal.get('title', '')}"
                    )
                    return True

        # General goals - use confidence as a proxy
        confidence = reasoning_result.get("confidence", 0)
        if confidence > 0.9:
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

        # Ensure result is not None
        if result is None:
            result = {
                "success": False,
                "iterations": 0,
                "errors": agent.state.error_count,
                "progress": 0.0,
                "message": "Agent completed without returning result",
            }

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
