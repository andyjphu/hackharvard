# Autonomous Agent System

A complete rearchitecture of an intelligent autonomous agent system that can perceive, reason, and act using macOS accessibility APIs. The system implements a modular perceive-reason-act loop with intelligent reasoning powered by Gemini 2.0 Flash.

## 🚀 Features

- **Autonomous Operation**: Complete perceive-reason-act loop with intelligent decision making
- **UI Automation**: Click, type, select, and interact with any macOS application
- **Intelligent Reasoning**: Powered by Gemini 2.0 Flash for contextual planning
- **Memory & Learning**: Stores experiences and learns from patterns
- **Modular Architecture**: Clean separation of concerns with 5 core modules
- **Robust Error Handling**: Comprehensive error recovery and retry logic
- **Position-based Element Finding**: Reliable UI element identification
- **System Monitoring**: Battery, CPU, memory, and network state awareness

## 🏗️ Architecture

The system consists of 5 core modules:

1. **Agent Core** (`agent_core.py`) - Main orchestration and perceive-reason-act loop
2. **Perception Engine** (`perception.py`) - UI scanning and system monitoring
3. **Reasoning Engine** (`reasoning.py`) - Gemini-powered intelligent planning
4. **Action Engine** (`action.py`) - UI interaction and automation
5. **Memory System** (`memory.py`) - Experience storage and learning

## 📋 Requirements

- macOS with accessibility APIs enabled
- Python 3.7+
- Gemini API key
- Terminal/IDE with accessibility permissions

## 🛠️ Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd hackharvard
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file:

```bash
echo "GEMINI_API_KEY=your_actual_gemini_api_key_here" > .env
```

Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

### 3. Grant Permissions

1. Open **System Settings** → **Privacy & Security** → **Accessibility**
2. Add your terminal and IDE to the list
3. Ensure both are enabled

## 🚀 Quick Start

### Easiest Way to Get Started

```bash
# 1. Setup (first time only)
python setup.py

# 2. Run the agent
python main.py
```

### Alternative: Command Line Interface

```bash
# Run with specific goal
python agent_core.py "optimize battery life" "System Settings"
python agent_core.py "enhance security" "System Settings"
python agent_core.py "calculate 1+2" "Calculator"

# With options
python agent_core.py "optimize battery life" --max-iterations 10 --verbose
```

### Programmatic Usage

```python
from agent_core import AgentCore

# Create agent
agent = AgentCore()

# Run autonomous loop
result = agent.run_autonomous_loop(
    goal="optimize battery life",
    target_app="System Settings",
    max_iterations=5
)

print(f"Success: {result['success']}")
```

### Test the System

```bash
# Run comprehensive tests
python test_agent.py

# Debug Gemini prompts
python debug_gemini_prompt.py
```

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed system architecture and design decisions
- **[USAGE_GUIDE.md](USAGE_GUIDE.md)** - Comprehensive usage guide with examples
- **[requirements.txt](requirements.txt)** - Python dependencies

## 🎯 Example Goals (Natural Language)

The agent understands natural language goals and automatically chooses the right app:

```bash
# Battery optimization
python agent_core.py "save battery life"
python agent_core.py "make my computer use less power"

# Security enhancement
python agent_core.py "make my computer more secure"
python agent_core.py "enable security features"

# Calculator automation
python agent_core.py "help me calculate 15 + 27"
python agent_core.py "what is 100 divided by 4"

# Web search
python agent_core.py "search for the meaning of life on Google"
python agent_core.py "look up Python programming tutorials"

# Writing tasks
python agent_core.py "write a note about my meeting"
python agent_core.py "create a document about the project"

# Calendar tasks
python agent_core.py "schedule a meeting for tomorrow"
python agent_core.py "add an event to my calendar"
```

### Intelligent App Selection

The agent automatically chooses the right application based on your goal:

- **"save battery life"** → System Settings
- **"calculate 15 + 27"** → Calculator
- **"search on Google"** → Google Chrome
- **"write a note"** → Cursor/Text Editor
- **"schedule meeting"** → Calendar
- **"make computer secure"** → System Settings

## 🔧 Key Components

### Perception Engine

- Scans UI elements with position-based IDs
- Monitors system state (battery, CPU, memory)
- Analyzes application context
- Identifies system constraints

### Reasoning Engine

- Integrates Gemini 2.0 Flash for intelligent planning
- Combines UI signals, system state, and domain knowledge
- Generates structured action plans with confidence scores
- Provides alternatives and risk assessment

### Action Engine

- Executes actions on UI elements (click, type, select, scroll)
- Uses multiple element finding strategies
- Implements retry logic and error handling
- Validates actions before execution

### Memory System

- Stores perceptions, reasonings, and actions
- Implements relevance-based retrieval
- Recognizes success/failure patterns
- Enables learning from experience

## 🐛 Troubleshooting

### Common Issues

**"GEMINI_API_KEY not found"**

- Create `.env` file with your actual API key
- Ensure key is valid and active

**"Accessibility permission denied"**

- Grant accessibility permissions in System Settings
- Add terminal and IDE to accessibility list

**"Element not found"**

- Ensure target application is open and accessible
- Check element IDs in debug output

**"Gemini API error"**

- Verify API key and network connectivity
- Check Gemini service status

### Debug Tools

```bash
# Debug Gemini prompts and responses
python debug_gemini_prompt.py

# Test individual components
python -c "from agent_core import AgentCore; agent = AgentCore(); print('Agent created successfully')"
```

## 📊 System Status

The system has been completely rearchitected from scratch with all critical issues resolved:

- ✅ **Element Finding**: Fixed critical bug with `findAllR()` vs `findFirst()`
- ✅ **ID Matching**: Robust position-based element ID generation
- ✅ **Gemini Integration**: Working perfectly with structured prompts
- ✅ **Memory System**: Complete experience storage and learning
- ✅ **Error Handling**: Comprehensive error recovery
- ✅ **Modular Design**: Clean separation of concerns

## 🔒 Security

- API keys stored in `.env` file (never committed)
- Local processing of all UI interactions
- No external data transmission except to Gemini
- Accessibility permissions handled securely

## 🚀 Performance

- Optimized UI scanning with element limits
- Efficient memory management with deque
- Action execution with timeout protection
- Comprehensive error handling and recovery

## 🤝 Contributing

1. Follow the modular architecture
2. Add comprehensive error handling
3. Include tests for new features
4. Update documentation

## 📄 License

This project is for educational and research purposes. Please ensure compliance with macOS accessibility guidelines and Google Gemini API terms of service.

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section
2. Run debug tools to identify problems
3. Review architecture documentation
4. Check error messages and logs

---

**Note**: This system requires macOS with accessibility APIs enabled and a valid Gemini API key. The agent is designed for autonomous UI automation and should be used responsibly.
