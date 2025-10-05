#!/usr/bin/env python3
"""
Action Engine - Handles all action execution using accessibility APIs
"""

import time
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

import atomacos as atomac
from PIL import Image

from model.gemini import VLMAnalyzer  # unified analyzer source


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
    - Visual verification of actions
    """

    def __init__(self):
        self.action_history: List[ActionResult] = []
        self.visual_verification_enabled = True
        self.max_retries = 3
        self.action_timeout = 10.0

    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action"""
        action_type = action.get("action", "").lower()
        target = action.get("target", "")
        reason = action.get("reason", "")

        print(f"      🎯 Executing: {action_type} on {target}")
        print(f"      📋 Full action details: {action}")

        try:
            action_method = getattr(self, f"_execute_{action_type}", None)
            if action_method:
                print(f"      🔧 Using method: _execute_{action_type}")
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
                    key = action.get("key", "enter")
                    print(f"      ⌨️  Converting press to key: '{key}'")
                    result = self._execute_key(key)
                elif action_type in ["launch_app"]:
                    app_name = action.get("app_name", target)
                    print(f"      🚀 App name: '{app_name}'")
                    result = action_method(app_name)
                else:
                    print(f"      🎯 Simple target fallback: '{target}'")
                    result = action_method(target)
            else:
                print(f"      ⚠️  No specific method found, using generic action")
                result = self._execute_generic_action(action_type, target, action)

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
            if target == "all":
                return {
                    "success": False,
                    "error": "Cannot click 'all' — use keystroke for system-wide actions",
                }

            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            before_state = None
            if self.visual_verification_enabled:
                before_state = self.capture_before_screenshot(target)

            try:
                # Prefer AXPress
                if hasattr(element, "AXPress"):
                    element.AXPress()
                elif hasattr(element, "AXPerformAction"):
                    element.AXPerformAction("AXPress")
                else:
                    # Coordinate fallback using cliclick
                    pos = getattr(element, "AXPosition", None)
                    if not pos:
                        return {"success": False, "error": f"No position for {target}"}
                    subprocess.run(["cliclick", f"c:{int(pos.x)},{int(pos.y)}"])
            except Exception as e:
                # Final coordinate fallback
                pos = getattr(element, "AXPosition", None)
                if not pos:
                    return {"success": False, "error": f"No position for {target}"}
                try:
                    subprocess.run(["cliclick", f"c:{int(pos.x)},{int(pos.y)}"])
                except Exception as ee:
                    return {"success": False, "error": f"Click failed: {ee}"}

            if self.visual_verification_enabled and before_state and before_state.get("success"):
                verification_result = self.verify_action_visually(target, before_state)
                if not verification_result.get("verified"):
                    return {
                        "success": False,
                        "error": "No visual change detected after click",
                        "verification": verification_result,
                    }

            return {"success": True, "result": f"Clicked {target}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_type(self, target: str, text: str) -> Dict[str, Any]:
        """Execute a type action - focus window and element first, then type"""
        try:
            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            # Try to focus the app that owns this element
            try:
                app = None
                common_apps = [
                    "Google Chrome",
                    "Safari",
                    "System Settings",
                    "Calculator",
                    "Cursor",
                    "Visual Studio Code",
                    "Mail",
                    "Calendar",
                ]
                for app_name in common_apps:
                    try:
                        test_app = atomac.getAppRefByLocalizedName(app_name)
                        if not test_app:
                            continue
                        for w in test_app.windows():
                            if getattr(w, "AXRole", None) == "AXWindow" and self._element_in_window(element, w):
                                app = test_app
                                break
                        if app:
                            break
                    except Exception:
                        continue

                if app:
                    print(f"      🎯 Focusing app: {getattr(app, 'AXTitle', 'Unknown')}")
                    app.activate()
                    time.sleep(1.0)
                    # If still not frontmost, try AppleScript
                    frontmost = atomac.getFrontmostApp()
                    if not frontmost or getattr(frontmost, "AXTitle", "") != getattr(app, "AXTitle", ""):
                        app_name = getattr(app, "AXTitle", "")
                        if app_name:
                            subprocess.run(["osascript", "-e", f'tell application "{app_name}" to activate'])
                            time.sleep(1.0)
            except Exception as e:
                print(f"      ❌ App focus failed: {e}")

            # Focus the element
            try:
                if hasattr(element, "AXPress"):
                    element.AXPress()
                elif hasattr(element, "AXSetFocused"):
                    element.AXSetFocused(True)
                else:
                    pos = getattr(element, "AXPosition", None)
                    size = getattr(element, "AXSize", None)
                    if pos and size:
                        cx = int(pos.x + size.width // 2)
                        cy = int(pos.y + size.height // 2)
                        subprocess.run(["cliclick", f"c:{cx},{cy}"])
                    else:
                        raise Exception("No suitable interaction method found")
                time.sleep(1.0)
            except Exception as e:
                return {"success": False, "error": f"Could not focus element: {e}"}

            # Clear then type
            subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "a" using command down'])
            time.sleep(0.25)
            subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke (ASCII character 127)'])
            time.sleep(0.25)
            subprocess.run(["osascript", "-e", f'tell application "System Events" to keystroke "{text}"'])
            time.sleep(0.4)
            subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 36'])
            time.sleep(0.4)

            return {"success": True, "result": f"Typed '{text}' and pressed Enter into {target}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_press_enter(self, target: str) -> Dict[str, Any]:
        """Press Enter key on an element"""
        try:
            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            try:
                if hasattr(element, "AXSetFocused"):
                    element.AXSetFocused(True)
                elif hasattr(element, "AXPress"):
                    element.AXPress()
                else:
                    pos = getattr(element, "AXPosition", None)
                    size = getattr(element, "AXSize", None)
                    if pos and size:
                        cx = int(pos.x + size.width // 2)
                        cy = int(pos.y + size.height // 2)
                        subprocess.run(["cliclick", f"c:{cx},{cy}"])
            except Exception as e:
                print(f"      ⚠️  Could not focus element: {e}")
            time.sleep(0.2)

            subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 36'])
            return {"success": True, "result": f"Pressed Enter on {target}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_select(self, target: str, option: str) -> Dict[str, Any]:
        """Execute a select action (dropdowns, etc.)"""
        try:
            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            if getattr(element, "AXRole", "") == "AXPopUpButton":
                try:
                    if hasattr(element, "AXPress"):
                        element.AXPress()
                    else:
                        pos = getattr(element, "AXPosition", None)
                        size = getattr(element, "AXSize", None)
                        if pos and size:
                            cx = int(pos.x + size.width // 2)
                            cy = int(pos.y + size.height // 2)
                            subprocess.run(["cliclick", f"c:{cx},{cy}"])
                    time.sleep(1.0)

                    option_element = self._find_option(element, option)
                    if option_element:
                        if hasattr(option_element, "AXPress"):
                            option_element.AXPress()
                        else:
                            pos = getattr(option_element, "AXPosition", None)
                            size = getattr(option_element, "AXSize", None)
                            if pos and size:
                                cx = int(pos.x + size.width // 2)
                                cy = int(pos.y + size.height // 2)
                                subprocess.run(["cliclick", f"c:{cx},{cy}"])
                        time.sleep(0.5)
                        return {"success": True, "result": f"Selected '{option}' from {target}"}
                    else:
                        return {"success": False, "error": f"Option '{option}' not found"}
                except Exception as e:
                    return {"success": False, "error": f"Select failed: {e}"}
            else:
                return {"success": False, "error": f"Element {target} is not a selectable element"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_scroll(self, target: str, direction: str) -> Dict[str, Any]:
        """Execute a scroll action"""
        try:
            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            d = direction.lower()
            if d == "up":
                element.AXScrollUp()
            elif d == "down":
                element.AXScrollDown()
            elif d == "left":
                element.AXScrollLeft()
            elif d == "right":
                element.AXScrollRight()
            else:
                return {"success": False, "error": f"Invalid scroll direction: {direction}"}

            time.sleep(0.4)
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
            subprocess.run(["osascript", "-e", f'tell application "System Events" to key code {key_code}'])
            time.sleep(0.3)
            return {"success": True, "result": f"Pressed {key} key"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_keystroke(self, target: str, text: str) -> Dict[str, Any]:
        """Type text and press Enter. If target == 'all', do a system-wide keystroke."""
        try:
            if target == "all":
                # Clear, type, Enter
                subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "a" using command down'])
                time.sleep(0.2)
                subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke (ASCII character 127)'])
                time.sleep(0.2)
                subprocess.run(["osascript", "-e", f'tell application "System Events" to keystroke "{text}"'])
                time.sleep(0.2)
                subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 36'])
                time.sleep(0.3)
                return {"success": True, "result": f"System-wide keystroke: '{text}' + Enter"}

            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            # Focus app owning the element (fixed: check windows, not app directly)
            try:
                app = None
                common_apps = [
                    "Google Chrome",
                    "Safari",
                    "System Settings",
                    "Calculator",
                    "Cursor",
                    "Visual Studio Code",
                    "Mail",
                    "Calendar",
                ]
                for app_name in common_apps:
                    try:
                        test_app = atomac.getAppRefByLocalizedName(app_name)
                        if not test_app:
                            continue
                        for w in test_app.windows():
                            if getattr(w, "AXRole", None) == "AXWindow" and self._element_in_window(element, w):
                                app = test_app
                                break
                        if app:
                            break
                    except Exception:
                        continue

                if app:
                    app.activate()
                    time.sleep(1.0)
            except Exception as e:
                print(f"      ⚠️  App focus failed: {e}")

            try:
                element.AXPress()
                time.sleep(0.4)
            except Exception as e:
                print(f"      ⚠️  Could not click element: {e}")

            subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "a" using command down'])
            time.sleep(0.2)
            subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke (ASCII character 127)'])
            time.sleep(0.2)
            subprocess.run(["osascript", "-e", f'tell application "System Events" to keystroke "{text}"'])
            time.sleep(0.25)
            subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 36'])
            time.sleep(0.25)

            return {"success": True, "result": f"Keystroke navigation: '{text}' + Enter"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_press(self, target: str) -> Dict[str, Any]:
        """Execute a press action (for keys like 'enter')"""
        try:
            if target.lower() in ["enter", "return"]:
                subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 36'])
                time.sleep(0.3)
                return {"success": True, "result": f"Pressed {target} key"}
            else:
                return {"success": False, "error": f"Unknown key: {target}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_generic_action(self, action_type: str, target: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generic actions dynamically with sensible fallbacks"""
        try:
            element = self._find_element(target)
            if not element:
                return {"success": False, "error": f"Element not found: {target}"}

            # Try AX* methods directly
            ax_method = f"AX{action_type.capitalize()}"
            if hasattr(element, ax_method):
                getattr(element, ax_method)()
                return {"success": True, "result": f"Executed {action_type} on {target}"}

            # Press fallback
            if hasattr(element, "AXPress"):
                element.AXPress()
                return {"success": True, "result": f"Pressed {target}"}

            if hasattr(element, "AXPerformAction"):
                element.AXPerformAction("AXPress")
                return {"success": True, "result": f"Performed action on {target}"}

            # Final fallback: coordinate click with cliclick
            pos = getattr(element, "AXPosition", None)
            if pos:
                subprocess.run(["cliclick", f"c:{int(pos.x)},{int(pos.y)}"])
                return {"success": True, "result": f"Clicked {target} at position ({int(pos.x)}, {int(pos.y)})"}
            else:
                return {"success": False, "error": f"Could not get position for {target}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---- Helpers ----

    def _get_bundle_id(self, app_name: str) -> str:
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
        """Find an element by identifier/title/role or by approximate position encoded in ID."""
        try:
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
                    if not app:
                        continue

                    windows = [w for w in app.windows() if getattr(w, "AXRole", None) == "AXWindow"]
                    for window in windows:
                        # By AXIdentifier
                        try:
                            els = window.findAllR(AXIdentifier=target)
                            if els:
                                return els[0]
                        except Exception:
                            pass

                        # By AXTitle
                        try:
                            els = window.findAllR(AXTitle=target)
                            if els:
                                return els[0]
                        except Exception:
                            pass

                        # Manual scan for identifier
                        try:
                            els = window.findAllR()
                            for elem in els:
                                try:
                                    identifier = getattr(elem, "AXIdentifier", "")
                                    if identifier == target:
                                        return elem
                                except Exception:
                                    continue
                        except Exception:
                            pass

                        # Position-encoded ID: e.g., "AXButton_533.0_310.0"
                        if "_" in target and target.count("_") >= 2:
                            try:
                                parts = target.split("_")
                                if len(parts) >= 3:
                                    role = parts[0]
                                    x = float(parts[1])
                                    y = float(parts[2])
                                    els = window.findAllR(AXRole=role)
                                    for elem in els:
                                        pos = getattr(elem, "AXPosition", None)
                                        if pos and abs(pos.x - x) < 10 and abs(pos.y - y) < 10:
                                            return elem
                            except Exception:
                                pass

                        # Role+Title
                        if "button" in target.lower():
                            try:
                                el = window.findFirst(AXRole="AXButton", AXTitle=target)
                                if el:
                                    return el
                            except Exception:
                                pass
                except Exception:
                    continue
            return None
        except Exception as e:
            print(f"      ⚠️  Error finding element {target}: {e}")
            return None

    def _element_in_window(self, element: Any, window: Any) -> bool:
        """Check if an element belongs to a specific window."""
        try:
            for elem in window.findAllR():
                if elem == element:
                    return True
            return False
        except Exception:
            return False

    def _find_option(self, parent_element: Any, option: str) -> Optional[Any]:
        """Find an option within a parent element (for dropdowns)."""
        try:
            children = getattr(parent_element, "AXChildren", None) or []
            for child in children:
                title = getattr(child, "AXTitle", None) or ""
                if option.lower() in title.lower():
                    return child
                grand = getattr(child, "AXChildren", None) or []
                for gc in grand:
                    t = getattr(gc, "AXTitle", None) or ""
                    if option.lower() in t.lower():
                        return gc
            return None
        except Exception as e:
            print(f"      ⚠️  Error finding option {option}: {e}")
            return None

    # ---- Visual verification ----

    def _crop_element_region(self, screenshot_path: str, element_position: tuple, element_size: tuple, padding: int = 20) -> Optional[Image.Image]:
        try:
            img = Image.open(screenshot_path)
            x, y = element_position
            width, height = element_size

            left = max(0, int(x - padding))
            top = max(0, int(y - padding))
            right = min(img.width, int(x + width + padding))
            bottom = min(img.height, int(y + height + padding))

            return img.crop((left, top, right, bottom))
        except Exception as e:
            print(f"      ⚠️  Error cropping image: {e}")
            return None

    def _compare_images(self, img1: Image.Image, img2: Image.Image, threshold: float = 0.05) -> Dict[str, Any]:
        try:
            if img1.size != img2.size:
                img2 = img2.resize(img1.size)

            if img1.mode != "RGB":
                img1 = img1.convert("RGB")
            if img2.mode != "RGB":
                img2 = img2.convert("RGB")

            pixels1 = list(img1.getdata())
            pixels2 = list(img2.getdata())

            total = len(pixels1)
            different = sum(1 for p1, p2 in zip(pixels1, pixels2) if p1 != p2)
            diff_pct = different / total
            changed = diff_pct > threshold

            return {"changed": changed, "difference_percentage": diff_pct, "different_pixels": different, "total_pixels": total}
        except Exception as e:
            print(f"      ⚠️  Error comparing images: {e}")
            return {"changed": False, "error": str(e)}

    def capture_before_screenshot(self, element_id: str, target_app: str = "System Settings") -> Dict[str, Any]:
        try:
            element = self._find_element(element_id)
            if not element:
                return {"success": False, "reason": "Element not found"}

            pos = getattr(element, "AXPosition", None)
            size = getattr(element, "AXSize", None)
            if not pos or not size:
                return {"success": False, "reason": "No position/size data"}

            element_position = (pos.x, pos.y)
            element_size = (size.width, size.height)

            vlm = VLMAnalyzer()
            screenshot = vlm.capture_screenshot(target_app)
            if not screenshot:
                return {"success": False, "reason": "Screenshot failed"}

            cropped = self._crop_element_region(screenshot, element_position, element_size)
            if not cropped:
                return {"success": False, "reason": "Crop failed"}

            cropped.save("before_action_crop.png")
            print(f"      💾 Saved before_action_crop.png")

            return {"success": True, "cropped_image": cropped, "position": element_position, "size": element_size}
        except Exception as e:
            return {"success": False, "reason": f"Error: {e}"}

    def verify_action_visually(self, element_id: str, before_state: Dict[str, Any], target_app: str = "System Settings") -> Dict[str, Any]:
        try:
            print(f"      🔍 Visually verifying action on {element_id}")
            if not before_state.get("success"):
                return {"verified": False, "reason": "No before state"}

            before_crop = before_state["cropped_image"]
            element_position = before_state["position"]
            element_size = before_state["size"]

            time.sleep(0.5)

            vlm = VLMAnalyzer()
            after_screenshot = vlm.capture_screenshot(target_app)
            if not after_screenshot:
                return {"verified": False, "reason": "Screenshot failed"}

            after_crop = self._crop_element_region(after_screenshot, element_position, element_size)
            if not after_crop:
                return {"verified": False, "reason": "Crop failed"}

            after_crop.save("after_action_crop.png")
            print(f"      💾 Saved after_action_crop.png")

            comparison = self._compare_images(before_crop, after_crop)
            if comparison.get("changed"):
                print(f"      ✅ Visual change detected: {comparison['difference_percentage']:.2%} pixels changed")
                return {"verified": True, "reason": "Visual change detected", "comparison": comparison}
            else:
                print(f"      ❌ No visual change detected: {comparison['difference_percentage']:.2%} pixels changed")
                return {"verified": False, "reason": "No visual change detected", "comparison": comparison}
        except Exception as e:
            print(f"      ❌ Visual verification error: {e}")
            return {"verified": False, "reason": f"Error: {e}"}

    # ---- Summaries ----

    def execute_action_sequence(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for i, action in enumerate(actions):
            print(f"   📋 Executing action {i+1}/{len(actions)}")
            result = self.execute_action(action)
            results.append(result)
            if not result.get("success", False):
                print(f"   ⚠️  Action {i+1} failed, continuing with next action")
            time.sleep(0.4)
        return results

    def validate_action(self, action: Dict[str, Any]) -> bool:
        action_type = action.get("action", "").lower()
        target = action.get("target", "")
        if not action_type or not target:
            return False

        element = self._find_element(target)
        if not element:
            return False

        role = getattr(element, "AXRole", None)
        if action_type == "click":
            return role in ["AXButton", "AXPopUpButton", "AXCheckBox", "AXRadioButton"]
        elif action_type == "type":
            return role in ["AXTextField", "AXTextArea"]
        elif action_type == "select":
            return role in ["AXPopUpButton", "AXComboBox"]
        return True

    def get_action_summary(self) -> Dict[str, Any]:
        successful = sum(1 for a in self.action_history if a.success)
        total = len(self.action_history)
        return {
            "total_actions": total,
            "successful_actions": successful,
            "success_rate": (successful / total if total > 0 else 0),
            "action_types": list(set(a.action for a in self.action_history)),
        }
