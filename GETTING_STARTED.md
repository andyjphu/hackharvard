# Getting Started with the Autonomous Agent System

## 🚀 Quick Start (5 minutes)

### Step 1: Setup

```bash
# Clone and navigate to the project
cd hackharvard

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Key

```bash
# Get your API key from: https://makersuite.google.com/app/apikey
echo "GEMINI_API_KEY=your_actual_key_here" > .env
```

### Step 3: Grant Permissions

1. Open **System Settings** → **Privacy & Security** → **Accessibility**
2. Add your terminal and IDE to the list
3. Ensure both are enabled

### Step 4: Run the Agent

```bash
# Easiest way - interactive menu
python main.py

# Or command line
python agent_core.py "optimize battery life"
```

## 🎯 What You Can Do

The agent can automate various tasks:

### Battery Optimization

```bash
python agent_core.py "optimize battery life"
```

- Enables Low Power Mode
- Reduces screen brightness
- Closes background applications

### Security Enhancement

```bash
python agent_core.py "enhance security"
```

- Enables FileVault encryption
- Configures firewall settings
- Sets up Touch ID

### Accessibility Improvement

```bash
python agent_core.py "improve accessibility"
```

- Configures VoiceOver
- Sets up Zoom magnification
- Enables High Contrast

### Calculator Automation

```bash
python agent_core.py "calculate 1+2" "Calculator"
```

- Automates calculator operations
- Performs mathematical calculations

## 🔧 Available Commands

### Main Entry Points

- `python main.py` - Interactive menu (easiest)
- `python agent_core.py "goal"` - Command line interface
- `python interactive_agent.py` - Advanced interactive mode

### Setup and Testing

- `python setup.py` - Automated setup
- `python test_main.py` - Test functionality
- `python test_agent.py` - Comprehensive tests

### Debug Tools

- `python debug_gemini_prompt.py` - Debug Gemini prompts
- `python agent_core.py --help` - Show all options

## 📋 Command Line Options

```bash
# Basic usage
python agent_core.py "goal" "target_app"

# With options
python agent_core.py "goal" "target_app" --max-iterations 10 --verbose

# Examples
python agent_core.py "optimize battery life" "System Settings"
python agent_core.py "enhance security" "System Settings" --max-iterations 5
python agent_core.py "calculate 1+2" "Calculator" --verbose
```

## 🐛 Troubleshooting

### Common Issues

**"GEMINI_API_KEY not found"**

```bash
# Create .env file with your API key
echo "GEMINI_API_KEY=your_actual_key_here" > .env
```

**"Accessibility permission denied"**

- Grant accessibility permissions in System Settings
- Add terminal and IDE to accessibility list

**"Element not found"**

- Ensure target application is open
- Check if application is accessible

**"Gemini API error"**

- Verify API key is correct and active
- Check network connectivity

### Debug Steps

1. **Test Setup**

   ```bash
   python test_main.py
   ```

2. **Debug Gemini**

   ```bash
   python debug_gemini_prompt.py
   ```

3. **Check Permissions**
   - System Settings → Privacy & Security → Accessibility
   - Ensure terminal and IDE are enabled

## 📚 Next Steps

### Learn More

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Check [USAGE_GUIDE.md](USAGE_GUIDE.md) for advanced usage
- Explore the code in `agent_core.py`, `perception.py`, etc.

### Customize

- Modify goals in `main.py`
- Add custom actions in `action.py`
- Extend reasoning in `reasoning.py`

### Examples

```python
# Programmatic usage
from agent_core import AgentCore

agent = AgentCore()
result = agent.run_autonomous_loop(
    goal="your custom goal",
    target_app="Your App",
    max_iterations=10
)
```

## 🆘 Need Help?

1. Check the troubleshooting section above
2. Run debug tools to identify issues
3. Review error messages and logs
4. Check the comprehensive documentation

## 🎉 Success!

Once you see:

```
✅ Task completed successfully!
💾 Results saved to agent_result_*.json
```

Your agent is working! You can now automate various tasks on macOS using natural language goals.
