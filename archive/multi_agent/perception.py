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
        max_elements = 50

        try:
            if target_app:
                app = atomac.getAppRefByLocalizedName(target_app)
                if not app:
                    print(f"   ❌ App '{target_app}' not found")
                    return elements

                windows = [
                    w for w in app.windows() if getattr(w, "AXRole", None) == "AXWindow"
                ]
            else:
                # Get all applications
                apps = atomac.getAppRefs()
                windows = []
                for app in apps:
                    try:
                        windows.extend(
                            [
                                w
                                for w in app.windows()
                                if getattr(w, "AXRole", None) == "AXWindow"
                            ]
                        )
                    except:
                        continue

            # Limit to first 2 windows to prevent performance issues
            for window in windows[:2]:
                if len(elements) >= max_elements:
                    break

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
        return [self._signal_to_dict(signal) for signal in elements[:max_elements]]

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
                for element in found_elements[:10]:  # Limit per role
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

            return UISignal(
                id=identifier or f"{role}_{pos_tuple[0]}_{pos_tuple[1]}",
                type=role,
                position=pos_tuple,
                size=size_tuple,
                current_value=value,
                available_options=available_options,
                actions=actions,
                title=title,
                description=description,
                enabled=enabled,
                focused=focused,
            )

        except Exception as e:
            return None

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
