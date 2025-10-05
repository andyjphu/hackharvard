#!/usr/bin/env python3
"""
Main Entry Point for the Autonomous Agent System
The simplest way to get started with the agent system.
"""

import sys
import os
from agent_core import AgentCore


def main():
    """Main entry point with simple goal selection"""

    print("🤖 Autonomous Agent System")
    print("=" * 50)
    print("Welcome! This agent can help you automate tasks on macOS.")
    print()

    # Check if API key is configured
    if (
        not os.getenv("GEMINI_API_KEY")
        or os.getenv("GEMINI_API_KEY") == "your_api_key_here"
    ):
        print("❌ GEMINI_API_KEY not configured!")
        print("Please create a .env file with your Gemini API key:")
        print("echo 'GEMINI_API_KEY=your_actual_key_here' > .env")
        print()
        print("Get your API key from: https://makersuite.google.com/app/apikey")
        return

    # Natural language goal input
    print("What would you like the agent to do?")
    print()
    print("Examples:")
    print("• 'save battery life'")
    print("• 'make my computer more secure'")
    print("• 'help me calculate 15 + 27'")
    print("• 'search for the meaning of life on Google'")
    print("• 'write a note about my meeting'")
    print("• 'schedule a meeting for tomorrow'")
    print()

    while True:
        try:
            goal = input("Enter your goal in natural language: ").strip()

            if not goal:
                print("❌ Goal cannot be empty")
                continue

            # The agent will automatically choose the target app
            target_app = None  # Let the agent choose intelligently
            description = f"Natural language goal: {goal}"
            break

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return

    # Create agent to get intelligent app selection
    agent = AgentCore()
    chosen_app = agent._choose_target_app(goal)

    # Confirm execution
    print(f"\n📋 Selected: {description}")
    print(f"Target App: {chosen_app} (chosen intelligently)")
    print()

    confirm = input("Start the agent? (Y/n): ").strip().lower()
    if confirm == "n":
        print("👋 Goodbye!")
        return

    # Run agent
    print(f"\n🚀 Starting Agent...")
    print(f"Goal: {goal}")
    print(f"Target App: {chosen_app}")
    print("=" * 50)

    try:
        # Run with reasonable defaults
        result = agent.run_autonomous_loop(
            goal=goal, target_app=chosen_app, max_iterations=5  # Reasonable default
        )

        # Show results
        print(f"\n🏁 Agent Finished!")
        print(f"Success: {result['success']}")
        print(f"Iterations: {result['iterations']}")
        print(f"Errors: {result['errors']}")
        print(f"Progress: {result['progress']:.2f}")

        if result["success"]:
            print("✅ Task completed successfully!")
        else:
            print("⚠️  Task completed with some issues")

        # Save results
        filename = f"agent_result_{goal.replace(' ', '_')}.json"
        import json

        with open(filename, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"💾 Results saved to {filename}")

    except KeyboardInterrupt:
        print("\n⏹️  Agent stopped by user")
    except Exception as e:
        print(f"\n❌ Agent failed: {e}")
        print("Check your setup and try again.")


if __name__ == "__main__":
    main()
