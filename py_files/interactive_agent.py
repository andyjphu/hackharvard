#!/usr/bin/env python3
"""
Interactive Agent - Interactive goal selection and execution
"""

import sys
from agent_core import AgentCore


def show_goal_menu():
    """Display available goals menu"""
    print("🤖 Interactive Autonomous Agent")
    print("=" * 40)
    print("Select a goal:")
    print()
    print("1. Optimize battery life")
    print("2. Enhance security settings")
    print("3. Improve accessibility")
    print("4. Configure display settings")
    print("5. Calculator automation")
    print("6. Custom goal")
    print("7. Exit")
    print()


def get_goal_choice():
    """Get user's goal choice"""
    while True:
        try:
            choice = input("Enter your choice (1-7): ").strip()
            if choice in ['1', '2', '3', '4', '5', '6', '7']:
                return choice
            else:
                print("❌ Invalid choice. Please enter 1-7.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)


def get_goal_details(choice):
    """Get goal details based on choice"""
    goals = {
        '1': {
            'goal': 'optimize battery life',
            'target_app': 'System Settings',
            'description': 'Enable Low Power Mode, reduce screen brightness, close background apps'
        },
        '2': {
            'goal': 'enhance security settings',
            'target_app': 'System Settings',
            'description': 'Enable FileVault, configure firewall, set up Touch ID'
        },
        '3': {
            'goal': 'improve accessibility',
            'target_app': 'System Settings',
            'description': 'Configure VoiceOver, Zoom, High Contrast, and other accessibility features'
        },
        '4': {
            'goal': 'configure display settings',
            'target_app': 'System Settings',
            'description': 'Adjust brightness, resolution, color profiles, and display preferences'
        },
        '5': {
            'goal': 'calculate 1+2',
            'target_app': 'Calculator',
            'description': 'Automate calculator operations'
        },
        '6': {
            'goal': None,  # Will be prompted
            'target_app': None,  # Will be prompted
            'description': 'Custom goal and target application'
        }
    }
    
    return goals.get(choice, {})


def get_custom_goal():
    """Get custom goal from user"""
    print("\n📝 Custom Goal Configuration")
    print("-" * 30)
    
    goal = input("Enter your goal: ").strip()
    if not goal:
        print("❌ Goal cannot be empty")
        return None, None
    
    target_app = input("Enter target application (default: System Settings): ").strip()
    if not target_app:
        target_app = "System Settings"
    
    return goal, target_app


def get_execution_options():
    """Get execution options from user"""
    print("\n⚙️  Execution Options")
    print("-" * 20)
    
    try:
        max_iterations = input("Max iterations (default: 10): ").strip()
        max_iterations = int(max_iterations) if max_iterations else 10
        
        max_errors = input("Max errors (default: 5): ").strip()
        max_errors = int(max_errors) if max_errors else 5
        
        verbose = input("Verbose output? (y/N): ").strip().lower() == 'y'
        
        return max_iterations, max_errors, verbose
    except ValueError:
        print("❌ Invalid number, using defaults")
        return 10, 5, False


def run_agent(goal, target_app, max_iterations=10, max_errors=5, verbose=False):
    """Run the agent with specified parameters"""
    print(f"\n🚀 Starting Agent")
    print(f"Goal: {goal}")
    print(f"Target App: {target_app}")
    print(f"Max Iterations: {max_iterations}")
    print(f"Max Errors: {max_errors}")
    print("=" * 50)
    
    try:
        agent = AgentCore()
        agent.max_iterations = max_iterations
        agent.max_errors = max_errors
        
        result = agent.run_autonomous_loop(
            goal=goal,
            target_app=target_app,
            max_iterations=max_iterations
        )
        
        print(f"\n🏁 Agent Finished")
        print(f"Success: {result['success']}")
        print(f"Iterations: {result['iterations']}")
        print(f"Errors: {result['errors']}")
        print(f"Progress: {result['progress']:.2f}")
        
        return result
        
    except KeyboardInterrupt:
        print("\n⏹️  Agent stopped by user")
        return None
    except Exception as e:
        print(f"\n❌ Agent failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return None


def main():
    """Main interactive loop"""
    print("🤖 Welcome to the Interactive Autonomous Agent!")
    print("This agent can help you automate various tasks on macOS.")
    print()
    
    while True:
        show_goal_menu()
        choice = get_goal_choice()
        
        if choice == '7':
            print("👋 Goodbye!")
            break
        
        # Get goal details
        goal_info = get_goal_details(choice)
        
        if choice == '6':  # Custom goal
            goal, target_app = get_custom_goal()
            if goal is None:
                continue
        else:
            goal = goal_info['goal']
            target_app = goal_info['target_app']
            print(f"\n📋 Selected: {goal_info['description']}")
        
        # Confirm execution
        confirm = input(f"\nExecute '{goal}' on '{target_app}'? (Y/n): ").strip().lower()
        if confirm == 'n':
            continue
        
        # Get execution options
        max_iterations, max_errors, verbose = get_execution_options()
        
        # Run agent
        result = run_agent(goal, target_app, max_iterations, max_errors, verbose)
        
        if result:
            # Ask if user wants to run another goal
            another = input("\nRun another goal? (Y/n): ").strip().lower()
            if another == 'n':
                print("👋 Goodbye!")
                break


if __name__ == "__main__":
    main()
