#!/usr/bin/env python3
"""
Perception Engine - Handles all environmental perception and signal discovery
"""

import time
import psutil
import atomacos as atomac
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import os
import sys

# Add model directory to path for VLM integration
sys.path.append(os.path.join(os.path.dirname(__file__), "model"))
try:
    from model.gemini import BrowserScreenshotAnalyzer

    VLM_AVAILABLE = True
except ImportError:
    VLM_AVAILABLE = False
    print("   ⚠️  VLM not available - install model dependencies for visual analysis")


@dataclass
class UISignal:
    """Represents a discovered UI element with all its properties"""

    id: str
    type: str
    position: tuple
    size: tuple
    current_value: str
    available_options: List[str]
    actions: List[str]
    title: str = ""
    description: str = ""
    enabled: bool = True
    focused: bool = False


@dataclass
class SystemState:
    """Current system state information"""

    battery_level: int
    power_source: str
    network_status: str
    time: str
    memory_usage: float
    cpu_usage: float


@dataclass
class VisualElement:
    """Represents a visually identified UI element from VLM analysis"""

    type: str
    position: str
    text: str
    purpose: str
    characteristics: str
    task_relevant: bool = False
    coordinates: Optional[Dict[str, int]] = None


@dataclass
class VisualAnalysis:
    """Complete visual analysis from VLM"""

    screen_description: str
    interactive_elements: List[VisualElement]
    safety_warnings: List[str]
    alternative_methods: List[str]
    task_context: str = ""


