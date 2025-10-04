#!/usr/bin/env python3
"""
Agent CLI - Simple command-line interface for the autonomous agent system
"""

import sys
import os
from agent_core import AgentCore


def main():
    """Simple CLI for the agent system"""
    
    if len(sys.argv) < 2:
        print("🤖 Autonomous Agent System")
        print("=" * 40)
        print("Usage: python agent.py <goal> [target_app] [options]")
        print()
        print("Examples:")
        print('  python agent.py "optimize battery life"')
        print('  python agent.py "enhance security" "System Settings"')
        print('  python agent.py "improve accessibility" "System Settings"')
        print('  python agent.py "calculate 1+2" "Calculator"')
        print('  python agent.py "configure display settings" "System Settings"')
        print()
        print("Available options:")
        print("  --max-iterations N    Maximum iterations (default: 10)")
        print("  --max-errors N        Maximum errors before stopping (default: 5)")
        print("  --verbose             Enable verbose output")
        print("  --no-save             Don't save results to file")
        print()
        print("For detailed help: python agent_core.py --help")
        return

    # Extract goal and target app
    goal = sys.argv[1]
    target_app = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else "System Settings"
    
    # Extract options
    options = []
    for arg in sys.argv[2:]:
        if arg.startswith('--'):
            options.append(arg)
    
    # Build command
    cmd = [sys.executable, "agent_core.py", goal, target_app] + options
    
    # Execute
    import subprocess
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Agent failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n⏹️  Agent stopped by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
