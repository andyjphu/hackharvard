#!/usr/bin/env python3
"""
Reasoning Engine - Handles all reasoning, planning, and decision-making
"""

import json
import os
import re
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

import google.generativeai as genai
from dotenv import load_dotenv

# Optional macOS settings hints
try:
    from macos_settings_map import find_settings_panel, get_panel_elements, MACOS_SETTINGS_MAP
except Exception:
    MACOS_SETTINGS_MAP = {}
    def find_settings_panel(goal: str): return {"panel": None, "confidence": 0.0}
    def get_panel_elements(panel: str): return {"elements": {}}

load_dotenv()

GEMINI_REASONING_MODEL = os.getenv("GEMINI_REASONING_MODEL", "gemini-2.5-pro")


@dataclass
class ReasoningResult:
    """Result of reasoning process"""
    plan: List[Dict[str, Any]]
    confidence: float
    reasoning: str
    alternatives: List[str]
    risks: List[str]
    next_step: str


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
        self.reasoning_history: List[Dict[str, Any]] = []
        self.long_range_plan: Optional[Dict[str, Any]] = None
        self._last_gemini_request_time: float = 0.0  # Throttling
        self.settings_map = MACOS_SETTINGS_MAP

    # -------- Gemini setup/throttle --------

    def _setup_gemini(self) -> bool:
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("   ⚠️  GEMINI_API_KEY not found")
                return False
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(GEMINI_REASONING_MODEL)
            print(f"   ✅ Gemini configured ({GEMINI_REASONING_MODEL}) for reasoning")
            return True
        except Exception as e:
            print(f"   ❌ Error setting up Gemini: {e}")
            return False

    def _throttle(self, min_seconds: float = 5.0):
        now = time.time()
        delta = now - self._last_gemini_request_time
        if delta < min_seconds:
            time.sleep(min_seconds - delta)
        self._last_gemini_request_time = time.time()

    # -------- Planning --------

    def create_long_range_plan(self, goal: str, target_app: Optional[str], ui_signals: List[Dict[str, Any]], system_state: Any) -> Dict[str, Any]:
        if not self.model:
            return {"error": "Gemini not configured"}

        print("   🎯 Creating long-range plan...")

        settings_info = find_settings_panel(goal)
        panel_context = ""
        if settings_info.get("panel"):
            panel_data = get_panel_elements(settings_info["panel"])
            panel_context = (
                f"MACOS SETTINGS CONTEXT:\n"
                f"- Target Panel: {settings_info['panel']}\n"
                f"- Confidence: {settings_info.get('confidence', 0.0)}\n"
                f"- Available Elements: {list(panel_data.get('elements', {}).keys())}\n"
            )

        prompt = f"""
You are an AI planning expert. Create a comprehensive, step-by-step plan to achieve the user's goal.

GOAL: {goal}
TARGET APP: {target_app}

{panel_context}

ENVIRONMENT SNAPSHOT:
- Available UI Elements: {len(ui_signals)}
- System State: {self._format_system_state(system_state)}

UI ELEMENTS (IDs are authoritative; do not invent):
{self._format_ui_elements(ui_signals)}

Respond ONLY with JSON:
{{
  "goal": "...",
  "end_state": "...",
  "success_criteria": ["..."],
  "steps": [
    {{"step": 1, "action": "action_type", "target": "element_id_or_all", "description": "what to do", "expected_outcome": "..."}}
  ],
  "obstacles": ["..."],
  "alternatives": ["..."],
  "completion_indicators": ["..."]
}}
"""

        try:
            self._throttle()
            resp = self.model.generate_content(prompt)
            txt = (resp.text or "").strip()
            m = re.search(r"\{.*\}", txt, flags=re.DOTALL)
            if not m:
                return {"error": "Could not parse plan JSON"}
            plan = json.loads(m.group(0))
            self.long_range_plan = plan
            return plan
        except Exception as e:
            return {"error": f"Plan creation failed: {e}"}

    # -------- Knowledge --------

    def gather_knowledge(self, goal: str, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Gather relevant knowledge for the goal (lightweight heuristics)."""
        print("   🧠 Gathering knowledge...")
        return {
            "domain_knowledge": self._get_domain_knowledge(goal),
            "best_practices": self._get_best_practices(goal),
            "system_recommendations": self._get_system_recommendations(perception),
            "historical_context": self._get_historical_context(goal),
        }

    @staticmethod
    def _get_domain_knowledge(goal: str) -> List[str]:
        gl = goal.lower()
        items = []
        if "battery" in gl:
            items += ["Prefer low-power mode", "Dim display", "Disable radios not in use"]
        if "privacy" in gl or "secure" in gl:
            items += ["Prefer system settings over third-party tools", "Review permissions/toggles"]
        if "search" in gl:
            items += ["Use address or search bar", "Submit via Enter"]
        if "calculator" in gl or "math" in gl:
            items += ["Use on-screen buttons if available", "Fallback to typing numbers"]
        return items or ["Use accessible UI controls where possible"]

    @staticmethod
    def _get_best_practices(goal: str) -> List[str]:
        return [
            "Use exact accessibility element IDs; do not invent IDs",
            "Prefer visible, labeled buttons/switches",
            "If no UI is found, use 'keystroke' with target 'all'",
            "Pause briefly after actions to allow UI updates",
        ]

    @staticmethod
    def _get_system_recommendations(perception: Dict[str, Any]) -> List[str]:
        recs = []
        st = perception.get("system_state")
        if st and getattr(st, "battery_level", 100) < 20:
            recs.append("Battery low: consider low power mode")
        return recs

    @staticmethod
    def _get_historical_context(goal: str) -> List[str]:
        return []

    # -------- Reasoning --------

    def analyze_situation(self, goal: str, perception: Dict[str, Any], knowledge: Dict[str, Any], agent_state: Any) -> Dict[str, Any]:
        """Analyze the current situation and generate a plan"""
        print("   🎯 Analyzing situation...")

        prompt = self._build_reasoning_prompt(goal, perception, knowledge, agent_state)

        print("\n" + "=" * 80)
        print("📝 FULL PROMPT SENT TO GEMINI:")
        print("=" * 80)
        print(prompt)
        print("=" * 80)

        if not self.model:
            print("   ❌ Gemini not available - API key required")
            return {"error": "Gemini API key required", "plan": [], "confidence": 0.0}

        try:
            self._throttle()
            resp = self.model.generate_content(prompt)

            print("\n" + "=" * 80)
            print("🤖 FULL GEMINI RESPONSE:")
            print("=" * 80)
            print(resp.text or "")
            print("=" * 80)

            parsed = self._parse_gemini_response(resp.text or "")

            print("\n" + "=" * 80)
            print("📊 PARSED REASONING RESULT:")
            print("=" * 80)
            print(f"Plan: {parsed.get('plan', [])}")
            print(f"Confidence: {parsed.get('confidence', 0)}")
            print(f"Reasoning: {parsed.get('reasoning', '')}")
            print(f"Alternatives: {parsed.get('alternatives', [])}")
            print(f"Risks: {parsed.get('risks', [])}")
            print("=" * 80)

            self.reasoning_history.append(parsed)
            return parsed

        except Exception as e:
            return {"error": str(e), "plan": [], "confidence": 0.0}

    def analyze_with_visual(self, goal: str, perception: Dict[str, Any], screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """Combined visual analysis and reasoning in a single API call."""
        print("   🎯 Analyzing with visual context...")

        if not self.model:
            return {"error": "Gemini API key required", "plan": [], "confidence": 0.0}

        prompt = self._build_visual_reasoning_prompt(goal, perception, screenshot_path)

        print("\n" + "=" * 80)
        print("📝 FULL VISUAL REASONING PROMPT SENT TO GEMINI:")
        print("=" * 80)
        print(prompt)
        print("=" * 80)

        try:
            self._throttle()
            if screenshot_path:
                with open(screenshot_path, "rb") as f:
                    image_data = {"mime_type": "image/png", "data": f.read()}
                resp = self.model.generate_content([prompt, image_data])
            else:
                resp = self.model.generate_content(prompt)

            print("\n" + "=" * 80)
            print("🤖 FULL GEMINI VISUAL REASONING RESPONSE:")
            print("=" * 80)
            print(resp.text or "")
            print("=" * 80)

            parsed = self._parse_gemini_response(resp.text or "")
            self.reasoning_history.append(parsed)
            return parsed

        except Exception as e:
            return {"error": str(e), "plan": [], "confidence": 0.0}

    # -------- Prompt builders / formatters --------

    def _build_visual_reasoning_prompt(self, goal: str, perception: Dict[str, Any], screenshot_path: Optional[str]) -> str:
        ui = perception.get("ui_signals", [])
        system_state = perception.get("system_state")
        visual = perception.get("visual_analysis")
        correlations = perception.get("correlations")

        settings_info = find_settings_panel(goal)
        panel_context = ""
        if settings_info.get("panel"):
            panel_data = get_panel_elements(settings_info["panel"])
            panel_context = (
                f"MACOS SETTINGS CONTEXT:\n"
                f"- Target Panel: {settings_info['panel']}\n"
                f"- Confidence: {settings_info.get('confidence', 0.0)}\n"
                f"- Available Elements: {list(panel_data.get('elements', {}).keys())}\n"
            )

        return f"""
You are an autonomous AI agent with visual + accessibility perception.

GOAL: {goal}

{panel_context}

ENVIRONMENT:
- Accessibility UI Elements: {len(ui)}
- Visual Elements: {len(visual.interactive_elements) if visual else 0}
- Correlated Elements: {(correlations or {}).get('matched_elements', 0)}
- System State: {self._format_system_state(system_state)}
- Screenshot Available: {"Yes" if screenshot_path else "No"}

ACCESSIBILITY UI ELEMENTS (IDs are authoritative; DO NOT invent new IDs):
{self._format_ui_elements(ui)}

VISUAL ANALYSIS:
{self._format_visual_analysis(visual)}

ELEMENT CORRELATIONS:
{self._format_correlations(correlations)}

LONG-RANGE PLAN (if any):
{self._format_long_range_plan()}

TASK:
Create a JSON plan to achieve the goal using ONLY the given element IDs. If no UI element is suitable,
use "keystroke" with target "all". Avoid made-up IDs like "BUTTON_2" or "WEB_BROWSER_ADDRESS_AND_SEARCH_FIELD".

Respond ONLY with JSON:
{{
  "plan": [{{"action":"click|type|keystroke|key|select|scroll|wait","target":"element_id|all","text":"...","key":"...","reason":"..."}}],
  "confidence": 0.0,
  "reasoning": "...",
  "alternatives": ["..."],
  "risks": ["..."],
  "next_step": "..."
}}
"""

    def _build_reasoning_prompt(self, goal: str, perception: Dict[str, Any], knowledge: Dict[str, Any], agent_state: Any) -> str:
        ui = perception.get("ui_signals", [])
        system_state = perception.get("system_state")
        visual = perception.get("visual_analysis")
        correlations = perception.get("correlations")

        return f"""
You are an autonomous AI agent with hybrid perception (accessibility + visual).
Use ELEMENT IDs exactly as provided; do not invent new IDs.

GOAL: {goal}

STATE:
- UI Elements: {len(ui)}
- Visual Elements: {len(visual.interactive_elements) if visual else 0}
- Correlated: {(correlations or {}).get('matched_elements', 0)}
- System State: {self._format_system_state(system_state)}
- Progress: {getattr(agent_state, "progress", 0.0):.2f}
- Errors: {getattr(agent_state, "error_count", 0)}

UI ELEMENTS (IDs are authoritative):
{self._format_ui_elements(ui)}

VISUAL:
{self._format_visual_analysis(visual)}

CORRELATIONS:
{self._format_correlations(correlations)}

KNOWLEDGE:
{self._format_knowledge(knowledge)}

LONG-RANGE PLAN:
{self._format_long_range_plan()}

Respond ONLY with JSON:
{{
  "plan": [{{"action":"click|type|keystroke|key|select|scroll|wait","target":"element_id|all","text":"...","key":"...","reason":"..."}}],
  "confidence": 0.0,
  "reasoning": "...",
  "alternatives": ["..."],
  "risks": ["..."],
  "next_step": "..."
}}
"""

    # -------- Format helpers --------

    @staticmethod
    def _format_ui_elements(ui: List[Dict[str, Any]]) -> str:
        if not ui:
            return "- (none)"
        lines = []
        for e in ui[:80]:  # avoid massive dumps
            lines.append(f"- {e.get('id')} | {e.get('type')} | {e.get('title')}")
        if len(ui) > 80:
            lines.append(f"... (+{len(ui)-80} more)")
        return "\n".join(lines)

    @staticmethod
    def _format_visual_analysis(visual) -> str:
        if not visual:
            return "- (none)"
        desc = visual.screen_description or "(no description)"
        count = len(visual.interactive_elements)
        return f"- {desc}\n- Interactive elements: {count}"

    @staticmethod
    def _format_correlations(corr) -> str:
        if not corr:
            return "- (none)"
        return f"- Matched elements: {corr.get('matched_elements', 0)}"

    @staticmethod
    def _format_system_state(state) -> str:
        if not state:
            return "(unknown)"
        return f"battery={state.battery_level}%, power={state.power_source}, net={state.network_status}, mem={state.memory_usage:.1f}%, cpu={state.cpu_usage:.1f}%"

    def _format_long_range_plan(self) -> str:
        if not self.long_range_plan:
            return "- (none)"
        try:
            steps = self.long_range_plan.get("steps", [])
            return f"- Steps: {len(steps)} | End-state: {self.long_range_plan.get('end_state', '(n/a)')}"
        except Exception:
            return "- (invalid)"

    @staticmethod
    def _format_knowledge(knowledge: Dict[str, Any]) -> str:
        try:
            return json.dumps(knowledge, indent=2)[:1200]
        except Exception:
            return "(unavailable)"

    # -------- Parse --------

    @staticmethod
    def _parse_gemini_response(text: str) -> Dict[str, Any]:
        """
        Parse a JSON response out of the model text. If parsing fails,
        return a conservative fallback.
        """
        try:
            m = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if m:
                obj = json.loads(m.group(0))
                # Normalize fields
                plan = obj.get("plan", [])
                confidence = float(obj.get("confidence", 0.0))
                reasoning = obj.get("reasoning", "")
                alts = obj.get("alternatives", [])
                risks = obj.get("risks", [])
                next_step = obj.get("next_step", "")
                return {
                    "plan": plan if isinstance(plan, list) else [],
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "alternatives": alts if isinstance(alts, list) else [],
                    "risks": risks if isinstance(risks, list) else [],
                    "next_step": next_step,
                }
        except Exception:
            pass

        # Fallback
        return {
            "plan": [],
            "confidence": 0.0,
            "reasoning": "",
            "alternatives": [],
            "risks": [],
            "next_step": "",
        }
