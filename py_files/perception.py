#!/usr/bin/env python3
"""
Perception Engine - Handles all environmental perception and signal discovery
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Third-party libs
import psutil
import atomacos as atomac

# VLM integration (single source of truth)
try:
    from model.gemini import BrowserScreenshotAnalyzer as VLMAnalyzer
    VLM_AVAILABLE = True
except Exception:
    VLM_AVAILABLE = False
    VLMAnalyzer = None
    print("   ⚠️  VLM not available - install model dependencies for visual analysis")


@dataclass
class UISignal:
    """Represents a discovered UI element with all its properties"""
    id: str
    type: str
    position: tuple
    size: tuple
    current_value: Any
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
        self.vlm_analyzer = None

        if VLM_AVAILABLE:
            try:
                self.vlm_analyzer = VLMAnalyzer()
                print("   ✅ VLM analyzer initialized for visual analysis")
            except Exception as e:
                print(f"   ⚠️  VLM initialization failed: {e}")
                self.vlm_analyzer = None

    # -------- UI Discovery --------

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

    def discover_ui_signals(self, target_app: Optional[str] = None) -> List[Dict[str, Any]]:
        """Discover all available UI elements and their capabilities"""
        print("   🔍 Scanning UI elements...")
        self.seen_elements.clear()
        out: List[UISignal] = []

        try:
            windows = []
            if target_app:
                normalized = self._normalize_app_name(target_app)
                print(f"   🎯 Looking for app: {target_app} (normalized: {normalized})")
                try:
                    app = atomac.getAppRefByLocalizedName(normalized)
                except Exception as e:
                    print(f"   ⚠️  Error getting app reference: {e}")
                    app = None

                if not app:
                    print(f"   ❌ App '{normalized}' not found")
                    return []

                windows = [w for w in app.windows() if getattr(w, "AXRole", None) == "AXWindow"]
                print(f"   📊 Found {len(windows)} windows for {normalized}")
            else:
                # Aggregate windows from common apps
                common_apps = [
                    "System Settings", "Calculator", "Google Chrome", "Safari",
                    "Cursor", "Visual Studio Code", "Mail", "Calendar", "Finder"
                ]
                for name in common_apps:
                    try:
                        app = atomac.getAppRefByLocalizedName(name)
                        if not app:
                            continue
                        windows.extend([w for w in app.windows() if getattr(w, "AXRole", None) == "AXWindow"])
                    except Exception:
                        continue

            for window in windows:
                try:
                    out.extend(self._scan_window(window))
                except Exception:
                    continue

        except Exception as e:
            print(f"   ❌ Error scanning elements: {e}")

        return [self._signal_to_dict(s) for s in out]

    def _scan_window(self, window) -> List[UISignal]:
        """Scan a window for interactive elements"""
        elements: List[UISignal] = []
        interactive_roles = [
            "AXButton", "AXPopUpButton", "AXCheckBox", "AXRadioButton",
            "AXTextField", "AXSlider", "AXMenuItem", "AXTabGroup",
            "AXComboBox", "AXList", "AXTable", "AXScrollArea",
        ]

        for role in interactive_roles:
            try:
                found = window.findAllR(AXRole=role) or []
                for el in found:
                    signal = self._create_ui_signal(el, role)
                    if signal and signal.id not in self.seen_elements:
                        elements.append(signal)
                        self.seen_elements.add(signal.id)
            except Exception:
                continue
        print(f"   📊 Found {len(elements)} elements in window")
        return elements

    def _create_ui_signal(self, element, role: str) -> Optional[UISignal]:
        """Create a UISignal from an element"""
        try:
            identifier = getattr(element, "AXIdentifier", None) or ""
            title = getattr(element, "AXTitle", None) or ""
            description = getattr(element, "AXDescription", None) or ""
            value = getattr(element, "AXValue", None) or ""
            position = getattr(element, "AXPosition", None)
            size = getattr(element, "AXSize", None)
            enabled = bool(getattr(element, "AXEnabled", True))
            focused = bool(getattr(element, "AXFocused", False))

            # Dropdown options
            available_options: List[str] = []
            if role == "AXPopUpButton":
                try:
                    children = getattr(element, "AXChildren", None) or []
                    for c in children:
                        t = getattr(c, "AXTitle", None) or ""
                        if t:
                            available_options.append(t)
                except Exception:
                    pass

            # Supported actions
            actions: List[str] = []
            try:
                actions_attr = getattr(element, "AXActions", None) or []
                if isinstance(actions_attr, list):
                    actions = [str(a) for a in actions_attr]
            except Exception:
                pass

            pos_tuple = (getattr(position, "x", 0), getattr(position, "y", 0)) if position else (0, 0)
            size_tuple = (getattr(size, "width", 0), getattr(size, "height", 0)) if size else (0, 0)

            # Fallback label logic
            label = title or description or getattr(element, "AXHelp", "") or str(value) or role
            label = str(label).strip()

            return UISignal(
                id=identifier or f"{role}_{pos_tuple[0]}_{pos_tuple[1]}",
                type=role,
                position=pos_tuple,
                size=size_tuple,
                current_value=value,
                available_options=available_options,
                actions=actions,
                title=label,
                description=description or "",
                enabled=enabled,
                focused=focused,
            )
        except Exception:
            return None

    # -------- System / Context --------

    def get_system_state(self) -> SystemState:
        """Get current system state"""
        print("   📊 Monitoring system state...")
        try:
            battery = psutil.sensors_battery()
            battery_level = int(getattr(battery, "percent", 0)) if battery else 0
            power_source = "battery" if (battery and not battery.power_plugged) else "power"

            # Very rough network indication
            ifaces = psutil.net_if_stats()
            network_status = "connected" if any(s.isup for s in ifaces.values()) else "disconnected"

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

    def get_context(self, target_app: Optional[str] = None) -> Dict[str, Any]:
        """Get current application context"""
        print("   🎯 Analyzing context...")
        try:
            if target_app:
                app = atomac.getAppRefByLocalizedName(target_app)
                if app:
                    windows = [w for w in app.windows() if getattr(w, "AXRole", None) == "AXWindow"]
                    if windows:
                        window = windows[0]
                        return {
                            "app_name": target_app,
                            "window_title": getattr(window, "AXTitle", ""),
                            "focused_element": self._get_focused_element(window),
                            "timestamp": time.time(),
                        }
            return {"app_name": target_app or "Unknown", "window_title": "", "focused_element": "", "timestamp": time.time()}
        except Exception as e:
            print(f"   ⚠️  Error getting context: {e}")
            return {"app_name": "Unknown", "window_title": "", "focused_element": "", "timestamp": time.time()}

    @staticmethod
    def _get_focused_element(window) -> str:
        try:
            focused = window.findFirst(AXFocused=True)
            if focused:
                return getattr(focused, "AXTitle", "") or getattr(focused, "AXIdentifier", "")
        except Exception:
            pass
        return ""

    # -------- Visual / Correlation --------

    def capture_visual_analysis(self, target_app: str, goal: str = "") -> Optional[VisualAnalysis]:
        """Capture and analyze visual elements using VLM with throttling"""
        if not self.vlm_analyzer:
            return None
        try:
            print("   📸 Capturing visual analysis...")

            # Throttle to avoid rate limits
            now = time.time()
            if hasattr(self, "_last_vlm_time"):
                delta = now - self._last_vlm_time
                if delta < 5.0:
                    time.sleep(5.0 - delta)
            self._last_vlm_time = time.time()

            screenshot_path = self.vlm_analyzer.capture_screenshot(target_app)
            if not screenshot_path:
                print("   ❌ Failed to capture screenshot for VLM analysis")
                return None

            analysis = self.vlm_analyzer.analyze_screenshot(screenshot_path, goal)
            if "error" in analysis:
                print(f"   ❌ VLM analysis failed: {analysis['error']}")
                return None

            visuals: List[VisualElement] = []
            for el in analysis.get("interactive_elements", []):
                visuals.append(
                    VisualElement(
                        type=el.get("type", "unknown"),
                        position=el.get("position", "unknown"),
                        text=el.get("text", ""),
                        purpose=el.get("purpose", ""),
                        characteristics=el.get("characteristics", ""),
                        task_relevant=bool(el.get("task_relevant", False)),
                        coordinates=el.get("coordinates", None),
                    )
                )

            return VisualAnalysis(
                screen_description=analysis.get("screen_description", ""),
                interactive_elements=visuals,
                safety_warnings=analysis.get("safety_warnings", []),
                alternative_methods=analysis.get("alternative_methods", []),
                task_context=goal,
            )
        except Exception as e:
            print(f"   ❌ VLM analysis error: {e}")
            return None

    def correlate_accessibility_visual(self, ui_signals: List[Dict], visual_analysis: VisualAnalysis) -> Dict[str, Any]:
        """Correlate accessibility elements with visual elements"""
        correlations = []
        for ui in ui_signals:
            ui_pos = ui.get("position", (0, 0))
            ui_title = (ui.get("title") or "").lower()
            ui_type = (ui.get("type") or "").lower()
            best, score = None, 0

            for vis in visual_analysis.interactive_elements:
                s = 0
                if vis.coordinates:
                    vx = vis.coordinates.get("click_x", 0)
                    vy = vis.coordinates.get("click_y", 0)
                    dist = ((ui_pos[0] - vx) ** 2 + (ui_pos[1] - vy) ** 2) ** 0.5
                    if dist < 50:
                        s += 3
                if ui_title and vis.text:
                    ut = ui_title.strip().lower()
                    vt = vis.text.strip().lower()
                    if ut == vt or (len(ut) > 3 and ut in vt) or (len(vt) > 3 and vt in ut):
                        s += 2
                if ui_type in (vis.type or "").lower() or (vis.type or "").lower() in ui_type:
                    s += 1
                if s > score:
                    best, score = vis, s

            if best and score > 0:
                correlations.append(
                    {"accessibility_id": ui.get("id"), "visual_element": best, "correlation_score": score, "ui_signal": ui}
                )

        # unique by text/type/purpose
        unique, seen = [], set()
        correlations.sort(key=lambda x: x["correlation_score"], reverse=True)
        for c in correlations:
            v = c["visual_element"]
            key = f"{v.text}|{v.type}|{v.purpose}"
            if key not in seen:
                seen.add(key)
                unique.append(c)

        return {
            "correlations": unique,
            "total_ui_signals": len(ui_signals),
            "total_visual_elements": len(visual_analysis.interactive_elements),
            "matched_elements": len(unique),
        }

    # -------- Hybrid --------

    def get_hybrid_perception(self, target_app: Optional[str], goal: str = "") -> Dict[str, Any]:
        """Get combined accessibility and visual perception data"""
        print("   🔍 Gathering hybrid perception (accessibility + visual)...")

        ui_signals = self.discover_ui_signals(target_app)
        system_state = self.get_system_state()
        context = self.get_context(target_app)

        visual_analysis = self.capture_visual_analysis(target_app, goal) if target_app else None
        correlations = None
        if visual_analysis:
            correlations = self.correlate_accessibility_visual(ui_signals, visual_analysis)

        return {
            "ui_signals": ui_signals,
            "system_state": system_state,
            "context": context,
            "visual_analysis": visual_analysis,
            "correlations": correlations,
            "perception_type": "hybrid" if visual_analysis else "accessibility_only",
        }

    # -------- Serialization --------

    @staticmethod
    def _signal_to_dict(signal: UISignal) -> Dict[str, Any]:
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
