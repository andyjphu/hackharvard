#!/usr/bin/env python3
"""
Test script to verify main.py functionality
"""

import os
import sys
from agent_core import AgentCore


def test_main_functionality():
    """Test the main functionality without interactive input"""

    print("🧪 Testing Main Functionality")
    print("=" * 40)

    # Check if API key is configured
    if (
        not os.getenv("GEMINI_API_KEY")
        or os.getenv("GEMINI_API_KEY") == "your_api_key_here"
    ):
        print("❌ GEMINI_API_KEY not configured!")
        print("Please create a .env file with your Gemini API key:")
        print("echo 'GEMINI_API_KEY=your_actual_key_here' > .env")
        return False

    print("✅ API key is configured")

    # Test agent creation
    try:
        agent = AgentCore()
        print("✅ Agent can be created")

        # Test a simple goal
        print("\n🚀 Testing with 'optimize battery life' goal...")
        result = agent.run_autonomous_loop(
            goal="optimize battery life",
            target_app="System Settings",
            max_iterations=2,  # Short test
        )

        print(f"✅ Test completed:")
        print(f"   Success: {result['success']}")
        print(f"   Iterations: {result['iterations']}")
        print(f"   Errors: {result['errors']}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_main_functionality()
    if success:
        print("\n🎉 Main functionality test passed!")
        print("You can now run: python main.py")
    else:
        print("\n❌ Main functionality test failed")
        print("Please check your setup and try again")
