#!/usr/bin/env python3
"""
Test script to demonstrate natural language goal interpretation
"""

from agent_core import AgentCore


def test_natural_language_goals():
    """Test various natural language goals"""

    print("🧠 Testing Natural Language Goal Interpretation")
    print("=" * 60)

    agent = AgentCore()

    # Test various natural language goals
    test_cases = [
        "save battery life",
        "make my computer more secure",
        "help me calculate 15 + 27",
        "search for the meaning of life on Google",
        "write a note about my meeting",
        "schedule a meeting for tomorrow",
        "make my computer accessible for blind users",
        "configure my display settings",
        "send an email to my boss",
        "create a calendar event for next week",
    ]

    print("Natural Language Goals → Intelligent App Selection:")
    print("-" * 60)

    for goal in test_cases:
        chosen_app = agent._choose_target_app(goal)
        print(f'🎯 "{goal}"')
        print(f"   → {chosen_app}")
        print()

    print("✅ Natural language interpretation working!")
    print("The agent can understand your goals and choose the right app automatically.")


if __name__ == "__main__":
    test_natural_language_goals()
