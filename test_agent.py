#!/usr/bin/env python3
"""
Test script for the multi-file agent system
"""

import sys
import json
from agent_core import AgentCore


def main():
    """Test the multi-file agent system"""
    print("🤖 Testing Multi-File Agent System")
    print("=" * 50)

    # Create agent
    agent = AgentCore()

    # Test different scenarios
    test_cases = [
        ("optimize battery life", "System Settings"),
        ("enhance security", "System Settings"),
        ("improve accessibility", "System Settings"),
    ]

    for goal, target_app in test_cases:
        print(f"\n🎯 Testing: {goal}")
        print("-" * 30)

        try:
            # Run autonomous loop with limited iterations
            result = agent.run_autonomous_loop(goal, target_app, max_iterations=3)

            print(f"✅ Test completed:")
            print(f"   Iterations: {result['iterations']}")
            print(f"   Errors: {result['errors']}")
            print(f"   Success: {result['success']}")

        except Exception as e:
            print(f"❌ Test failed: {e}")

    # Show agent status
    print(f"\n📊 Agent Status:")
    status = agent.get_status()
    print(f"   Memory Size: {status['memory_size']}")
    print(f"   Reasoning Count: {status['reasoning_count']}")
    print(f"   Action Count: {status['action_count']}")

    # Save results
    with open("agent_test_result.json", "w") as f:
        json.dump(status, f, indent=2, default=str)

    print(f"\n💾 Test results saved to agent_test_result.json")


if __name__ == "__main__":
    main()
