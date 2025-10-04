#!/usr/bin/env python3
"""
Action Engine - Handles all action execution using accessibility APIs
"""

import time
import atomacos as atomac
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ActionResult:
    """Result of an action execution"""

    success: bool
    action: str
    target: str
    result: Any
    error: str = ""
    timestamp: float = 0.0


class ActionEngine:
    """
    Handles all action execution:
    - UI interactions (click, type, select)
    - System actions (keyboard shortcuts, system calls)
    - Action validation and error handling
    - Action chaining and sequencing
    """

    def __init__(self):
        self.action_history = []
        self.max_retries = 3
        self.action_timeout = 10.0

    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action"""
        action_type = action.get("action", "").lower()
        target = action.get("target", "")
        reason = action.get("reason", "")

        print(f"      🎯 Executing: {action_type} on {target}")

        try:
            if action_type == "click":
                result = self._execute_click(target)
            elif action_type == "type":
                result = self._execute_type(target, action.get("text", ""))
            elif action_type == "select":
                result = self._execute_select(target, action.get("option", ""))
            elif action_type == "scroll":
                result = self._execute_scroll(target, action.get("direction", "down"))
            elif action_type == "wait":
                result = self._execute_wait(action.get("duration", 1.0))
            elif action_type == "key":
                result = self._execute_key(action.get("key", ""))
            else:
                result = self._execute_unknown_action(action_type, target)

            # Store action result
            action_result = ActionResult(
                success=result.get("success", False),
                action=action_type,
                target=target,
                result=result.get("result"),
                error=result.get("error", ""),
                timestamp=time.time(),
            )

            self.action_history.append(action_result)

            if result.get("success", False):
                print(f"      ✅ Action successful: {action_type}")
            else:
                print(f"      ❌ Action failed: {result.get('error', 'Unknown error')}")

            return {
                "success": result.get("success", False),
                "action": action_type,
                "target": target,
                "result": result.get("result"),
                "error": result.get("error", ""),
                "timestamp": time.time(),
            }

        except Exception as e:
            print(f"      ❌ Action execution error: {e}")
            return {
                "success": False,
                "action": action_type,
                "target": target,
                "error": str(e),
                "timestamp": time.time(),
            }

    def _execute_click(self, target: str) -> Dict[str, Any]:
        """Execute a click action"""
        try:
            # Find the target element
            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            # Click the element
            element.AXPress()
            time.sleep(0.5)  # Wait for action to complete

            return {"success": True, "result": f"Clicked {target}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_type(self, target: str, text: str) -> Dict[str, Any]:
        """Execute a type action"""
        try:
            # Find the target element
            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            # Focus the element first
            element.AXSetFocused(True)
            time.sleep(0.2)

            # Type the text
            element.AXSetValue(text)
            time.sleep(0.5)

            return {"success": True, "result": f"Typed '{text}' into {target}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_select(self, target: str, option: str) -> Dict[str, Any]:
        """Execute a select action (for dropdowns, etc.)"""
        try:
            # Find the target element
            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            # For popup buttons, click to open dropdown first
            if element.AXRole == "AXPopUpButton":
                element.AXPress()
                time.sleep(1.0)  # Wait for dropdown to appear

                # Find and click the option
                option_element = self._find_option(element, option)
                if option_element:
                    option_element.AXPress()
                    time.sleep(0.5)
                    return {
                        "success": True,
                        "result": f"Selected '{option}' from {target}",
                    }
                else:
                    return {"success": False, "error": f"Option '{option}' not found"}
            else:
                return {
                    "success": False,
                    "error": f"Element {target} is not a selectable element",
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_scroll(self, target: str, direction: str) -> Dict[str, Any]:
        """Execute a scroll action"""
        try:
            # Find the target element
            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            # Scroll in the specified direction
            if direction.lower() == "up":
                element.AXScrollUp()
            elif direction.lower() == "down":
                element.AXScrollDown()
            elif direction.lower() == "left":
                element.AXScrollLeft()
            elif direction.lower() == "right":
                element.AXScrollRight()
            else:
                return {
                    "success": False,
                    "error": f"Invalid scroll direction: {direction}",
                }

            time.sleep(0.5)
            return {"success": True, "result": f"Scrolled {direction} in {target}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_wait(self, duration: float) -> Dict[str, Any]:
        """Execute a wait action"""
        try:
            time.sleep(duration)
            return {"success": True, "result": f"Waited {duration} seconds"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_key(self, key: str) -> Dict[str, Any]:
        """Execute a keyboard shortcut"""
        try:
            # This would use keyboard automation
            # For now, just simulate
            print(f"      ⌨️  Executing keyboard shortcut: {key}")
            time.sleep(0.5)
            return {"success": True, "result": f"Executed keyboard shortcut: {key}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_unknown_action(self, action_type: str, target: str) -> Dict[str, Any]:
        """Handle unknown action types"""
        return {"success": False, "error": f"Unknown action type: {action_type}"}

    def _find_element(self, target: str) -> Optional[Any]:
        """Find an element by ID or other identifier using position-based matching"""
        try:
            # Try to find in System Settings first (most common target)
            try:
                app = atomac.getAppRefByLocalizedName("System Settings")
                if app:
                    windows = [
                        w
                        for w in app.windows()
                        if getattr(w, "AXRole", None) == "AXWindow"
                    ]

                    for window in windows:
                        # Try to find element by ID first (use findAllR for better compatibility)
                        elements = window.findAllR(AXIdentifier=target)
                        if elements:
                            return elements[0]

                        # Try to find by title
                        elements = window.findAllR(AXTitle=target)
                        if elements:
                            return elements[0]

                        # CRITICAL: Position-based element finding
                        if "_" in target and target.count("_") >= 2:
                            try:
                                # Parse position from ID like "AXButton_533.0_310.0"
                                parts = target.split("_")
                                if len(parts) >= 3:
                                    role = parts[0]  # AXButton
                                    x = float(parts[1])  # 533.0
                                    y = float(parts[2])  # 310.0

                                    # Find all elements of this role
                                    elements = window.findAllR(AXRole=role)
                                    for elem in elements:
                                        pos = getattr(elem, "AXPosition", None)
                                        if (
                                            pos
                                            and abs(pos.x - x) < 10
                                            and abs(pos.y - y) < 10
                                        ):
                                            return elem
                            except:
                                pass

                        # Try to find by role and title
                        if "button" in target.lower():
                            element = window.findFirst(
                                AXRole="AXButton", AXTitle=target
                            )
                            if element:
                                return element
            except Exception:
                pass

            # Try to find in frontmost app
            try:
                app = atomac.getFrontmostApp()
                if app:
                    windows = [
                        w
                        for w in app.windows()
                        if getattr(w, "AXRole", None) == "AXWindow"
                    ]

                    for window in windows:
                        # Try to find element by ID (use findAllR for better compatibility)
                        elements = window.findAllR(AXIdentifier=target)
                        if elements:
                            return elements[0]

                        # Try to find by title
                        elements = window.findAllR(AXTitle=target)
                        if elements:
                            return elements[0]
            except Exception:
                pass

            return None

        except Exception as e:
            print(f"      ⚠️  Error finding element {target}: {e}")
            return None

    def _find_option(self, parent_element: Any, option: str) -> Optional[Any]:
        """Find an option within a parent element (for dropdowns)"""
        try:
            # Get children of the parent element
            children = getattr(parent_element, "AXChildren", None) or []

            for child in children:
                # Check if this child matches the option
                title = getattr(child, "AXTitle", None) or ""
                if option.lower() in title.lower():
                    return child

                # Recursively search children
                grand_children = getattr(child, "AXChildren", None) or []
                for grand_child in grand_children:
                    grand_title = getattr(grand_child, "AXTitle", None) or ""
                    if option.lower() in grand_title.lower():
                        return grand_child

            return None

        except Exception as e:
            print(f"      ⚠️  Error finding option {option}: {e}")
            return None

    def execute_action_sequence(
        self, actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute a sequence of actions"""
        results = []

        for i, action in enumerate(actions):
            print(f"   📋 Executing action {i+1}/{len(actions)}")
            result = self.execute_action(action)
            results.append(result)

            # If action failed, decide whether to continue
            if not result.get("success", False):
                print(f"   ⚠️  Action {i+1} failed, continuing with next action")

            # Small delay between actions
            time.sleep(0.5)

        return results

    def validate_action(self, action: Dict[str, Any]) -> bool:
        """Validate that an action can be executed"""
        action_type = action.get("action", "").lower()
        target = action.get("target", "")

        # Basic validation
        if not action_type or not target:
            return False

        # Check if target element exists
        element = self._find_element(target)
        if not element:
            return False

        # Check if action is supported for this element type
        element_role = getattr(element, "AXRole", None)

        if action_type == "click":
            return element_role in [
                "AXButton",
                "AXPopUpButton",
                "AXCheckBox",
                "AXRadioButton",
            ]
        elif action_type == "type":
            return element_role in ["AXTextField", "AXTextArea"]
        elif action_type == "select":
            return element_role in ["AXPopUpButton", "AXComboBox"]

        return True

    def get_action_summary(self) -> Dict[str, Any]:
        """Get a summary of action capabilities"""
        successful_actions = sum(1 for action in self.action_history if action.success)
        total_actions = len(self.action_history)

        return {
            "total_actions": total_actions,
            "successful_actions": successful_actions,
            "success_rate": (
                successful_actions / total_actions if total_actions > 0 else 0
            ),
            "action_types": list(set(action.action for action in self.action_history)),
        }
