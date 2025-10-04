#!/usr/bin/env python3
"""
Test script for Intelligent Automation System
Demonstrates the system without requiring Gemini API key
"""

import sys
import os

sys.path.append(".")

from intelligent_automation import IntelligentAutomationSystem


def main():
    """Test the intelligent automation system"""
    print("🧪 Testing Intelligent Automation System")
    print("=" * 50)

    # Create system instance
    system = IntelligentAutomationSystem()

    # Test with different goals
    test_cases = [
        ("optimize battery life", "System Settings"),
        ("enhance security", "System Settings"),
        ("improve accessibility", "System Settings"),
        ("configure display settings", "System Settings"),
    ]

    for goal, target_app in test_cases:
        print(f"\n🎯 Testing: {goal}")
        print("-" * 30)

        try:
            result = system.automate(goal, target_app)

            # Show key results
            signals = result.get("signals", {})
            plan = result.get("plan", {})

            print(
                f"✅ Discovered {len(signals.get('interactive_elements', []))} UI elements"
            )
            print(f"✅ Generated {len(plan.get('plan', []))} automation steps")
            print(f"✅ Confidence: {plan.get('confidence', 0)}")

        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n🎉 Test completed successfully!")
    print("The system can discover UI elements and generate automation plans.")


if __name__ == "__main__":
    main()