class PerceptionEngine:
    """
    Handles all perception tasks:
    - UI element discovery
    - System state monitoring
    - Context analysis
    - Signal processing
    """

    def __init__(self):
        self.seen_elements = set()
        self.perception_history = []

        # Initialize VLM if available
        self.vlm_analyzer = None
        if VLM_AVAILABLE:
            try:
                self.vlm_analyzer = BrowserScreenshotAnalyzer()
                print("   ✅ VLM analyzer initialized for visual analysis")
            except Exception as e:
                print(f"   ⚠️  VLM initialization failed: {e}")
                self.vlm_analyzer = None

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

    def discover_ui_signals(self, target_app: str = None) -> List[Dict[str, Any]]:
        """Discover all available UI elements and their capabilities"""
        print("   🔍 Scanning UI elements...")

        # Clear seen elements to ensure fresh scanning on each call
        self.seen_elements.clear()
        elements = []

        try:
            if target_app:
                # Normalize the app name to handle common variations
                normalized_app_name = self._normalize_app_name(target_app)
                print(
                    f"   🎯 Looking for app: {target_app} (normalized: {normalized_app_name})"
                )
                try:
                    app = atomac.getAppRefByLocalizedName(normalized_app_name)
                except Exception as e:
                    print(f"   ⚠️  Error getting app reference: {e}")
                    app = None

                if not app:
                    print(f"   ❌ App '{normalized_app_name}' not found")
                    print(
                        f"   🚀 No UI elements found, attempting to launch {normalized_app_name}..."
                    )
                    # Try to launch the app
                    app = self._launch_app(normalized_app_name)
                    if not app:
                        print(f"   ❌ Could not launch {target_app}")
                        return elements
                    # Wait for app to load
                    time.sleep(3)

                windows = [
                    w for w in app.windows() if getattr(w, "AXRole", None) == "AXWindow"
                ]
                print(f"   📊 Found {len(windows)} windows for {normalized_app_name}")
            else:
                # Get all applications dynamically
                windows = []
                try:
                    # Try to get all running applications
                    all_apps = (
                        atomac.getAppRefs() if hasattr(atomac, "getAppRefs") else []
                    )
                    for app in all_apps:
                        try:
                            app_windows = [
                                w
                                for w in app.windows()
                                if getattr(w, "AXRole", None) == "AXWindow"
                            ]
                            windows.extend(app_windows)
                        except:
                            continue
                except:
                    # Fallback to common apps if getAppRefs doesn't work
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
                                app_windows = [
                                    w
                                    for w in app.windows()
                                    if getattr(w, "AXRole", None) == "AXWindow"
                                ]
                                windows.extend(app_windows)
                        except:
                            continue

            # Scan all available windows without artificial limits
            for window in windows:
                try:
                    window_elements = self._scan_window(window)
                    elements.extend(window_elements)
                    print(f"   📊 Found {len(window_elements)} elements in window")
                except Exception as e:
                    print(f"   ⚠️  Error scanning window: {e}")
                    continue

        except Exception as e:
            print(f"   ❌ Error scanning elements: {e}")

        # Convert to dictionaries for JSON serialization
        return [self._signal_to_dict(signal) for signal in elements]

    def _scan_window(self, window) -> List[UISignal]:
        """Scan a window for interactive elements"""
        elements = []

        interactive_roles = [
            "AXButton",
            "AXPopUpButton",
            "AXCheckBox",
            "AXRadioButton",
            "AXTextField",
            "AXSlider",
            "AXMenuItem",
            "AXTabGroup",
            "AXComboBox",
            "AXList",
            "AXTable",
            "AXScrollArea",
        ]

        for role in interactive_roles:
            try:
                found_elements = window.findAllR(AXRole=role) or []
                # Scan all elements without artificial limits
                for element in found_elements:
                    try:
                        signal = self._create_ui_signal(element, role)
                        if signal and signal.id not in self.seen_elements:
                            elements.append(signal)
                            self.seen_elements.add(signal.id)
                    except Exception as e:
                        continue
            except Exception as e:
                continue

        return elements

    def _create_ui_signal(self, element, role: str) -> Optional[UISignal]:
        """Create a UISignal from an element"""
        try:
            # Get element properties
            identifier = getattr(element, "AXIdentifier", None) or ""
            title = getattr(element, "AXTitle", None) or ""
            description = getattr(element, "AXDescription", None) or ""
            value = getattr(element, "AXValue", None) or ""
            position = getattr(element, "AXPosition", None)
            size = getattr(element, "AXSize", None)
            enabled = getattr(element, "AXEnabled", True)
            focused = getattr(element, "AXFocused", False)

            # Get available options for dropdowns
            available_options = []
            if role == "AXPopUpButton":
                try:
                    children = getattr(element, "AXChildren", None) or []
                    for child in children:
                        child_title = getattr(child, "AXTitle", None) or ""
                        if child_title:
                            available_options.append(child_title)
                except:
                    pass

            # Get available actions
            actions = []
            try:
                actions_attr = getattr(element, "AXActions", None) or []
                if isinstance(actions_attr, list):
                    actions = [str(action) for action in actions_attr]
            except:
                pass

            # Create position and size tuples
            pos_tuple = (position.x, position.y) if position else (0, 0)
            size_tuple = (size.width, size.height) if size else (0, 0)

            # Prioritize real accessibility labels, fall back to contextual guessing
            contextual_title = self._get_best_title(element, role, pos_tuple)
            contextual_description = self._get_best_description(
                element, role, pos_tuple
            )

            return UISignal(
                id=identifier or f"{role}_{pos_tuple[0]}_{pos_tuple[1]}",
                type=role,
                position=pos_tuple,
                size=size_tuple,
                current_value=value,
                available_options=available_options,
                actions=actions,
                title=contextual_title,
                description=contextual_description,
                enabled=enabled,
                focused=focused,
            )

        except Exception as e:
            return None

    def _get_best_title(self, element, role: str, pos_tuple: tuple) -> str:
        """Get the best available title from accessibility API or fallback to contextual"""
        try:
            # 1. Try AXTitle (most common)
            title = getattr(element, "AXTitle", None)
            if title and title.strip():
                return title.strip()

            # 2. Try AXDescription
            description = getattr(element, "AXDescription", None)
            if description and description.strip():
                return description.strip()

            # 3. Try AXHelp
            help_text = getattr(element, "AXHelp", None)
            if help_text and help_text.strip():
                return help_text.strip()

            # 4. Try AXValue (for some elements)
            value = getattr(element, "AXValue", None)
            if value and str(value).strip():
                return str(value).strip()

            # 5. Try AXRoleDescription
            role_desc = getattr(element, "AXRoleDescription", None)
            if role_desc and role_desc.strip():
                return role_desc.strip()

            # 6. Fall back to contextual guessing
            return self._get_contextual_title(role, element, pos_tuple)

        except Exception:
            # If anything fails, use contextual guessing
            return self._get_contextual_title(role, element, pos_tuple)

    def _get_best_description(self, element, role: str, pos_tuple: tuple) -> str:
        """Get the best available description from accessibility API or fallback to contextual"""
        try:
            # 1. Try AXDescription (most common)
            description = getattr(element, "AXDescription", None)
            if description and description.strip():
                return description.strip()

            # 2. Try AXHelp
            help_text = getattr(element, "AXHelp", None)
            if help_text and help_text.strip():
                return help_text.strip()

            # 3. Try AXTitle (sometimes used for descriptions)
            title = getattr(element, "AXTitle", None)
            if title and title.strip():
                return title.strip()

            # 4. Try AXValue (for some elements)
            value = getattr(element, "AXValue", None)
            if value and str(value).strip():
                return str(value).strip()

            # 5. Fall back to contextual guessing
            return self._get_contextual_description(role, element, pos_tuple)

        except Exception:
            # If anything fails, use contextual guessing
            return self._get_contextual_description(role, element, pos_tuple)

    def _get_contextual_title(self, role: str, element, pos_tuple: tuple) -> str:
        """Generate contextual title based on role and position"""
        x, y = pos_tuple

        # Browser-specific contextual titles
        if role == "AXTextField":
            if 150 < x < 400 and 70 < y < 100:  # Typical search bar position
                return "Search Bar"
            elif 200 < x < 600 and 100 < y < 200:  # Address bar area
                return "Address Bar"
            else:
                return "Text Input Field"
        elif role == "AXButton":
            # More flexible button labeling based on position
            if 70 < y < 120:  # Top toolbar area
                if 300 < x < 500:  # Near search area
                    return "Search Button"
                elif 500 < x < 700:  # Middle toolbar
                    return "Action Button"
                elif 700 < x < 900:  # Right toolbar
                    return "Toolbar Button"
                else:
                    return "Toolbar Button"
            elif 120 < y < 200:  # Secondary toolbar
                return "Action Button"
            else:
                return "Button"
        elif role == "AXPopUpButton":
            return "Dropdown Menu"
        elif role == "AXRadioButton":
            return "Option Button"
        else:
            return f"{role} Element"

    def _get_contextual_description(self, role: str, element, pos_tuple: tuple) -> str:
        """Generate contextual description based on role and position"""
        x, y = pos_tuple

        if role == "AXTextField":
            if 150 < x < 400 and 70 < y < 100:
                return "Main search input field for entering search queries"
            else:
                return "Text input field for user data entry"
        elif role == "AXButton":
            if 300 < x < 400 and 70 < y < 100:
                return "Button to execute search or submit form"
            elif 400 < x < 500 and 70 < y < 100:
                return "Secondary action button (may be download/install button)"
            elif 500 < x < 600 and 70 < y < 100:
                return "Menu or toolbar button"
            else:
                return "Interactive button element"
        elif role == "AXPopUpButton":
            return "Dropdown menu for selecting options"
        else:
            return f"Interactive {role.lower()} element"

    def _launch_app(self, app_name: str) -> Optional[Any]:
        """Launch an application and return the app reference"""
        try:
            import subprocess

            # Try different launch methods
            launch_methods = [
                # Method 1: Direct app name
                lambda: subprocess.run(["open", "-a", app_name], check=True),
                # Method 2: Bundle ID
                lambda: subprocess.run(
                    ["open", "-b", self._get_bundle_id(app_name)], check=True
                ),
                # Method 3: Bundle path
                lambda: subprocess.run(
                    ["open", self._get_bundle_path(app_name)], check=True
                ),
            ]

            for i, method in enumerate(launch_methods):
                try:
                    print(f"      🚀 Trying launch method {i+1} for {app_name}")
                    method()
                    time.sleep(2)  # Wait for app to start

                    # Check if app is now running
                    try:
                        app = atomac.getAppRefByLocalizedName(app_name)
                        if app:
                            print(f"      ✅ Successfully launched {app_name}")
                            return app
                    except Exception as e:
                        print(f"      ⚠️  Error checking if app launched: {e}")
                        # Try with normalized name
                        try:
                            normalized_name = self._normalize_app_name(app_name)
                            app = atomac.getAppRefByLocalizedName(normalized_name)
                            if app:
                                print(
                                    f"      ✅ Successfully launched {normalized_name}"
                                )
                                return app
                        except:
                            pass
                except Exception as e:
                    print(f"      ⚠️  Launch method {i+1} failed: {e}")
                    continue

            print(f"      ❌ All launch methods failed for {app_name}")
            return None

        except Exception as e:
            print(f"      ❌ Error launching {app_name}: {e}")
            return None

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

    def _get_bundle_path(self, app_name: str) -> str:
        """Get bundle path for common apps"""
        bundle_paths = {
            "Calculator": "/Applications/Calculator.app",
            "Numbers": "/Applications/Numbers.app",
            "Google Chrome": "/Applications/Google Chrome.app",
            "Safari": "/Applications/Safari.app",
            "System Settings": "/System/Applications/System Settings.app",
            "Mail": "/Applications/Mail.app",
            "Calendar": "/Applications/Calendar.app",
            "Finder": "/System/Library/CoreServices/Finder.app",
            "Terminal": "/Applications/Utilities/Terminal.app",
        }
        return bundle_paths.get(app_name, "")

    def _signal_to_dict(self, signal: UISignal) -> Dict[str, Any]:
        """Convert UISignal to dictionary for JSON serialization"""
        return {
            "id": signal.id,
            "type": signal.type,
            "position": signal.position,
            "size": signal.size,
            "current_value": signal.current_value,
            "available_options": signal.available_options,
            "actions": signal.actions,
            "title": signal.title,
            "description": signal.description,
            "enabled": signal.enabled,
            "focused": signal.focused,
        }

    def get_system_state(self) -> SystemState:
        """Get current system state"""
        print("   📊 Monitoring system state...")

        try:
            battery = psutil.sensors_battery()
            battery_level = int(battery.percent) if battery else 0
            power_source = (
                "battery" if battery and not battery.power_plugged else "power"
            )

            network_status = "connected" if psutil.net_if_stats() else "disconnected"

            return SystemState(
                battery_level=battery_level,
                power_source=power_source,
                network_status=network_status,
                time=time.strftime("%H:%M"),
                memory_usage=psutil.virtual_memory().percent,
                cpu_usage=psutil.cpu_percent(),
            )
        except Exception as e:
            print(f"   ⚠️  Error getting system state: {e}")
            return SystemState(0, "unknown", "unknown", "00:00", 0, 0)

    def get_context(self, target_app: str = None) -> Dict[str, Any]:
        """Get current application context"""
        print("   🎯 Analyzing context...")

        try:
            if target_app:
                app = atomac.getAppRefByLocalizedName(target_app)
                if app:
                    windows = [
                        w
                        for w in app.windows()
                        if getattr(w, "AXRole", None) == "AXWindow"
                    ]
                    if windows:
                        window = windows[0]
                        return {
                            "app_name": target_app,
                            "window_title": getattr(window, "AXTitle", ""),
                            "focused_element": self._get_focused_element(window),
                            "timestamp": time.time(),
                        }

            return {
                "app_name": target_app or "Unknown",
                "window_title": "",
                "focused_element": "",
                "timestamp": time.time(),
            }
        except Exception as e:
            print(f"   ⚠️  Error getting context: {e}")
            return {
                "app_name": "Unknown",
                "window_title": "",
                "focused_element": "",
                "timestamp": time.time(),
            }

    def _get_focused_element(self, window) -> str:
        """Get currently focused element"""
        try:
            focused = window.findFirst(AXFocused=True)
            if focused:
                return getattr(focused, "AXTitle", "") or getattr(
                    focused, "AXIdentifier", ""
                )
        except:
            pass
        return ""

    def identify_constraints(self) -> List[str]:
        """Identify system constraints"""
        constraints = []

        # Check system resources
        if psutil.virtual_memory().percent > 80:
            constraints.append("high_memory_usage")
        if psutil.cpu_percent() > 80:
            constraints.append("high_cpu_usage")

        # Check battery
        battery = psutil.sensors_battery()
        if battery and battery.percent < 20:
            constraints.append("low_battery")

        return constraints

    def get_perception_summary(self) -> Dict[str, Any]:
        """Get a summary of current perception capabilities"""
        return {
            "elements_discovered": len(self.seen_elements),
            "perception_history_size": len(self.perception_history),
            "constraints": self.identify_constraints(),
        }

    def capture_visual_analysis(
        self, target_app: str, goal: str = ""
    ) -> Optional[VisualAnalysis]:
        """Capture and analyze visual elements using VLM with throttling"""
        if not self.vlm_analyzer:
            return None

        try:
            print("   📸 Capturing visual analysis...")

            # Throttle VLM requests to avoid 429 rate limits
            current_time = time.time()
            if hasattr(self, "_last_vlm_request_time"):
                time_since_last = current_time - self._last_vlm_request_time
                if time_since_last < 5.0:  # 5 second throttle
                    wait_time = 5.0 - time_since_last
                    print(
                        f"   ⏳ Throttling VLM request for {wait_time:.1f}s to avoid rate limits..."
                    )
                    time.sleep(wait_time)

            self._last_vlm_request_time = time.time()

            # Capture screenshot of focused window
            screenshot_path = self.vlm_analyzer.capture_screenshot(target_app)
            if not screenshot_path:
                print("   ❌ Failed to capture screenshot for VLM analysis")
                return None

            # Analyze with VLM
            analysis_result = self.vlm_analyzer.analyze_screenshot(
                screenshot_path, goal
            )

            if "error" in analysis_result:
                print(f"   ❌ VLM analysis failed: {analysis_result['error']}")
                return None

            # Convert to our data structures
            visual_elements = []
            for element_data in analysis_result.get("interactive_elements", []):
                visual_element = VisualElement(
                    type=element_data.get("type", "unknown"),
                    position=element_data.get("position", "unknown"),
                    text=element_data.get("text", ""),
                    purpose=element_data.get("purpose", ""),
                    characteristics=element_data.get("characteristics", ""),
                    task_relevant=element_data.get("task_relevant", False),
                    coordinates=element_data.get("coordinates", {}),
                )
                visual_elements.append(visual_element)

            visual_analysis = VisualAnalysis(
                screen_description=analysis_result.get("screen_description", ""),
                interactive_elements=visual_elements,
                safety_warnings=analysis_result.get("safety_warnings", []),
                alternative_methods=analysis_result.get("alternative_methods", []),
                task_context=goal,
            )

            print(
                f"   ✅ VLM analysis complete: {len(visual_elements)} visual elements"
            )
            return visual_analysis

        except Exception as e:
            print(f"   ❌ VLM analysis error: {e}")
            return None

    def correlate_accessibility_visual(
        self, ui_signals: List[Dict], visual_analysis: VisualAnalysis
    ) -> Dict[str, Any]:
        """Correlate accessibility elements with visual elements"""
        correlations = []

        for ui_signal in ui_signals:
            ui_pos = ui_signal.get("position", (0, 0))
            ui_title = ui_signal.get("title", "").lower()
            ui_type = ui_signal.get("type", "").lower()

            best_match = None
            best_score = 0

            for visual_element in visual_analysis.interactive_elements:
                # Calculate correlation score
                score = 0

                # Position correlation (if coordinates available)
                if visual_element.coordinates:
                    vis_x = visual_element.coordinates.get("click_x", 0)
                    vis_y = visual_element.coordinates.get("click_y", 0)
                    distance = (
                        (ui_pos[0] - vis_x) ** 2 + (ui_pos[1] - vis_y) ** 2
                    ) ** 0.5
                    if distance < 50:  # Within 50 pixels
                        score += 3

                # Text correlation (be more selective)
                if ui_title and visual_element.text:
                    ui_title_clean = ui_title.strip().lower()
                    vis_text_clean = visual_element.text.strip().lower()

                    # Only match if there's a meaningful overlap (not just generic text)
                    if (
                        ui_title_clean == vis_text_clean  # Exact match
                        or (
                            len(ui_title_clean) > 3 and ui_title_clean in vis_text_clean
                        )  # Meaningful substring
                        or (
                            len(vis_text_clean) > 3 and vis_text_clean in ui_title_clean
                        )  # Meaningful substring
                    ):
                        score += 2
                    # Penalize generic matches
                    elif ui_title_clean in [
                        "button",
                        "turn off",
                        "click",
                    ] or vis_text_clean in ["button", "turn off", "click"]:
                        score -= 1  # Penalize generic matches

                # Type correlation
                if (
                    ui_type in visual_element.type.lower()
                    or visual_element.type.lower() in ui_type
                ):
                    score += 1

                # Purpose correlation
                if (
                    ui_signal.get("description", "").lower()
                    in visual_element.purpose.lower()
                ):
                    score += 1

                if score > best_score:
                    best_score = score
                    best_match = visual_element

            if best_match and best_score > 0:
                correlations.append(
                    {
                        "accessibility_id": ui_signal.get("id"),
                        "visual_element": best_match,
                        "correlation_score": best_score,
                        "ui_signal": ui_signal,
                    }
                )

        # Remove duplicate correlations (multiple accessibility elements matching same visual element)
        unique_correlations = []
        used_visual_elements = set()

        # Sort by correlation score (highest first)
        correlations.sort(key=lambda x: x["correlation_score"], reverse=True)

        for correlation in correlations:
            visual_element = correlation["visual_element"]
            visual_key = (
                f"{visual_element.text}_{visual_element.type}_{visual_element.purpose}"
            )

            if visual_key not in used_visual_elements:
                unique_correlations.append(correlation)
                used_visual_elements.add(visual_key)

        return {
            "correlations": unique_correlations,
            "total_ui_signals": len(ui_signals),
            "total_visual_elements": len(visual_analysis.interactive_elements),
            "matched_elements": len(unique_correlations),
        }

    def get_hybrid_perception(self, target_app: str, goal: str = "") -> Dict[str, Any]:
        """Get combined accessibility and visual perception data"""
        print("   🔍 Gathering hybrid perception (accessibility + visual)...")

        # Get accessibility data
        ui_signals = self.discover_ui_signals(target_app)
        system_state = self.get_system_state()

        # Get visual analysis
        visual_analysis = self.capture_visual_analysis(target_app, goal)

        # Correlate the two
        correlations = None
        if visual_analysis:
            correlations = self.correlate_accessibility_visual(
                ui_signals, visual_analysis
            )

        return {
            "ui_signals": ui_signals,
            "system_state": system_state,
            "visual_analysis": visual_analysis,
            "correlations": correlations,
            "perception_type": "hybrid" if visual_analysis else "accessibility_only",
        }
