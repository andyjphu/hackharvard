#!/usr/bin/env python3
"""
Memory System - Handles storage and retrieval of agent experiences
"""

from typing import Dict, List, Any


class MemorySystem:
    """Handles storage and retrieval of agent memories"""

    def __init__(self):
        self.perceptions: List[Dict[str, Any]] = []
        self.reasonings: List[Dict[str, Any]] = []
        self.actions: List[Dict[str, Any]] = []

    def store_perception(self, ui_signals, system_state, context, visual_analysis, correlations, timestamp) -> None:
        self.perceptions.append({
            "ui_signals": ui_signals,
            "system_state": system_state,
            "context": context,
            "visual_analysis": visual_analysis,
            "correlations": correlations,
            "timestamp": timestamp
        })

    def store_reasoning(self, reasoning_result: Dict[str, Any]) -> None:
        self.reasonings.append(reasoning_result)

    def store_actions(self, action_results: List[Dict[str, Any]]) -> None:
        self.actions.extend(action_results)
