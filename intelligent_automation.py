#!/usr/bin/env python3
"""
Intelligent UI Automation System
Implements the architecture for LLM-driven UI automation with signal discovery and knowledge integration
"""

import json
import time
import psutil
import requests
from typing import Dict, List, Any, Optional
import atomacos as atomac
from dataclasses import dataclass
import sys
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


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


class SignalCollector:
    """Discovers and presents all available UI signals to the LLM"""

    def __init__(self):
        self.seen_elements = set()

    def discover_ui_signals(self, target_app: str = None) -> Dict[str, Any]:
        """Discover all available UI elements and their capabilities"""
        print("🔍 Discovering UI signals...")

        signals = {
            "interactive_elements": self._scan_interactive_elements(target_app),
            "system_state": self._get_system_state(),
            "application_context": self._get_app_context(target_app),
            "available_actions": self._identify_actions(),
            "constraints": self._identify_constraints(),
        }

        print(
            f"✅ Discovered {len(signals['interactive_elements'])} interactive elements"
        )
        return signals

    def _scan_interactive_elements(self, target_app: str = None) -> List[UISignal]:
        """Find all clickable, typeable, selectable elements with timeout protection"""
        elements = []
        max_elements = 50  # Limit total elements to prevent performance issues

        try:
            if target_app:
                app = atomac.getAppRefByLocalizedName(target_app)
                if not app:
                    print(f"❌ App '{target_app}' not found")
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
                    print(f"   ⚠️  Reached limit of {max_elements} elements")
                    break

                try:
                    window_elements = self._scan_window(window)
                    elements.extend(window_elements)
                    print(f"   📊 Found {len(window_elements)} elements in window")
                except Exception as e:
                    print(f"   ⚠️  Error scanning window: {e}")
                    continue

        except Exception as e:
            print(f"❌ Error scanning elements: {e}")

        return elements[:max_elements]  # Ensure we don't exceed the limit

    def _scan_window(self, window) -> List[UISignal]:
        """Scan a window for interactive elements with optimized approach"""
        elements = []

        # Get all interactive element types
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
                # Use findFirst with limit to avoid deep recursion
                found_elements = window.findAllR(AXRole=role) or []
                for element in found_elements[
                    :10
                ]:  # Limit to first 10 elements per role
                    try:
                        signal = self._create_ui_signal(element, role)
                        if signal and signal.id not in self.seen_elements:
                            elements.append(signal)
                            self.seen_elements.add(signal.id)
                    except Exception as e:
                        continue
            except Exception as e:
                print(f"   ⚠️  Error scanning {role}: {e}")
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

            # Get available options for dropdowns, etc.
            available_options = []
            if role == "AXPopUpButton":
                try:
                    # Try to get menu items
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

    def _get_system_state(self) -> SystemState:
        """Get current system state"""
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
            return SystemState(0, "unknown", "unknown", "00:00", 0, 0)

    def _get_app_context(self, target_app: str = None) -> Dict[str, Any]:
        """Get current application context"""
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
                        }

            return {
                "app_name": target_app or "Unknown",
                "window_title": "",
                "focused_element": "",
            }
        except:
            return {"app_name": "Unknown", "window_title": "", "focused_element": ""}

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

    def _identify_actions(self) -> List[str]:
        """Identify available automation actions"""
        return [
            "click",
            "double_click",
            "right_click",
            "type",
            "select",
            "scroll",
            "drag",
            "hover",
            "focus",
            "press_key",
        ]

    def _identify_constraints(self) -> List[str]:
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


