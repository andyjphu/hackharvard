#!/usr/bin/env python3
"""
Perception Engine - Handles all environmental perception and signal discovery
"""

import time
import psutil
import atomacos as atomac
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


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

    def discover_ui_signals(self, target_app: str = None) -> List[Dict[str, Any]]:
        """Discover all available UI elements and their capabilities"""
        print("   🔍 Scanning UI elements...")

        elements = []

        try:
            if target_app:
                app = atomac.getAppRefByLocalizedName(target_app)
                if not app:
                    print(f"   ❌ App '{target_app}' not found")
                    print(f"   🚀 No UI elements found, attempting to launch {target_app}...")
                    # Try to launch the app
                    app = self._launch_app(target_app)
                    if not app:
                        print(f"   ❌ Could not launch {target_app}")
                        return elements
                    # Wait for app to load
                    time.sleep(3)

                windows = [
                    w for w in app.windows() if getattr(w, "AXRole", None) == "AXWindow"
                ]
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

            # Add contextual information for better LLM understanding
            contextual_title = title or self._get_contextual_title(
                role, element, pos_tuple
            )
            contextual_description = description or self._get_contextual_description(
                role, element, pos_tuple
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
            if 300 < x < 400 and 70 < y < 100:  # Right of search bar (narrower range)
                return "Search Button"
            elif 400 < x < 500 and 70 < y < 100:  # Further right
                return "Action Button"
            elif 500 < x < 600 and 70 < y < 100:  # Even further right
                return "Menu Button"
            elif 600 < x < 800 and 70 < y < 100:  # Far right
                return "Toolbar Button"
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
                lambda: subprocess.run(["open", "-b", self._get_bundle_id(app_name)], check=True),
                # Method 3: Bundle path
                lambda: subprocess.run(["open", self._get_bundle_path(app_name)], check=True),
            ]
            
            for i, method in enumerate(launch_methods):
                try:
                    print(f"      🚀 Trying launch method {i+1} for {app_name}")
                    method()
                    time.sleep(2)  # Wait for app to start
                    
                    # Check if app is now running
                    app = atomac.getAppRefByLocalizedName(app_name)
                    if app:
                        print(f"      ✅ Successfully launched {app_name}")
                        return app
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
