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
        self.long_range_plan = None
        self.plan_created = False

    def _setup_gemini(self):
        """Setup Gemini API for reasoning"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key or api_key == "your_api_key_here":
                print("   ⚠️  GEMINI_API_KEY not found or invalid")
                return False

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash-lite")
            print("   ✅ Gemini 2.5 Flash-Lite configured for intelligent reasoning")
            return True
        except Exception as e:
            print(f"   ❌ Error setting up Gemini: {e}")
            return False

    def create_long_range_plan(
        self,
        goal: str,
        target_app: str,
        ui_signals: List[Dict[str, Any]],
        system_state: Any,
    ) -> Dict[str, Any]:
        """Create a comprehensive long-range plan for achieving the goal"""
        if not self.model:
            return {"error": "Gemini not configured"}

        try:
            print("   🎯 Creating long-range plan...")

            # Build the planning prompt
            planning_prompt = f"""
            You are an AI planning expert. Create a comprehensive, step-by-step plan to achieve the user's goal.
            
            GOAL: {goal}
            TARGET APP: {target_app}
            
            CURRENT ENVIRONMENT:
            - Available UI Elements: {len(ui_signals)}
            - System State: {system_state}
            
            AVAILABLE UI ELEMENTS:
            {self._format_ui_elements(ui_signals)}
            
            SYSTEM STATE:
            {self._format_system_state(system_state)}
            
            Create a detailed plan that:
            1. Breaks down the goal into clear, actionable steps
            2. Identifies the end state/success criteria
            3. Considers potential obstacles and alternatives
            4. Provides a clear sequence of actions
            5. Defines what "success" looks like
            
            Respond with JSON:
            {{
                "goal": "The original user goal",
                "end_state": "Clear description of what success looks like",
                "success_criteria": ["Specific criteria that indicate goal achievement"],
                "steps": [
                    {{"step": 1, "action": "action_type", "description": "what to do", "expected_outcome": "what should happen"}},
                    {{"step": 2, "action": "action_type", "description": "what to do", "expected_outcome": "what should happen"}},
                    ...
                ],
                "obstacles": ["Potential issues that might arise"],
                "alternatives": ["Alternative approaches if main plan fails"],
                "completion_indicators": ["Signs that the goal has been achieved"]
            }}
            """

            response = self.model.generate_content(planning_prompt)
            plan_text = response.text.strip()

            # Parse the JSON response
            try:
                import re

                json_match = re.search(r"\{.*\}", plan_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    plan = json.loads(json_str)
                    self.long_range_plan = plan
                    self.plan_created = True
                    print(
                        f"   ✅ Long-range plan created with {len(plan.get('steps', []))} steps"
                    )
                    return plan
                else:
                    return {"error": "Could not parse plan JSON"}
            except Exception as e:
                return {"error": f"Plan parsing failed: {e}"}

        except Exception as e:
            return {"error": f"Plan creation failed: {e}"}

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

        # VERBOSE: Print the full prompt
        print("\n" + "=" * 80)
        print("📝 FULL PROMPT SENT TO GEMINI:")
        print("=" * 80)
        print(prompt)
        print("=" * 80)

        # Use Gemini for reasoning
        if self.model:
            try:
                response = self.model.generate_content(prompt)

                # VERBOSE: Print the full response
                print("\n" + "=" * 80)
                print("🤖 FULL GEMINI RESPONSE:")
                print("=" * 80)
                print(response.text)
                print("=" * 80)

                reasoning_result = self._parse_gemini_response(response.text)

                # VERBOSE: Print parsed result
                print("\n" + "=" * 80)
                print("📊 PARSED REASONING RESULT:")
                print("=" * 80)
                print(f"Plan: {reasoning_result.get('plan', [])}")
                print(f"Confidence: {reasoning_result.get('confidence', 0)}")
                print(f"Reasoning: {reasoning_result.get('reasoning', '')}")
                print(f"Alternatives: {reasoning_result.get('alternatives', [])}")
                print(f"Risks: {reasoning_result.get('risks', [])}")
                print("=" * 80)

                print(
                    f"   ✅ Gemini reasoning complete: {reasoning_result['confidence']:.2f} confidence"
                )
            except Exception as e:
                print(f"   ❌ Gemini error: {e}")
                import traceback

                traceback.print_exc()
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
        """
        Build comprehensive reasoning prompt with hybrid accessibility + visual data.

        This method creates a detailed prompt that includes both traditional accessibility
        API data and visual language model analysis for enhanced decision-making.

        Args:
            goal: User's goal to achieve
            perception: Hybrid perception data including accessibility and visual elements
            knowledge: Domain knowledge and best practices
            agent_state: Current agent state information

        Returns:
            Formatted prompt string for Gemini reasoning
        """

        ui_signals = perception.get("ui_signals", [])
        system_state = perception.get("system_state", {})
        visual_analysis = perception.get("visual_analysis")
        correlations = perception.get("correlations")

        return f"""
        You are an autonomous AI agent with hybrid perception capabilities that can interact 
        with any application or system to achieve goals using both accessibility APIs and 
        visual analysis.
        
        GOAL: {goal}
        
        CURRENT ENVIRONMENT:
        - Accessibility UI Elements: {len(ui_signals)}
        - Visual Elements: {len(visual_analysis.interactive_elements) if visual_analysis else 0}
        - Correlated Elements: {correlations.get('matched_elements', 0) if correlations else 0}
        - System State: {system_state}
        - Progress: {agent_state.progress:.2f}
        - Errors: {agent_state.error_count}
        
        ACCESSIBILITY UI ELEMENTS (Use these exact IDs):
        {self._format_ui_elements(ui_signals)}
        
        VISUAL ANALYSIS:
        {self._format_visual_analysis(visual_analysis)}
        
        ELEMENT CORRELATIONS:
        {self._format_correlations(correlations)}
        
        SYSTEM STATE:
        {self._format_system_state(system_state)}
        
        CONTEXT:
        {self._format_knowledge(knowledge)}
        
        LONG-RANGE PLAN:
        {self._format_long_range_plan()}
        
        Analyze the situation and create a plan to achieve the goal. Use the exact element IDs provided.
        Consider what actions are needed, which elements to use, potential risks, and alternatives.
        
        CRITICAL: You MUST use ONLY the element IDs provided in the "AVAILABLE UI ELEMENTS" section above.
        Do NOT create or invent your own element IDs like "WEB_BROWSER_ADDRESS_AND_SEARCH_FIELD".
        Look for elements with IDs like "AXTextField_802.5_43.0" or "AXButton_123.0_456.0".
        
        WHEN NO UI ELEMENTS ARE AVAILABLE:
        - Use "keystroke" action with target "all" for system-wide commands
        - Do NOT use "click" action with target "all" (this will fail)
        - For browser tasks: use "keystroke" with target "all" and text like "open safari" or search queries
        - For terminal tasks: use "keystroke" with target "all" and terminal commands
        
        WHEN UI ELEMENTS ARE AVAILABLE:
        - ALWAYS prefer clicking on existing UI elements over system commands
        - If search results are visible, click on the most relevant result
        - For video requests: click on YouTube video links to navigate to the actual video page
        - Only use system commands when no relevant UI elements are available
        
        IMPORTANT: Plan only ONE action at a time. The agent will observe the results and plan the next action.
        Focus on the most immediate next step to make progress toward the goal.
        
        NAVIGATION PREFERENCES:
        - Prefer "keystroke" action for search fields and text inputs (automatically presses Enter)
        - Use "type" action for general text input that doesn't need Enter
        - Use "click" action for buttons, links, and interactive elements
        - Keystroke navigation is often more reliable than clicking search buttons
        
        TERMINAL APPLICATIONS (iTerm2, Terminal):
        - Use "keystroke" action with target "all" for terminal commands
        - Do NOT try to find specific UI elements in terminals
        - Terminal commands should be sent as system-wide keystrokes
        - Examples: "echo hello world", "ls", "cd /path", etc.
        
        SYSTEM SETTINGS SEARCH:
        - Use "keystroke" action with target "all" for search queries
        - Do NOT try to click individual settings buttons
        - Let System Settings handle the search results automatically
        - Examples: "battery saver", "low power mode", "display settings", etc.
        
        BROWSER TASKS (Safari, Chrome, Firefox):
        - Use "keystroke" action with target "all" for search queries
        - Do NOT try to click individual browser buttons when no elements are available
        - Let the browser handle the search results automatically
        - Examples: "ishowspeed", "youtube ishowspeed", "search for ishowspeed", etc.
        
        VIDEO GOALS (showing videos, watching videos):
        - If YouTube video links are visible in search results, click on them to navigate to the actual video page
        - Look for elements with titles containing "YouTube", "Play on Google", or video duration
        - Prioritize clicking on the most relevant video result rather than searching again
        - Only search again if no video results are visible
        
        AVAILABLE ACTIONS:
        - "click": Click on a UI element (button, link, etc.)
        - "type": Type text into a text field (auto-presses Enter for search completion)
        - "keystroke": Type text and automatically press Enter (preferred for search fields)
        - "key": Press a keyboard key (enter, space, tab, etc.)
        - "select": Select an option from a dropdown
        - "scroll": Scroll in a direction (up, down, left, right)
        - "wait": Wait for a specified duration
        
        Respond with JSON:
        {{
            "plan": [
                {{"action": "action_type", "target": "element_id", "text": "text_to_type", "key": "key_name", "reason": "why this action"}}
            ],
            "confidence": 0.0-1.0,
            "reasoning": "explanation of your approach",
            "alternatives": ["other approaches if needed"],
            "risks": ["potential issues and mitigations"],
            "next_step": "what to do after this action completes"
        }}
        """

    def _format_ui_elements(self, elements: List[Dict[str, Any]]) -> str:
        """Format UI elements for reasoning prompt"""
        if not elements:
            return "No UI elements available"

        # Prioritize important elements (text fields, search elements, buttons with meaningful titles)
        important_elements = []
        other_elements = []

        for element in elements:
            element_type = element.get("type", "")
            title = element.get("title", "").lower()
            description = element.get("description", "").lower()

            # Prioritize text fields, search elements, and meaningful buttons
            if (
                element_type == "AXTextField"
                or "search" in title
                or "search" in description
                or "input" in title
                or "input" in description
                or (element_type == "AXButton" and title and title != "button")
            ):
                important_elements.append(element)
            else:
                other_elements.append(element)

        # Combine important elements first, then others - NO LIMIT!
        prioritized_elements = important_elements + other_elements
        elements_to_show = prioritized_elements  # Show ALL elements

        formatted = []
        for element in elements_to_show:
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

    def _format_long_range_plan(self) -> str:
        """Format the long-range plan for the prompt"""
        if not self.long_range_plan:
            return "No long-range plan available yet."

        plan = self.long_range_plan
        formatted = []

        formatted.append(f"ORIGINAL GOAL: {plan.get('goal', 'Unknown')}")
        formatted.append(f"END STATE: {plan.get('end_state', 'Not defined')}")
        formatted.append("")

        # Success criteria
        criteria = plan.get("success_criteria", [])
        if criteria:
            formatted.append("SUCCESS CRITERIA:")
            for criterion in criteria:
                formatted.append(f"- {criterion}")
            formatted.append("")

        # Steps
        steps = plan.get("steps", [])
        if steps:
            formatted.append("PLANNED STEPS:")
            for step in steps:
                step_num = step.get("step", "?")
                action = step.get("action", "unknown")
                description = step.get("description", "No description")
                expected = step.get("expected_outcome", "No expected outcome")
                formatted.append(f"{step_num}. {action.upper()}: {description}")
                formatted.append(f"   Expected: {expected}")
            formatted.append("")

        # Obstacles
        obstacles = plan.get("obstacles", [])
        if obstacles:
            formatted.append("POTENTIAL OBSTACLES:")
            for obstacle in obstacles:
                formatted.append(f"- {obstacle}")
            formatted.append("")

        # Completion indicators
        indicators = plan.get("completion_indicators", [])
        if indicators:
            formatted.append("COMPLETION INDICATORS:")
            for indicator in indicators:
                formatted.append(f"- {indicator}")

        return "\n".join(formatted)

    def _format_visual_analysis(self, visual_analysis) -> str:
        """
        Format visual analysis data for the reasoning prompt.

        Args:
            visual_analysis: VisualAnalysis object or None

        Returns:
            Formatted string describing visual elements and analysis
        """
        if not visual_analysis:
            return "No visual analysis available"

        formatted = []
        formatted.append(f"Screen Description: {visual_analysis.screen_description}")
        formatted.append("")

        if visual_analysis.interactive_elements:
            formatted.append(
                f"Visual Interactive Elements ({len(visual_analysis.interactive_elements)}):"
            )
            for i, element in enumerate(visual_analysis.interactive_elements, 1):
                formatted.append(f"  {i}. {element.type.upper()}")
                formatted.append(f"     Position: {element.position}")
                formatted.append(f"     Text: {element.text}")
                formatted.append(f"     Purpose: {element.purpose}")
                formatted.append(f"     Characteristics: {element.characteristics}")
                if element.task_relevant:
                    formatted.append(f"     🎯 TASK-RELEVANT")
                if element.coordinates:
                    formatted.append(f"     Coordinates: {element.coordinates}")
                formatted.append("")
        else:
            formatted.append("No visual interactive elements identified")

        if visual_analysis.safety_warnings:
            formatted.append("Visual Safety Warnings:")
            for warning in visual_analysis.safety_warnings:
                formatted.append(f"  ⚠️  {warning}")
            formatted.append("")

        if visual_analysis.alternative_methods:
            formatted.append("Alternative Methods:")
            for method in visual_analysis.alternative_methods:
                formatted.append(f"  💡 {method}")

        return "\n".join(formatted)

    def _format_correlations(self, correlations) -> str:
        """
        Format element correlations between accessibility and visual data.

        Args:
            correlations: Correlation data or None

        Returns:
            Formatted string describing element correlations
        """
        if not correlations:
            return "No element correlations available"

        formatted = []
        formatted.append(
            f"Total Accessibility Elements: {correlations.get('total_ui_signals', 0)}"
        )
        formatted.append(
            f"Total Visual Elements: {correlations.get('total_visual_elements', 0)}"
        )
        formatted.append(f"Matched Elements: {correlations.get('matched_elements', 0)}")
        formatted.append("")

        correlation_list = correlations.get("correlations", [])
        if correlation_list:
            formatted.append("Element Correlations:")
            for i, correlation in enumerate(
                correlation_list[:10], 1
            ):  # Limit to 10 for readability
                ui_signal = correlation.get("ui_signal", {})
                visual_element = correlation.get("visual_element")
                score = correlation.get("correlation_score", 0)

                formatted.append(
                    f"  {i}. Accessibility ID: {correlation.get('accessibility_id', 'Unknown')}"
                )
                formatted.append(
                    f"     Visual Element: {visual_element.type if visual_element else 'Unknown'}"
                )
                formatted.append(f"     Correlation Score: {score}")
                formatted.append(f"     UI Title: {ui_signal.get('title', 'No title')}")
                formatted.append(
                    f"     Visual Text: {visual_element.text if visual_element else 'No text'}"
                )
                formatted.append("")
        else:
            formatted.append("No element correlations found")

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
