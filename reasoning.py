#!/usr/bin/env python3
"""
Reasoning Engine - Handles all reasoning, planning, and decision-making
"""

import json
import os
import google.generativeai as genai
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class ReasoningResult:
    """Result of reasoning process"""

    plan: List[Dict[str, Any]]
    confidence: float
    reasoning: str
    alternatives: List[str]
    risks: List[str]
    next_steps: List[str]


class ReasoningEngine:
    """
    Handles all reasoning tasks:
    - Goal analysis
    - Plan generation
    - Decision making
    - Risk assessment
    - Alternative generation
    """

    def __init__(self):
        self.model = None
        self._setup_gemini()
        self.reasoning_history = []

    def _setup_gemini(self):
        """Setup Gemini API for reasoning"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key or api_key == "your_api_key_here":
                print("   ⚠️  GEMINI_API_KEY not found or invalid")
                return False

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
            print("   ✅ Gemini 2.0 Flash configured for intelligent reasoning")
            return True
        except Exception as e:
            print(f"   ❌ Error setting up Gemini: {e}")
            return False

    def gather_knowledge(self, goal: str, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Gather relevant knowledge for the goal"""
        print("   🧠 Gathering knowledge...")

        return {
            "domain_knowledge": self._get_domain_knowledge(goal),
            "best_practices": self._get_best_practices(goal),
            "system_recommendations": self._get_system_recommendations(perception),
            "historical_context": self._get_historical_context(goal),
        }

    def analyze_situation(
        self,
        goal: str,
        perception: Dict[str, Any],
        knowledge: Dict[str, Any],
        agent_state: Any,
    ) -> Dict[str, Any]:
        """Analyze the current situation and generate a plan"""
        print("   🎯 Analyzing situation...")

        # Build comprehensive prompt
        prompt = self._build_reasoning_prompt(goal, perception, knowledge, agent_state)

        # Use Gemini for reasoning
        if self.model:
            try:
                response = self.model.generate_content(prompt)
                reasoning_result = self._parse_gemini_response(response.text)
                print(
                    f"   ✅ Gemini reasoning complete: {reasoning_result['confidence']:.2f} confidence"
                )
            except Exception as e:
                print(f"   ❌ Gemini error: {e}")
                return {"error": str(e), "plan": [], "confidence": 0.0}
        else:
            print("   ❌ Gemini not available - API key required")
            return {"error": "Gemini API key required", "plan": [], "confidence": 0.0}

        # Store reasoning in history
        self.reasoning_history.append(reasoning_result)

        return reasoning_result

    def _build_reasoning_prompt(
        self,
        goal: str,
        perception: Dict[str, Any],
        knowledge: Dict[str, Any],
        agent_state: Any,
    ) -> str:
        """Build comprehensive prompt for reasoning"""

        ui_signals = perception.get("ui_signals", [])
        system_state = perception.get("system_state", {})

        return f"""
        AUTONOMOUS AGENT REASONING TASK
        
        GOAL: {goal}
        
        CURRENT SITUATION:
        - UI Elements Available: {len(ui_signals)}
        - System State: {system_state}
        - Agent Progress: {agent_state.progress:.2f}
        - Error Count: {agent_state.error_count}
        
        AVAILABLE UI ELEMENTS (USE THESE EXACT IDs):
        {self._format_ui_elements(ui_signals)}
        
        SYSTEM STATE:
        {self._format_system_state(system_state)}
        
        KNOWLEDGE BASE:
        {self._format_knowledge(knowledge)}
        
        TASK: As an autonomous agent, analyze this situation and create an optimal action plan.
        
        IMPORTANT: You MUST use the exact element IDs provided above. Do not create new IDs.
        
        Consider:
        1. What actions are needed to achieve the goal?
        2. Which of the available UI elements can be used?
        3. What are the risks and how to mitigate them?
        4. What alternatives exist if the primary plan fails?
        5. How confident are you in this plan?
        
        Respond with a JSON structure:
        {{
            "plan": [
                {{"action": "click", "target": "EXACT_ELEMENT_ID_FROM_ABOVE", "reason": "explanation"}},
                {{"action": "select", "target": "EXACT_ELEMENT_ID_FROM_ABOVE", "reason": "explanation"}}
            ],
            "confidence": 0.85,
            "reasoning": "Detailed explanation of the plan",
            "alternatives": ["Alternative approach 1", "Alternative approach 2"],
            "risks": ["Risk 1: mitigation", "Risk 2: mitigation"],
            "next_steps": ["Step 1", "Step 2"]
        }}
        """

    def _format_ui_elements(self, elements: List[Dict[str, Any]]) -> str:
        """Format UI elements for reasoning prompt"""
        if not elements:
            return "No UI elements available"

        formatted = []
        for element in elements[:10]:  # Limit to first 10 elements
            formatted.append(
                f"""
            - ID: {element.get('id', 'Unknown')}
              Type: {element.get('type', 'Unknown')}
              Position: {element.get('position', (0, 0))}
              Current Value: {element.get('current_value', '')}
              Available Options: {element.get('available_options', [])}
              Actions: {element.get('actions', [])}
              Title: {element.get('title', '')}
            """
            )
        return "\n".join(formatted)

    def _format_system_state(self, state: Any) -> str:
        """Format system state for reasoning prompt"""
        if not state:
            return "System state unknown"

        # Handle both dict and SystemState object
        if hasattr(state, "battery_level"):
            return f"""
        Battery Level: {state.battery_level}%
        Power Source: {state.power_source}
        Network: {state.network_status}
        Memory Usage: {state.memory_usage}%
        CPU Usage: {state.cpu_usage}%
        """
        else:
            return f"""
        Battery Level: {state.get('battery_level', 0)}%
        Power Source: {state.get('power_source', 'unknown')}
        Network: {state.get('network_status', 'unknown')}
        Memory Usage: {state.get('memory_usage', 0)}%
        CPU Usage: {state.get('cpu_usage', 0)}%
        """

    def _format_knowledge(self, knowledge: Dict[str, Any]) -> str:
        """Format knowledge for reasoning prompt"""
        formatted = []
        for key, value in knowledge.items():
            if isinstance(value, list):
                formatted.append(f"{key}: {', '.join(value)}")
            else:
                formatted.append(f"{key}: {value}")
        return "\n".join(formatted)

    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response into structured reasoning result"""
        try:
            # Try to extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                return self._parse_text_response(response_text)
        except Exception as e:
            print(f"   ⚠️  Error parsing Gemini response: {e}")
            return self._parse_text_response(response_text)

    def _parse_text_response(self, response_text: str) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        return {
            "plan": [
                {
                    "action": "analyze",
                    "target": "system",
                    "reason": "Gemini provided text response",
                }
            ],
            "confidence": 0.7,
            "reasoning": (
                response_text[:200] + "..."
                if len(response_text) > 200
                else response_text
            ),
            "alternatives": ["Manual configuration"],
            "risks": ["Requires human verification"],
            "next_steps": ["Verify current state", "Plan next actions"],
        }

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

    def _get_system_recommendations(self, perception: Dict[str, Any]) -> List[str]:
        """Get system-specific recommendations"""
        recommendations = []

        system_state = perception.get("system_state")
        constraints = perception.get("constraints", [])

        if "low_battery" in constraints:
            recommendations.append("Consider enabling Low Power Mode")

        if (
            system_state
            and hasattr(system_state, "battery_level")
            and system_state.battery_level < 30
        ):
            recommendations.append("Battery is low - optimize power settings")

        if "high_memory_usage" in constraints:
            recommendations.append("Close unnecessary applications")

        return recommendations

    def _get_historical_context(self, goal: str) -> List[str]:
        """Get historical context from previous reasoning"""
        # Simple implementation - in a real system this would be more sophisticated
        return [f"Previous reasoning for {goal}"]

    def get_reasoning_summary(self) -> Dict[str, Any]:
        """Get a summary of reasoning capabilities"""
        return {
            "reasoning_history_size": len(self.reasoning_history),
            "gemini_available": self.model is not None,
            "fallback_mode": self.model is None,
        }
