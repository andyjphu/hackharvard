#!/usr/bin/env python3
"""
Clean Direct Agent - No iterations, just do the task once
"""

import sys
import argparse
from dataclasses import dataclass
from perception import PerceptionEngine
from reasoning import ReasoningEngine
from action import ActionEngine

@dataclass
class SimpleAgentState:
    """Simple agent state"""
    goal: str
    progress: float = 0.0
    error_count: int = 0

def main():
    parser = argparse.ArgumentParser(description="Clean Direct Agent")
    parser.add_argument("goal", help="Goal to achieve")
    parser.add_argument("--target-app", help="Target application")
    args = parser.parse_args()

    print(f"🎯 CLEAN DIRECT AGENT")
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
        agent_state = SimpleAgentState(goal=args.goal)
        reasoning_result = reasoning.analyze_situation(args.goal, full_perception, {}, agent_state)
        
        if "error" in reasoning_result:
            print(f"❌ Reasoning failed: {reasoning_result['error']}")
            return

        print(f"✅ Generated plan with {reasoning_result.get('confidence', 0):.2f} confidence")
        print(f"Plan: {reasoning_result.get('plan', [])}")

        # 3. Act
        print("🎯 ACTING...")
        plan = reasoning_result.get('plan', [])
        success_count = 0
        total_actions = len(plan)
        
        for i, action_item in enumerate(plan):
            print(f"   Executing action {i+1}/{total_actions}: {action_item.get('action')} on {action_item.get('target')}")
            result = action.execute_action(action_item)
            if result.get('success'):
                success_count += 1
                print(f"   ✅ Action successful")
            else:
                print(f"   ❌ Action failed: {result.get('error', 'Unknown error')}")
        
        action_result = {
            'success': success_count == total_actions,
            'successful_actions': success_count,
            'total_actions': total_actions
        }
        
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
