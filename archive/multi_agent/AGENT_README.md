# Multi-File Agent System

A modular reasoning and acting agent system for autonomous UI automation using macOS accessibility APIs.

## 🏗️ Architecture

The system is split into specialized modules that work together to create an autonomous agent:

### Core Components

1. **`agent_core.py`** - Main orchestration system

   - Perceive-Reason-Act loop
   - Agent state management
   - Autonomous operation control

2. **`perception.py`** - Environmental perception

   - UI element discovery
   - System state monitoring
   - Context analysis

3. **`reasoning.py`** - Reasoning and planning

   - Goal analysis
   - Plan generation using Gemini 2.0 Flash
   - Decision making and risk assessment

4. **`action.py`** - Action execution

   - UI interactions (click, type, select)
   - System actions and keyboard shortcuts
   - Action validation and error handling

5. **`memory.py`** - Memory and learning
   - Experience storage and retrieval
   - Pattern recognition
   - Learning from past actions

## 🚀 Usage

### Basic Usage

```bash
# Run autonomous agent
python agent_core.py "optimize battery life" "System Settings"

# Test the system
python test_agent.py
```

### Advanced Usage

```python
from agent_core import AgentCore

# Create agent
agent = AgentCore()

# Run autonomous loop
result = agent.run_autonomous_loop(
    goal="optimize battery life",
    target_app="System Settings",
    max_iterations=10
)

# Check agent status
status = agent.get_status()
print(f"Memory size: {status['memory_size']}")
```

## 🔧 Configuration

### Environment Setup

1. **Install dependencies:**

```bash
pip install atomacos psutil google-generativeai python-dotenv
```

2. **Set up Gemini API key (REQUIRED):**

```bash
# Create .env file with your actual Gemini API key
echo "GEMINI_API_KEY=your_actual_api_key_here" > .env
```

3. **Grant accessibility permissions:**
   - Go to System Preferences > Security & Privacy > Privacy > Accessibility
   - Add your terminal/IDE to the list

## 🧠 How It Works

### 1. Perception Phase

- Scans UI elements using accessibility APIs
- Monitors system state (battery, memory, CPU)
- Analyzes current context and constraints

### 2. Reasoning Phase

- Analyzes goal and current situation
- Uses Gemini 2.5 Flash-Lite for intelligent planning
- Generates action plans with confidence scores
- Identifies risks and alternatives

### 3. Action Phase

- Executes planned actions using accessibility APIs
- Handles errors and retries
- Monitors action success/failure
- Learns from experience

### 4. Memory Phase

- Stores all perceptions, reasonings, and actions
- Identifies patterns in successful/failed actions
- Learns from experience to improve future performance

## 📊 Agent Capabilities

### Perception

- ✅ Discovers 50+ UI elements per scan
- ✅ Monitors system state in real-time
- ✅ Identifies constraints and limitations
- ✅ Context-aware analysis

### Reasoning

- ✅ Goal-oriented planning
- ✅ Risk assessment and mitigation
- ✅ Alternative strategy generation
- ✅ Confidence-based decision making

### Action

- ✅ Click, type, select, scroll actions
- ✅ Dropdown menu handling
- ✅ Error recovery and retry logic
- ✅ Action validation

### Memory

- ✅ Experience storage and retrieval
- ✅ Pattern recognition
- ✅ Learning from success/failure
- ✅ Long-term memory management

## 🎯 Example Use Cases

### Battery Optimization

```bash
python agent_core.py "optimize battery life" "System Settings"
```

- Discovers Low Power Mode toggle
- Analyzes battery level and power source
- Plans optimal power management strategy
- Executes actions to enable power saving

### Security Enhancement

```bash
python agent_core.py "enhance security" "System Settings"
```

- Finds security-related settings
- Analyzes current security posture
- Plans security improvements
- Executes security configurations

### Accessibility Setup

```bash
python agent_core.py "improve accessibility" "System Settings"
```

- Discovers accessibility features
- Analyzes user needs
- Plans accessibility improvements
- Configures accessibility settings

## 🔍 Monitoring and Debugging

### Agent Status

```python
status = agent.get_status()
print(f"Progress: {status['state'].progress}")
print(f"Errors: {status['state'].error_count}")
print(f"Memory: {status['memory_size']} entries")
```

### Memory Analysis

```python
# Get memory summary
summary = agent.memory.get_memory_summary()
print(f"Total memories: {summary['total_memories']}")

# Learn from experience
insights = agent.memory.learn_from_experience()
print(f"Learning confidence: {insights['learning_confidence']}")
```

### Action History

```python
# Get action summary
action_summary = agent.action.get_action_summary()
print(f"Success rate: {action_summary['success_rate']:.2f}")
```

## 🚨 Error Handling

The system includes comprehensive error handling:

- **Perception errors**: Graceful fallback to partial information
- **Reasoning errors**: Fallback to rule-based reasoning
- **Action errors**: Retry logic and alternative approaches
- **Memory errors**: Safe storage and retrieval

## 🔮 Future Enhancements

### Planned Features

- **Real-time learning**: Continuous improvement from experience
- **Multi-modal perception**: Voice, gesture, and text input
- **Predictive planning**: Anticipate user needs
- **Cross-platform support**: Windows and Linux compatibility

### Integration Possibilities

- **Calendar integration**: Schedule automations
- **Cloud sync**: Share learning across devices
- **API access**: Third-party automation integration
- **Workflow orchestration**: Complex multi-step automations

## 📁 File Structure

```
/Users/andyphu/hackharvard/
├── agent_core.py          # Main agent orchestration
├── perception.py          # Environmental perception
├── reasoning.py           # Reasoning and planning
├── action.py             # Action execution
├── memory.py             # Memory and learning
├── test_agent.py         # Test script
├── AGENT_README.md       # This documentation
├── .env                  # Environment variables
└── agent_result.json     # Generated results
```

## 🎉 Success Metrics

The multi-file agent system successfully:

- ✅ **Modular Architecture**: Clean separation of concerns
- ✅ **Autonomous Operation**: Perceive-reason-act loop
- ✅ **Intelligent Planning**: Gemini 2.5 Flash-Lite integration
- ✅ **Learning Capability**: Memory and pattern recognition
- ✅ **Error Resilience**: Comprehensive error handling
- ✅ **Extensibility**: Easy to add new capabilities

This architecture provides a solid foundation for building sophisticated autonomous agents that can perceive, reason, and act in complex UI environments.
