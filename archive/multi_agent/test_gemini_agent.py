#!/usr/bin/env python3
"""
Test script to demonstrate the Gemini-powered agent system
"""

import sys
from agent_core import AgentCore


def main():
    """Test the Gemini-powered agent system"""
    print("🤖 Testing Gemini-Powered Agent System")
    print("=" * 50)

    # Create agent
    agent = AgentCore()

    # Test with a simple goal
    goal = "optimize battery life"
    target_app = "System Settings"

    print(f"\n🎯 Goal: {goal}")
    print(f"🎯 Target App: {target_app}")
    print("-" * 40)

    try:
        # Run a single iteration to test Gemini reasoning
        print("\n🔄 SINGLE ITERATION TEST")
        print("-" * 30)

        # 1. Perceive
        print("1. PERCEIVING...")
        perception_data = agent.perceive(target_app)
        if "error" in perception_data:
            print(f"❌ Perception failed: {perception_data['error']}")
            return

        # 2. Reason
        print("\n2. REASONING...")
        reasoning_result = agent.reason(goal, perception_data)
        if "error" in reasoning_result:
            print(f"❌ Reasoning failed: {reasoning_result['error']}")
            return

        # 3. Act
        print("\n3. ACTING...")
        action_result = agent.act(reasoning_result)

        # Show results
        print(f"\n📊 RESULTS:")
        print(f"   UI Elements Found: {len(perception_data.get('ui_signals', []))}")
        print(f"   Reasoning Confidence: {reasoning_result.get('confidence', 0):.2f}")
        print(f"   Actions Generated: {len(reasoning_result.get('plan', []))}")
        print(f"   Actions Executed: {action_result.get('success_rate', 0):.2f}")

        # Show the plan
        plan = reasoning_result.get("plan", [])
        if plan:
            print(f"\n🎯 GENERATED PLAN:")
            for i, action in enumerate(plan, 1):
                print(
                    f"   {i}. {action.get('action', 'Unknown')} - {action.get('reason', 'No reason')}"
                )

        print(f"\n✅ Test completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
