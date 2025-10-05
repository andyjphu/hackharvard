#!/usr/bin/env python3
"""
Simple Direct Agent - No iterations, just do the task once
"""

import sys
import argparse
from perception import PerceptionEngine
from reasoning import ReasoningEngine
from action import ActionEngine

def main():
    parser = argparse.ArgumentParser(description="Simple Direct Agent")
    parser.add_argument("goal", help="Goal to achieve")
    parser.add_argument("--target-app", help="Target application")
    args = parser.parse_args()

    print(f"🎯 SIMPLE DIRECT AGENT")
    print(f"Goal: {args.goal}")
    print("=" * 50)

    # Initialize engines
    perception = PerceptionEngine()
    reasoning = ReasoningEngine()
    action = ActionEngine()

    try:
        # 1. Perceive
        print("🔍 PERCEIVING...")
        perception_data = perception.discover_ui_signals(args.target_app)
        system_state = perception.get_system_state()
        
        full_perception = {
            "ui_signals": perception_data,
            "system_state": system_state
        }
        
        print(f"✅ Found {len(perception_data)} UI elements")

        # 2. Reason
        print("🧠 REASONING...")
        from dataclasses import dataclass
        from agent_core import AgentState
        
        agent_state = AgentState(
            goal=args.goal,
            current_task="",
            progress=0.0,
            confidence=0.0,
            last_action="",
            error_count=0,
            session_id="simple"
        )
        
        reasoning_result = reasoning.analyze_situation(args.goal, full_perception, {}, agent_state)
        
        if "error" in reasoning_result:
            print(f"❌ Reasoning failed: {reasoning_result['error']}")
            return

        print(f"✅ Generated plan with {reasoning_result.get('confidence', 0):.2f} confidence")

        # 3. Act
        print("🎯 ACTING...")
        action_result = action.execute_plan(reasoning_result.get('plan', []))
        
        if action_result.get('success'):
            print("✅ TASK COMPLETED SUCCESSFULLY!")
        else:
            print(f"❌ Task failed: {action_result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
