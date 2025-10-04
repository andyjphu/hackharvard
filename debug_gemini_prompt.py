#!/usr/bin/env python3
"""
Debug script to show exactly what Gemini is receiving as input
"""

import sys
from agent_core import AgentCore


def main():
    """Debug the Gemini prompt"""
    print("🔍 DEBUGGING GEMINI PROMPT")
    print("=" * 60)

    # Create agent
    agent = AgentCore()

    # Get perception data
    print("1. PERCEPTION DATA:")
    print("-" * 30)
    perception = agent.perceive("System Settings")

    print(f"UI Signals found: {len(perception.get('ui_signals', []))}")
    for i, signal in enumerate(perception.get("ui_signals", [])[:5]):
        print(
            f"  {i+1}. ID: {signal.get('id')} | Type: {signal.get('type')} | Title: {signal.get('title')}"
        )

    print(f"\nSystem State: {perception.get('system_state')}")
    print(f"Context: {perception.get('context')}")

    # Get knowledge
    print("\n2. KNOWLEDGE DATA:")
    print("-" * 30)
    knowledge = agent.reasoning.gather_knowledge("optimize battery life", perception)
    print(f"Domain Knowledge: {knowledge.get('domain_knowledge')}")
    print(f"Best Practices: {knowledge.get('best_practices')}")
    print(f"System Recommendations: {knowledge.get('system_recommendations')}")

    # Build the actual prompt that Gemini sees
    print("\n3. COMPLETE GEMINI PROMPT:")
    print("=" * 60)
    prompt = agent.reasoning._build_reasoning_prompt(
        goal="optimize battery life",
        perception=perception,
        knowledge=knowledge,
        agent_state=agent.state,
    )

    print(prompt)
    print("\n" + "=" * 60)

    # Show what Gemini actually responds with
    print("\n4. GEMINI RESPONSE:")
    print("-" * 30)
    try:
        response = agent.reasoning.model.generate_content(prompt)
        print("Raw Gemini Response:")
        print(response.text)

        print("\nParsed Response:")
        parsed = agent.reasoning._parse_gemini_response(response.text)
        print(f"Plan: {parsed.get('plan')}")
        print(f"Confidence: {parsed.get('confidence')}")
        print(f"Reasoning: {parsed.get('reasoning')}")

    except Exception as e:
        print(f"Error getting Gemini response: {e}")


if __name__ == "__main__":
    main()