class KnowledgeIntegrator:
    """Provides external context and domain knowledge to the LLM"""

    def __init__(self):
        self.search_cache = {}

    def gather_context(
        self, user_goal: str, current_signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gather relevant knowledge for the task"""
        print("🧠 Gathering contextual knowledge...")

        return {
            "web_search_results": self._search_web(user_goal),
            "domain_knowledge": self._get_domain_knowledge(user_goal),
            "best_practices": self._get_best_practices(user_goal),
            "system_recommendations": self._get_system_recommendations(current_signals),
        }

    def _search_web(self, query: str) -> List[Dict[str, str]]:
        """Search for relevant information (placeholder implementation)"""
        # In a real implementation, this would use web search APIs
        search_queries = [
            f"{query} best practices",
            f"{query} automation techniques",
            f"{query} common issues",
            f"{query} optimization tips",
        ]

        # For now, return mock data
        return [
            {"query": q, "results": f"Mock search results for: {q}", "confidence": 0.8}
            for q in search_queries
        ]

    def _get_domain_knowledge(self, goal: str) -> Dict[str, Any]:
        """Get domain-specific knowledge"""
        knowledge_base = {
            "battery_optimization": {
                "low_power_mode": "Reduces background activity and performance",
                "screen_brightness": "Major battery drain factor",
                "background_apps": "Can significantly impact battery life",
            },
            "security_settings": {
                "filevault": "Encrypts entire disk for security",
                "firewall": "Blocks unauthorized network access",
                "touch_id": "Biometric authentication method",
            },
            "accessibility": {
                "voiceover": "Screen reader for visual impairment",
                "zoom": "Magnification for better visibility",
                "high_contrast": "Improved text readability",
            },
        }

        # Find relevant knowledge
        relevant_knowledge = {}
        for domain, knowledge in knowledge_base.items():
            if any(keyword in goal.lower() for keyword in domain.split("_")):
                relevant_knowledge.update(knowledge)

        return relevant_knowledge

    def _get_best_practices(self, goal: str) -> List[str]:
        """Get best practices for the goal"""
        practices = {
            "battery": [
                "Enable Low Power Mode when battery is low",
                "Reduce screen brightness to save power",
                "Close unnecessary background applications",
                "Use 'Only on Battery' for Low Power Mode",
            ],
            "security": [
                "Enable FileVault for disk encryption",
                "Use strong, unique passwords",
                "Enable two-factor authentication",
                "Keep system and apps updated",
            ],
            "accessibility": [
                "Test accessibility features with actual users",
                "Provide multiple input methods",
                "Ensure sufficient contrast ratios",
                "Offer customization options",
            ],
        }

        # Find relevant practices
        relevant_practices = []
        for category, practice_list in practices.items():
            if category in goal.lower():
                relevant_practices.extend(practice_list)

        return relevant_practices

    def _get_system_recommendations(self, signals: Dict[str, Any]) -> List[str]:
        """Get system-specific recommendations"""
        recommendations = []

        system_state = signals.get("system_state")
        constraints = signals.get("constraints", [])

        if "low_battery" in constraints:
            recommendations.append("Consider enabling Low Power Mode")

        if system_state and system_state.battery_level < 30:
            recommendations.append("Battery is low - optimize power settings")

        if "high_memory_usage" in constraints:
            recommendations.append("Close unnecessary applications")

        return recommendations


class LLMPlanner:
    """Processes all signals and creates intelligent automation plans"""

    def __init__(self):
        self.plans_generated = 0
        self._setup_gemini()

    def _setup_gemini(self):
        """Setup Gemini API"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("⚠️  GEMINI_API_KEY not found in environment variables")
                return False

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
            print("✅ Gemini 2.5 Flash-Lite configured successfully")
            return True
        except Exception as e:
            print(f"❌ Error setting up Gemini: {e}")
            return False

    def create_automation_plan(
        self, signals: Dict[str, Any], knowledge: Dict[str, Any], user_goal: str
    ) -> Dict[str, Any]:
        """Generate intelligent automation plan"""
        print("🤖 Generating automation plan...")

        prompt = self._build_decision_prompt(signals, knowledge, user_goal)

        # Use Gemini for plan generation
        if hasattr(self, "model") and self.model:
            try:
                response = self.model.generate_content(prompt)
                plan = self._parse_gemini_response(response.text, signals)
            except Exception as e:
                print(f"⚠️  Gemini error: {e}, falling back to mock planning")
                plan = self._mock_llm_planning(signals, knowledge, user_goal)
        else:
            print("⚠️  Using mock planning (Gemini not available)")
            plan = self._mock_llm_planning(signals, knowledge, user_goal)

        self.plans_generated += 1
        return plan

    def _build_decision_prompt(
        self, signals: Dict[str, Any], knowledge: Dict[str, Any], goal: str
    ) -> str:
        """Build comprehensive prompt for LLM decision making"""
        return f"""
        GOAL: {goal}
        
        AVAILABLE UI ELEMENTS:
        {self._format_ui_elements(signals['interactive_elements'])}
        
        SYSTEM STATE:
        {self._format_system_state(signals['system_state'])}
        
        EXTERNAL KNOWLEDGE:
        {self._format_knowledge(knowledge)}
        
        TASK: Create an optimal automation plan that achieves the goal using available elements.
        Consider system state, best practices, and potential risks.
        
        Please respond with a JSON structure containing:
        - "plan": List of automation steps with action, target, and reason
        - "reasoning": Explanation of the plan
        - "alternatives": Alternative approaches
        - "risks": Potential issues and mitigations
        - "confidence": Confidence level (0.0-1.0)
        """

    def _format_ui_elements(self, elements: List[UISignal]) -> str:
        """Format UI elements for LLM prompt"""
        formatted = []
        for element in elements:
            formatted.append(
                f"""
            - ID: {element.id}
              Type: {element.type}
              Position: {element.position}
              Current Value: {element.current_value}
              Available Options: {element.available_options}
              Actions: {element.actions}
              Title: {element.title}
            """
            )
        return "\n".join(formatted)

    def _format_system_state(self, state: SystemState) -> str:
        """Format system state for LLM prompt"""
        return f"""
        Battery Level: {state.battery_level}%
        Power Source: {state.power_source}
        Network: {state.network_status}
        Time: {state.time}
        Memory Usage: {state.memory_usage}%
        CPU Usage: {state.cpu_usage}%
        """

    def _format_knowledge(self, knowledge: Dict[str, Any]) -> str:
        """Format knowledge for LLM prompt"""
        formatted = []
        for key, value in knowledge.items():
            formatted.append(f"{key}: {value}")
        return "\n".join(formatted)

    def _parse_gemini_response(
        self, response_text: str, signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse Gemini response into structured plan"""
        try:
            # Try to extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                plan_data = json.loads(json_str)
                return plan_data
            else:
                # Fallback: parse text response
                return self._parse_text_response(response_text, signals)
        except Exception as e:
            print(f"⚠️  Error parsing Gemini response: {e}")
            return self._parse_text_response(response_text, signals)

    def _parse_text_response(
        self, response_text: str, signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        # Simple text parsing as fallback
        return {
            "plan": [
                {
                    "action": "analyze",
                    "target": "system",
                    "reason": "Gemini provided text response",
                }
            ],
            "reasoning": (
                response_text[:200] + "..."
                if len(response_text) > 200
                else response_text
            ),
            "alternatives": ["Manual configuration"],
            "risks": ["Requires human verification"],
            "confidence": 0.7,
        }

    def _mock_llm_planning(
        self, signals: Dict[str, Any], knowledge: Dict[str, Any], goal: str
    ) -> Dict[str, Any]:
        """Mock LLM planning (replace with actual LLM in production)"""
        elements = signals.get("interactive_elements", [])
        system_state = signals.get("system_state", {})

        # Simple rule-based planning for demonstration
        plan_steps = []

        if "battery" in goal.lower() or "power" in goal.lower():
            # Look for Low Power Mode toggle
            for element in elements:
                if "low_power" in element.id.lower():
                    if system_state.battery_level < 50:
                        plan_steps.append(
                            {
                                "action": "click",
                                "target": element.id,
                                "reason": "Enable Low Power Mode for battery optimization",
                            }
                        )
                    break

        if "security" in goal.lower():
            # Look for security-related elements
            for element in elements:
                if any(
                    security_term in element.id.lower()
                    for security_term in ["filevault", "firewall", "touch"]
                ):
                    plan_steps.append(
                        {
                            "action": "click",
                            "target": element.id,
                            "reason": f"Configure {element.id} for security",
                        }
                    )

        return {
            "plan": plan_steps,
            "reasoning": f"Generated plan based on {len(elements)} available elements",
            "alternatives": ["Manual configuration", "Gradual implementation"],
            "risks": [
                "May require user confirmation",
                "Could affect system performance",
            ],
            "confidence": 0.8,
        }


class IntelligentAutomationSystem:
    """Main system that orchestrates all components"""

    def __init__(self):
        self.signal_collector = SignalCollector()
        self.knowledge_integrator = KnowledgeIntegrator()
        self.llm_planner = LLMPlanner()

    def automate(self, user_goal: str, target_app: str = None) -> Dict[str, Any]:
        """Main automation method"""
        print(f"🎯 Intelligent Automation System")
        print(f"Goal: {user_goal}")
        print(f"Target App: {target_app or 'All Apps'}")
        print("=" * 60)

        # Step 1: Discover signals
        signals = self.signal_collector.discover_ui_signals(target_app)

        # Step 2: Gather knowledge
        knowledge = self.knowledge_integrator.gather_context(user_goal, signals)

        # Step 3: Generate plan
        plan = self.llm_planner.create_automation_plan(signals, knowledge, user_goal)

        # Step 4: Present results
        self._present_results(signals, knowledge, plan)

        return {"signals": signals, "knowledge": knowledge, "plan": plan}

    def _present_results(
        self, signals: Dict[str, Any], knowledge: Dict[str, Any], plan: Dict[str, Any]
    ):
        """Present the results to the user"""
        print(f"\n📊 DISCOVERED SIGNALS:")
        print(f"   Interactive Elements: {len(signals['interactive_elements'])}")
        print(f"   System State: {signals['system_state']}")
        print(f"   Constraints: {signals['constraints']}")

        print(f"\n🧠 KNOWLEDGE INTEGRATION:")
        print(f"   Web Search Results: {len(knowledge['web_search_results'])}")
        print(f"   Domain Knowledge: {len(knowledge['domain_knowledge'])}")
        print(f"   Best Practices: {len(knowledge['best_practices'])}")
        print(f"   Recommendations: {len(knowledge['system_recommendations'])}")

        print(f"\n🤖 LLM GENERATED PLAN:")
        print(f"   Steps: {len(plan['plan'])}")
        print(f"   Confidence: {plan['confidence']}")
        print(f"   Reasoning: {plan['reasoning']}")

        print(f"\n📋 AUTOMATION STEPS:")
        for i, step in enumerate(plan["plan"], 1):
            print(f"   {i}. {step['action']} on {step['target']}")
            print(f"      Reason: {step['reason']}")


def main():
    """Main function for testing the system"""
    system = IntelligentAutomationSystem()

    if len(sys.argv) > 1:
        goal = sys.argv[1]
        target_app = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        goal = "optimize battery life"
        target_app = "System Settings"

    result = system.automate(goal, target_app)

    # Save results to file
    with open("automation_result.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n💾 Results saved to automation_result.json")


if __name__ == "__main__":
    main()
