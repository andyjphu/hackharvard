#!/usr/bin/env python3
"""
Memory System - Handles storage and retrieval of agent experiences
"""

from typing import Dict, List, Any, Optional
import time

class MemorySystem:
    """Handles storage and retrieval of agent memories"""
    
    def __init__(self):
        self.perceptions = []
        self.reasonings = []
        self.actions = []
    
    def store_perception(self, ui_signals: List[Dict], system_state: Dict, 
                        context: Dict, visual_analysis: Any, 
                        correlations: Dict, timestamp: float) -> None:
        """Store perception data in memory"""
        self.perceptions.append({
            "ui_signals": ui_signals,
            "system_state": system_state,
            "context": context,
            "visual_analysis": visual_analysis,
            "correlations": correlations,
            "timestamp": timestamp
        })
    
    def store_reasoning(self, reasoning_result: Dict[str, Any]) -> None:
        """Store reasoning result in memory"""
        self.reasonings.append(reasoning_result)
    
    def store_actions(self, action_results: List[Dict[str, Any]]) -> None:
        """Store action results in memory"""
        self.actions.extend(action_results)