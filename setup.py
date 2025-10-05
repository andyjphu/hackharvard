#!/usr/bin/env python3
"""
Setup script for the Autonomous Agent System
Helps with initial configuration and setup.
"""

import os
import sys
import subprocess


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def check_virtual_environment():
    """Check if we're in a virtual environment"""
    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        print("✅ Virtual environment detected")
        return True
    else:
        print("⚠️  Not in a virtual environment")
        print("Consider running: python -m venv .venv && source .venv/bin/activate")
        return False


def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
        )
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def setup_env_file():
    """Setup .env file with API key"""
    env_file = ".env"

    if os.path.exists(env_file):
        print(f"✅ {env_file} already exists")
        with open(env_file, "r") as f:
            content = f.read()
            if "GEMINI_API_KEY" in content and "your_api_key_here" not in content:
                print("✅ GEMINI_API_KEY appears to be configured")
                return True
            else:
                print("⚠️  GEMINI_API_KEY needs to be configured")
    else:
        print(f"📝 Creating {env_file} file...")

    print("\n🔑 Gemini API Key Setup")
    print("Get your API key from: https://makersuite.google.com/app/apikey")
    print()

    api_key = input("Enter your Gemini API key (or press Enter to skip): ").strip()

    if api_key:
        with open(env_file, "w") as f:
            f.write(f"GEMINI_API_KEY={api_key}\n")
        print(f"✅ API key saved to {env_file}")
        return True
    else:
        print("⚠️  Skipping API key setup")
        print("You can set it later by editing .env file")
        return False


def check_accessibility_permissions():
    """Check accessibility permissions"""
    print("\n🔐 Accessibility Permissions")
    print("The agent needs accessibility permissions to control other apps.")
    print()
    print("To grant permissions:")
    print("1. Open System Settings → Privacy & Security → Accessibility")
    print("2. Add your terminal application (Terminal, iTerm2, etc.)")
    print("3. Add your IDE (Cursor, VS Code, etc.)")
    print("4. Ensure both are enabled")
    print()

    input("Press Enter when you've granted accessibility permissions...")


def test_setup():
    """Test the setup"""
    print("\n🧪 Testing Setup...")

    try:
        # Test imports
        from agent_core import AgentCore

        print("✅ Agent core imports successfully")

        # Test API key
        from dotenv import load_dotenv

        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "your_api_key_here":
            print("✅ API key is configured")
        else:
            print("⚠️  API key not configured")
            return False

        # Test basic agent creation
        agent = AgentCore()
        print("✅ Agent can be created")

        print("✅ Setup test passed!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        return False


def main():
    """Main setup function"""
    print("🤖 Autonomous Agent System Setup")
    print("=" * 40)
    print("This script will help you set up the agent system.")
    print()

    # Check Python version
    if not check_python_version():
        return

    # Check virtual environment
    check_virtual_environment()

    # Install dependencies
    if not install_dependencies():
        return

    # Setup environment file
    setup_env_file()

    # Check accessibility permissions
    check_accessibility_permissions()

    # Test setup
    if test_setup():
        print("\n🎉 Setup completed successfully!")
        print()
        print("You can now run the agent with:")
        print("  python main.py")
        print()
        print("Or use the command line interface:")
        print('  python agent_core.py "optimize battery life"')
        print('  python agent_core.py "enhance security"')
    else:
        print("\n❌ Setup test failed")
        print("Please check the errors above and try again")


if __name__ == "__main__":
    main()
