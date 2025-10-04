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

        # VERBOSE: Print full action details
        print(f"      📋 Full action details: {action}")

        try:
            # Dynamic action execution based on action type
            action_method = getattr(self, f"_execute_{action_type}", None)
            if action_method:
                print(f"      🔧 Using method: _execute_{action_type}")
                # Call the appropriate method with parameters
                if action_type in ["type", "select"]:
                    text_or_option = action.get("text", action.get("option", ""))
                    print(f"      📝 Text/option: '{text_or_option}'")
                    result = action_method(target, text_or_option)
                elif action_type in ["keystroke"]:
                    text = action.get("text", "")
                    print(f"      ⌨️  Keystroke text: '{text}'")
                    result = action_method(target, text)
                elif action_type in ["scroll"]:
                    direction = action.get("direction", "down")
                    print(f"      📜 Direction: {direction}")
                    result = action_method(target, direction)
                elif action_type in ["wait"]:
                    duration = action.get("duration", 1.0)
                    print(f"      ⏱️  Duration: {duration}")
                    result = action_method(duration)
                elif action_type in ["key"]:
                    key = action.get("key", "")
                    print(f"      ⌨️  Key: '{key}'")
                    result = action_method(key)
                elif action_type in ["press"]:
                    # Convert press to key action
                    key = action.get("key", "enter")
                    print(f"      ⌨️  Converting press to key: '{key}'")
                    result = self._execute_key(key)
                elif action_type in ["launch_app"]:
                    app_name = action.get("app_name", target)
                    print(f"      🚀 App name: '{app_name}'")
                    result = action_method(app_name)
                else:
                    print(f"      🎯 Simple target: '{target}'")
                    result = action_method(target)
            else:
                print(f"      ⚠️  No specific method found, using generic action")
                # Try to execute as a generic action
                result = self._execute_generic_action(action_type, target, action)

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
        """Execute a click action with multiple fallback methods"""
        try:
            # Handle "all" target for system-wide actions
            if target == "all":
                print(f"      ⚠️  Cannot click 'all' - this is not a valid click target")
                return {
                    "success": False,
                    "error": "Cannot click 'all' - use keystroke action instead",
                }

            # Find the target element
            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            # Try multiple click methods
            try:
                # Method 1: Standard AXPress
                element.AXPress()
                return {"success": True, "result": f"Clicked {target}"}

            except AttributeError:
                # Try alternative click methods
                if hasattr(element, "AXPerformAction"):
                    element.AXPerformAction("AXPress")
                    return {"success": True, "result": f"Performed action on {target}"}

                # Try mouse click simulation
                try:
                    import subprocess

                    pos = getattr(element, "AXPosition", None)
                    if pos:
                        # Use osascript to click at the element position
                        subprocess.run(
                            [
                                "osascript",
                                "-e",
                                f'tell application "System Events" to click at {{{pos.x}, {pos.y}}}',
                            ]
                        )
                        return {
                            "success": True,
                            "result": f"Clicked {target} at position ({pos.x}, {pos.y})",
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Could not get position for {target}",
                        }
                except Exception as e:
                    return {"success": False, "error": f"Click simulation failed: {e}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_type(self, target: str, text: str) -> Dict[str, Any]:
        """Execute a type action - focus window and element first, then type"""
        try:
            import subprocess

            # Find and click the target element to focus it
            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            # CRITICAL: Force focus the application window first
            try:
                # Find the application that contains this element
                app = None
                common_apps = [
                    "Google Chrome",
                    "Safari",
                    "System Settings",
                    "Calculator",
                    "Cursor",
                    "Visual Studio Code",
                ]

                for app_name in common_apps:
                    try:
                        test_app = atomac.getAppRefByLocalizedName(app_name)
                        if test_app:
                            # Check if this element belongs to this app
                            windows = [
                                w
                                for w in test_app.windows()
                                if getattr(w, "AXRole", None) == "AXWindow"
                            ]
                            for window in windows:
                                # Try to find this element in this window
                                if self._element_in_window(element, window):
                                    app = test_app
                                    print(f"      🎯 Found app: {app_name}")
                                    break
                            if app:
                                break
                    except:
                        continue

                if app:
                    print(
                        f"      🎯 Focusing app: {getattr(app, 'AXTitle', 'Unknown')}"
                    )
                    app.activate()  # Focus the application
                    time.sleep(1.0)  # Wait longer for focus

                    # Double-check that the app is focused
                    frontmost_app = atomac.getFrontmostApp()
                    if frontmost_app and getattr(
                        frontmost_app, "AXTitle", ""
                    ) != getattr(app, "AXTitle", ""):
                        print(f"      ⚠️  App focus failed, trying alternative method")
                        # Try using osascript to focus the app
                        app_name = getattr(app, "AXTitle", "")
                        if app_name:
                            subprocess.run(
                                [
                                    "osascript",
                                    "-e",
                                    f'tell application "{app_name}" to activate',
                                ]
                            )
                            time.sleep(1.0)
                else:
                    print(
                        f"      ⚠️  Could not find app for element, trying to focus anyway"
                    )
                    # Try to focus the element directly
            except Exception as e:
                print(f"      ❌ App focus failed: {e}")
                # Continue anyway - maybe the element click will work

            # Click the element to focus it
            try:
                print(f"      🎯 Clicking element to focus it")
                element.AXPress()  # Click to focus
                time.sleep(1.0)  # Wait longer for focus
            except Exception as e:
                print(f"      ⚠️  Could not click element: {e}")
                return {"success": False, "error": f"Could not focus element: {e}"}

            # Clear the field (select all and delete)
            print(f"      🧹 Clearing field")
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to keystroke "a" using command down',
                ]
            )
            time.sleep(0.3)
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to keystroke (ASCII character 127)',
                ]
            )
            time.sleep(0.3)

            # Type the text
            print(f"      ⌨️  Typing: '{text}'")
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'tell application "System Events" to keystroke "{text}"',
                ]
            )
            time.sleep(0.5)

            # Auto-press Enter for search completion (keystroke navigation)
            print(f"      ⏎  Pressing Enter to complete search")
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to key code 36',  # Enter key
                ]
            )
            time.sleep(0.5)

            return {
                "success": True,
                "result": f"Typed '{text}' and pressed Enter into {target}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_press_enter(self, target: str) -> Dict[str, Any]:
        """Press Enter key on an element"""
        try:
            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            # Focus the element first
            try:
                element.AXSetFocused()
            except:
                element.AXPress()
            time.sleep(0.2)

            # Press Enter key using system events
            import subprocess

            subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to key code 36']
            )
            return {"success": True, "result": f"Pressed Enter on {target}"}

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
        """Execute a keyboard key press"""
        try:
            import subprocess

            # Map common keys to key codes
            key_map = {
                "enter": "36",
                "return": "36",
                "space": "49",
                "tab": "48",
                "escape": "53",
                "delete": "51",
                "backspace": "51",
            }

            key_code = key_map.get(key.lower(), key)
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'tell application "System Events" to key code {key_code}',
                ]
            )
            time.sleep(0.5)

            return {"success": True, "result": f"Pressed {key} key"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_keystroke(self, target: str, text: str) -> Dict[str, Any]:
        """Execute keystroke navigation - type and press Enter automatically"""
        try:
            import subprocess

            # Handle "all" target for terminal applications and System Settings search
            if target == "all":
                # Check if this is an app launch command
                if text.lower().startswith("open ") or text.lower().startswith(
                    "launch "
                ):
                    print(f"      🚀 App launch command: '{text}'")
                    try:
                        import subprocess

                        # Extract app name from command
                        app_name = (
                            text.replace("open ", "").replace("launch ", "").strip()
                        )
                        subprocess.run(["open", "-a", app_name], check=True)
                        time.sleep(2)  # Wait for app to launch
                        return {"success": True, "result": f"Launched {app_name}"}
                    except Exception as e:
                        return {
                            "success": False,
                            "error": f"Failed to launch {app_name}: {e}",
                        }

                print(f"      ⌨️  System-wide keystroke: '{text}' + Enter")

                # Clear any existing text (select all and delete)
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "System Events" to keystroke "a" using command down',
                    ]
                )
                time.sleep(0.2)
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "System Events" to keystroke (ASCII character 127)',
                    ]
                )
                time.sleep(0.2)

                # Type the text
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        f'tell application "System Events" to keystroke "{text}"',
                    ]
                )
                time.sleep(0.3)

                # Press Enter to execute
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "System Events" to key code 36',
                    ]
                )
                time.sleep(0.5)

                return {
                    "success": True,
                    "result": f"System-wide keystroke: '{text}' + Enter",
                }

            # Find and focus the target element
            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            # Focus the application window
            try:
                app = None
                common_apps = [
                    "Google Chrome",
                    "Safari",
                    "System Settings",
                    "Calculator",
                    "Cursor",
                    "Visual Studio Code",
                ]

                for app_name in common_apps:
                    try:
                        test_app = atomac.getAppRefByLocalizedName(app_name)
                        if test_app and self._element_in_window(element, test_app):
                            app = test_app
                            break
                    except:
                        continue

                if app:
                    app.activate()
                    time.sleep(1.0)
            except Exception as e:
                print(f"      ⚠️  App focus failed: {e}")

            # Click the element to focus it
            try:
                element.AXPress()
                time.sleep(0.5)
            except Exception as e:
                print(f"      ⚠️  Could not click element: {e}")

            # Clear the field and type
            print(f"      ⌨️  Keystroke navigation: '{text}' + Enter")

            # Clear field
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to keystroke "a" using command down',
                ]
            )
            time.sleep(0.2)
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to keystroke (ASCII character 127)',
                ]
            )
            time.sleep(0.2)

            # Type the text
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'tell application "System Events" to keystroke "{text}"',
                ]
            )
            time.sleep(0.3)

            # Press Enter to complete
            subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to key code 36']
            )
            time.sleep(0.5)

            return {
                "success": True,
                "result": f"Keystroke navigation: '{text}' + Enter",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_press(self, target: str) -> Dict[str, Any]:
        """Execute a press action (for keys like 'enter')"""
        try:
            import subprocess

            # Handle key presses
            if target.lower() in ["enter", "return"]:
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "System Events" to key code 36',
                    ]
                )
                time.sleep(0.5)
                return {"success": True, "result": f"Pressed {target} key"}
            else:
                return {"success": False, "error": f"Unknown key: {target}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_generic_action(
        self, action_type: str, target: str, action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute generic actions dynamically"""
        try:
            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            # Try common accessibility actions
            if hasattr(element, f"AX{action_type.capitalize()}"):
                method = getattr(element, f"AX{action_type.capitalize()}")
                method()
                return {
                    "success": True,
                    "result": f"Executed {action_type} on {target}",
                }

            # Try generic press action
            elif hasattr(element, "AXPress"):
                element.AXPress()
                return {"success": True, "result": f"Pressed {target}"}

            # Try alternative click methods
            elif hasattr(element, "AXPerformAction"):
                element.AXPerformAction("AXPress")
                return {"success": True, "result": f"Performed action on {target}"}

            # Try mouse click simulation
            else:
                try:
                    import subprocess

                    pos = getattr(element, "AXPosition", None)
                    if pos:
                        # Use osascript to click at the element position
                        subprocess.run(
                            [
                                "osascript",
                                "-e",
                                f'tell application "System Events" to click at {{{pos.x}, {pos.y}}}',
                            ]
                        )
                        return {
                            "success": True,
                            "result": f"Clicked {target} at position ({pos.x}, {pos.y})",
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Could not get position for {target}",
                        }
                except Exception as e:
                    return {"success": False, "error": f"Click simulation failed: {e}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_unknown_action(self, action_type: str, target: str) -> Dict[str, Any]:
        """Handle unknown action types"""
        return {"success": False, "error": f"Unknown action type: {action_type}"}

    def _execute_launch_app(self, app_name: str) -> Dict[str, Any]:
        """Launch and focus on an application"""
        try:
            # Try to get existing app first
            app = atomac.getAppRefByLocalizedName(app_name)

            if not app:
                # App not running, try to launch it
                print(f"      🚀 Launching {app_name}...")

                # Use system command as primary method
                import subprocess

                try:
                    subprocess.run(["open", "-a", app_name], check=True)
                    time.sleep(3)  # Wait for app to start
                    app = atomac.getAppRefByLocalizedName(app_name)
                except subprocess.CalledProcessError:
                    # Try alternative launch methods
                    bundle_id = self._get_bundle_id(app_name)
                    if bundle_id:
                        try:
                            subprocess.run(["open", "-b", bundle_id], check=True)
                            time.sleep(3)
                            app = atomac.getAppRefByLocalizedName(app_name)
                        except:
                            pass

            if app:
                # Focus the app
                app.activate()
                time.sleep(2)  # Wait for focus and UI to load

                # Check if we have windows
                windows = [
                    w for w in app.windows() if getattr(w, "AXRole", None) == "AXWindow"
                ]
                if windows:
                    return {
                        "success": True,
                        "result": f"Launched and focused {app_name}",
                    }
                else:
                    return {
                        "success": True,
                        "result": f"Launched {app_name} (no windows yet)",
                    }
            else:
                return {"success": False, "error": f"Could not launch {app_name}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_bundle_id(self, app_name: str) -> str:
        """Get bundle ID for common apps"""
        bundle_ids = {
            "Google Chrome": "com.google.Chrome",
            "Safari": "com.apple.Safari",
            "Calculator": "com.apple.calculator",
            "System Settings": "com.apple.systempreferences",
            "Mail": "com.apple.mail",
            "Calendar": "com.apple.iCal",
            "Finder": "com.apple.finder",
            "Cursor": "com.todesktop.230313mzl4w4u92",
            "Visual Studio Code": "com.microsoft.VSCode",
        }
        return bundle_ids.get(app_name, "")

    def _get_bundle_path(self, app_name: str) -> str:
        """Get bundle path for common apps"""
        bundle_paths = {
            "Google Chrome": "/Applications/Google Chrome.app",
            "Safari": "/Applications/Safari.app",
            "Calculator": "/Applications/Calculator.app",
            "System Settings": "/System/Applications/System Settings.app",
            "Mail": "/Applications/Mail.app",
            "Calendar": "/Applications/Calendar.app",
            "Finder": "/System/Library/CoreServices/Finder.app",
        }
        return bundle_paths.get(app_name, "")

    def _find_element(self, target: str) -> Optional[Any]:
        """Find an element by ID or other identifier using position-based matching"""
        try:
            # Search in common apps where elements might be found
            common_apps = [
                "System Settings",
                "Calculator",
                "Google Chrome",
                "Safari",
                "Cursor",
                "Visual Studio Code",
                "Mail",
                "Calendar",
                "Finder",
            ]

            for app_name in common_apps:
                try:
                    app = atomac.getAppRefByLocalizedName(app_name)
                    if app:
                        windows = [
                            w
                            for w in app.windows()
                            if getattr(w, "AXRole", None) == "AXWindow"
                        ]

                        for window in windows:
                            # Try to find element by ID first (use findAllR for better compatibility)
                            try:
                                elements = window.findAllR(AXIdentifier=target)
                                if elements:
                                    return elements[0]
                            except Exception as e:
                                print(f"      ⚠️  AXIdentifier search failed: {e}")
                                # Continue to other methods

                            # Try to find by title
                            try:
                                elements = window.findAllR(AXTitle=target)
                                if elements:
                                    return elements[0]
                            except Exception as e:
                                print(f"      ⚠️  AXTitle search failed: {e}")
                                # Continue to other methods

                            # Fallback: Manual element scanning for identifier-based IDs
                            try:
                                all_elements = window.findAllR()
                                for elem in all_elements:
                                    try:
                                        identifier = getattr(elem, "AXIdentifier", "")
                                        if identifier == target:
                                            return elem
                                    except:
                                        continue
                            except Exception as e:
                                print(f"      ⚠️  Manual element scan failed: {e}")

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
                    continue

            return None

        except Exception as e:
            print(f"      ⚠️  Error finding element {target}: {e}")
            return None

    def _element_in_window(self, element: Any, window: Any) -> bool:
        """Check if an element belongs to a specific window"""
        try:
            # Get all elements in the window and check if our element is among them
            all_elements = window.findAllR()
            for elem in all_elements:
                if elem == element:
                    return True
            return False
        except:
            return False

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
