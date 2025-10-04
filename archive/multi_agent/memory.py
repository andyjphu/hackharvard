#!/usr/bin/env python3
"""
Memory System - Handles all memory storage, retrieval, and learning
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque


@dataclass
class MemoryEntry:
    """A single memory entry"""

    id: str
    type: str
    content: Dict[str, Any]
    timestamp: float
    importance: float = 1.0
    access_count: int = 0


class MemorySystem:
    """
    Handles all memory operations:
    - Perception storage and retrieval
    - Reasoning history
    - Action results and learning
    - Pattern recognition
    - Long-term memory management
    """

    def __init__(self, max_memories: int = 1000):
        self.max_memories = max_memories
        self.perceptions = deque(maxlen=max_memories)
        self.reasonings = deque(maxlen=max_memories)
        self.actions = deque(maxlen=max_memories)
        self.episodes = deque(maxlen=100)  # Complete perceive-reason-act episodes

        self.memory_counter = 0
        self.learning_enabled = True

    def store_perception(self, perception_data: Dict[str, Any]) -> str:
        """Store perception data in memory"""
        memory_id = f"perception_{self.memory_counter}_{int(time.time())}"

        entry = MemoryEntry(
            id=memory_id,
            type="perception",
            content=perception_data,
            timestamp=time.time(),
            importance=self._calculate_importance(perception_data),
        )

        self.perceptions.append(entry)
        self.memory_counter += 1

        return memory_id

    def store_reasoning(self, reasoning_data: Dict[str, Any]) -> str:
        """Store reasoning data in memory"""
        memory_id = f"reasoning_{self.memory_counter}_{int(time.time())}"

        entry = MemoryEntry(
            id=memory_id,
            type="reasoning",
            content=reasoning_data,
            timestamp=time.time(),
            importance=self._calculate_importance(reasoning_data),
        )

        self.reasonings.append(entry)
        self.memory_counter += 1

        return memory_id

    def store_actions(self, action_data: List[Dict[str, Any]]) -> str:
        """Store action data in memory"""
        memory_id = f"actions_{self.memory_counter}_{int(time.time())}"

        entry = MemoryEntry(
            id=memory_id,
            type="actions",
            content={"actions": action_data},
            timestamp=time.time(),
            importance=self._calculate_importance({"actions": action_data}),
        )

        self.actions.append(entry)
        self.memory_counter += 1

        return memory_id

    def store_episode(self, episode_data: Dict[str, Any]) -> str:
        """Store a complete perceive-reason-act episode"""
        memory_id = f"episode_{self.memory_counter}_{int(time.time())}"

        entry = MemoryEntry(
            id=memory_id,
            type="episode",
            content=episode_data,
            timestamp=time.time(),
            importance=self._calculate_episode_importance(episode_data),
        )

        self.episodes.append(entry)
        self.memory_counter += 1

        return memory_id

    def retrieve_relevant_memories(
        self, query: str, memory_type: str = None, limit: int = 10
    ) -> List[MemoryEntry]:
        """Retrieve memories relevant to a query"""
        relevant_memories = []

        # Search through all memory types
        memory_sources = []
        if memory_type is None or memory_type == "perception":
            memory_sources.extend(self.perceptions)
        if memory_type is None or memory_type == "reasoning":
            memory_sources.extend(self.reasonings)
        if memory_type is None or memory_type == "actions":
            memory_sources.extend(self.actions)
        if memory_type is None or memory_type == "episode":
            memory_sources.extend(self.episodes)

        # Simple relevance scoring (in a real system, this would be more sophisticated)
        for memory in memory_sources:
            relevance_score = self._calculate_relevance(memory, query)
            if relevance_score > 0.3:  # Threshold for relevance
                relevant_memories.append((memory, relevance_score))

        # Sort by relevance and return top results
        relevant_memories.sort(key=lambda x: x[1], reverse=True)
        return [memory for memory, score in relevant_memories[:limit]]

    def get_patterns(self, pattern_type: str = "success") -> List[Dict[str, Any]]:
        """Identify patterns in memory"""
        patterns = []

        if pattern_type == "success":
            # Find successful action patterns
            successful_actions = []
            for action_memory in self.actions:
                actions = action_memory.content.get("actions", [])
                for action in actions:
                    if action.get("success", False):
                        successful_actions.append(action)

            # Find common patterns in successful actions
            action_types = {}
            for action in successful_actions:
                action_type = action.get("action", "")
                if action_type not in action_types:
                    action_types[action_type] = 0
                action_types[action_type] += 1

            patterns.append(
                {
                    "type": "successful_actions",
                    "data": action_types,
                    "confidence": len(successful_actions) / max(len(self.actions), 1),
                }
            )

        elif pattern_type == "failure":
            # Find failure patterns
            failed_actions = []
            for action_memory in self.actions:
                actions = action_memory.content.get("actions", [])
                for action in actions:
                    if not action.get("success", False):
                        failed_actions.append(action)

            # Find common failure patterns
            error_types = {}
            for action in failed_actions:
                error = action.get("error", "Unknown error")
                if error not in error_types:
                    error_types[error] = 0
                error_types[error] += 1

            patterns.append(
                {
                    "type": "failed_actions",
                    "data": error_types,
                    "confidence": len(failed_actions) / max(len(self.actions), 1),
                }
            )

        return patterns

    def learn_from_experience(self) -> Dict[str, Any]:
        """Learn from stored experiences"""
        if not self.learning_enabled:
            return {"learning": "disabled"}

        print("   🧠 Learning from experience...")

        # Analyze patterns
        success_patterns = self.get_patterns("success")
        failure_patterns = self.get_patterns("failure")

        # Extract insights
        insights = {
            "successful_strategies": success_patterns,
            "common_failures": failure_patterns,
            "memory_usage": {
                "perceptions": len(self.perceptions),
                "reasonings": len(self.reasonings),
                "actions": len(self.actions),
                "episodes": len(self.episodes),
            },
            "learning_confidence": self._calculate_learning_confidence(),
        }

        return insights

    def _calculate_importance(self, data: Dict[str, Any]) -> float:
        """Calculate importance score for a memory entry"""
        importance = 1.0

        # Increase importance for successful actions
        if "actions" in data:
            actions = data.get("actions", [])
            success_rate = sum(
                1 for action in actions if action.get("success", False)
            ) / max(len(actions), 1)
            importance += success_rate

        # Increase importance for high-confidence reasoning
        if "confidence" in data:
            confidence = data.get("confidence", 0.5)
            importance += confidence

        # Increase importance for goal-related content
        if "goal" in str(data).lower():
            importance += 0.5

        return min(importance, 5.0)  # Cap at 5.0

    def _calculate_episode_importance(self, episode_data: Dict[str, Any]) -> float:
        """Calculate importance for a complete episode"""
        importance = 1.0

        # Check if episode was successful
        if episode_data.get("success", False):
            importance += 2.0

        # Check if episode achieved a goal
        if episode_data.get("goal_achieved", False):
            importance += 3.0

        # Check episode length (longer episodes might be more important)
        episode_length = episode_data.get("iterations", 1)
        importance += min(episode_length / 10.0, 1.0)

        return min(importance, 5.0)

    def _calculate_relevance(self, memory: MemoryEntry, query: str) -> float:
        """Calculate relevance score for a memory entry"""
        relevance = 0.0
        query_lower = query.lower()

        # Check content for query terms
        content_str = str(memory.content).lower()
        query_terms = query_lower.split()

        for term in query_terms:
            if term in content_str:
                relevance += 0.2

        # Boost relevance for recent memories
        age = time.time() - memory.timestamp
        if age < 3600:  # Less than 1 hour
            relevance += 0.3
        elif age < 86400:  # Less than 1 day
            relevance += 0.1

        # Boost relevance for important memories
        relevance += memory.importance * 0.1

        return min(relevance, 1.0)

    def _calculate_learning_confidence(self) -> float:
        """Calculate confidence in learning from experience"""
        total_memories = (
            len(self.perceptions) + len(self.reasonings) + len(self.actions)
        )

        if total_memories < 10:
            return 0.3  # Low confidence with few memories
        elif total_memories < 50:
            return 0.6  # Medium confidence
        else:
            return 0.9  # High confidence with many memories

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of the memory system"""
        return {
            "total_memories": len(self.perceptions)
            + len(self.reasonings)
            + len(self.actions)
            + len(self.episodes),
            "perceptions": len(self.perceptions),
            "reasonings": len(self.reasonings),
            "actions": len(self.actions),
            "episodes": len(self.episodes),
            "learning_enabled": self.learning_enabled,
            "memory_usage_percent": (
                len(self.perceptions)
                + len(self.reasonings)
                + len(self.actions)
                + len(self.episodes)
            )
            / self.max_memories
            * 100,
        }

    def export_memories(self, filepath: str) -> bool:
        """Export memories to a file"""
        try:
            memories = {
                "perceptions": [asdict(memory) for memory in self.perceptions],
                "reasonings": [asdict(memory) for memory in self.reasonings],
                "actions": [asdict(memory) for memory in self.actions],
                "episodes": [asdict(memory) for memory in self.episodes],
                "export_timestamp": time.time(),
            }

            with open(filepath, "w") as f:
                json.dump(memories, f, indent=2)

            return True
        except Exception as e:
            print(f"   ❌ Error exporting memories: {e}")
            return False

    def import_memories(self, filepath: str) -> bool:
        """Import memories from a file"""
        try:
            with open(filepath, "r") as f:
                memories = json.load(f)

            # Import each memory type
            for memory_data in memories.get("perceptions", []):
                memory = MemoryEntry(**memory_data)
                self.perceptions.append(memory)

            for memory_data in memories.get("reasonings", []):
                memory = MemoryEntry(**memory_data)
                self.reasonings.append(memory)

            for memory_data in memories.get("actions", []):
                memory = MemoryEntry(**memory_data)
                self.actions.append(memory)

            for memory_data in memories.get("episodes", []):
                memory = MemoryEntry(**memory_data)
                self.episodes.append(memory)

            return True
        except Exception as e:
            print(f"   ❌ Error importing memories: {e}")
            return False
