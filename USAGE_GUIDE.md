# Agent System Usage Guide

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the project root:

```bash
# .env file
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

**Important**: Replace `your_actual_gemini_api_key_here` with your real Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

### 3. Grant Accessibility Permissions

On macOS, you need to grant accessibility permissions:

1. Open **System Settings** → **Privacy & Security** → **Accessibility**
2. Add your terminal application (Terminal, iTerm2, etc.) to the list
3. Add your IDE (Cursor, VS Code, etc.) to the list
4. Ensure both are enabled

### 4. Test the System

```bash
# Run basic test
python test_agent.py

# Run with specific goal
python agent_core.py "optimize battery life" "System Settings"

# Debug Gemini prompts
python debug_gemini_prompt.py
```

## Core Usage

### Basic Agent Operation

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
print(f"Iterations: {result['iterations']}")
print(f"Errors: {result['errors']}")
```

### Individual Component Usage

#### Perception Engine

```python
from perception import PerceptionEngine

perception = PerceptionEngine()

# Discover UI elements
ui_signals = perception.discover_ui_signals("System Settings")
print(f"Found {len(ui_signals)} UI elements")

# Get system state
system_state = perception.get_system_state()
print(f"Battery: {system_state.battery_level}%")

# Get context
context = perception.get_context("System Settings")
print(f"App: {context['app_name']}")
```

#### Reasoning Engine

```python
from reasoning import ReasoningEngine

reasoning = ReasoningEngine()

# Gather knowledge
knowledge = reasoning.gather_knowledge("optimize battery life", perception_data)

# Analyze situation
plan = reasoning.analyze_situation(
    goal="optimize battery life",
    perception=perception_data,
    knowledge=knowledge,
    agent_state=agent_state
)

print(f"Confidence: {plan['confidence']}")
print(f"Plan: {plan['plan']}")
```

#### Action Engine

```python
from action import ActionEngine

action_engine = ActionEngine()

# Execute single action
result = action_engine.execute_action({
    "action": "click",
    "target": "AX_FEATURE_DISPLAY",
    "reason": "Navigate to display settings"
})

print(f"Success: {result['success']}")

# Execute action sequence
actions = [
    {"action": "click", "target": "AXButton_533.0_310.0"},
    {"action": "wait", "duration": 1.0},
    {"action": "click", "target": "AXButton_340.0_276.0"}
]

results = action_engine.execute_action_sequence(actions)
```

#### Memory System

```python
from memory import MemorySystem

memory = MemorySystem()

# Store experiences
memory.store_perception(perception_data)
memory.store_reasoning(reasoning_data)
memory.store_actions(action_results)

# Retrieve relevant memories
relevant = memory.retrieve_relevant_memories("battery optimization")

# Learn from experience
insights = memory.learn_from_experience()
print(f"Learning confidence: {insights['learning_confidence']}")

# Export memories
memory.export_memories("memories.json")
```

## Advanced Usage

### Custom Goals

The agent can handle various types of goals:

```python
# Battery optimization
agent.run_autonomous_loop("optimize battery life", "System Settings")

# Security enhancement
agent.run_autonomous_loop("enhance security", "System Settings")

# Accessibility improvement
agent.run_autonomous_loop("improve accessibility", "System Settings")

# Custom application
agent.run_autonomous_loop("configure display settings", "System Settings")
```

### Custom Action Types

You can extend the action engine with custom actions:

```python
class CustomActionEngine(ActionEngine):
    def _execute_custom_action(self, target: str, params: dict) -> dict:
        """Execute a custom action"""
        try:
            # Your custom logic here
            return {"success": True, "result": "Custom action completed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### Memory Management

```python
# Configure memory limits
memory = MemorySystem(max_memories=2000)

# Enable/disable learning
memory.learning_enabled = True

# Get memory summary
summary = memory.get_memory_summary()
print(f"Total memories: {summary['total_memories']}")
print(f"Memory usage: {summary['memory_usage_percent']}%")

# Import/export memories
memory.export_memories("backup.json")
memory.import_memories("backup.json")
```

### Error Handling

```python
try:
    result = agent.run_autonomous_loop(goal, target_app)
    if not result['success']:
        print(f"Agent failed after {result['iterations']} iterations")
        print(f"Errors: {result['errors']}")
except KeyboardInterrupt:
    print("Agent stopped by user")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Configuration Options

### Agent Configuration

```python
agent = AgentCore()

# Configure limits
agent.max_errors = 10          # Maximum errors before stopping
agent.max_iterations = 20       # Maximum iterations per run

# Configure state
agent.state.goal = "custom goal"
agent.state.progress = 0.5
agent.state.confidence = 0.8
```

### Perception Configuration

```python
perception = PerceptionEngine()

# Configure scanning limits
perception.max_elements = 100   # Maximum elements to scan
perception.max_windows = 3      # Maximum windows to scan
```

### Action Configuration

```python
action_engine = ActionEngine()

# Configure retry settings
action_engine.max_retries = 5
action_engine.action_timeout = 15.0
```

## Troubleshooting

### Common Issues

#### 1. "GEMINI_API_KEY not found"

**Solution**: Create `.env` file with your actual API key

```bash
echo "GEMINI_API_KEY=your_actual_key_here" > .env
```

#### 2. "Accessibility permission denied"

**Solution**: Grant accessibility permissions in System Settings

1. System Settings → Privacy & Security → Accessibility
2. Add your terminal and IDE to the list
3. Ensure both are enabled

#### 3. "Element not found"

**Solution**: Check if the target application is open and accessible

```python
# Debug element finding
from action import ActionEngine
action_engine = ActionEngine()
element = action_engine._find_element("AX_FEATURE_DISPLAY")
print(f"Element found: {element is not None}")
```

#### 4. "Gemini API error"

**Solution**: Check your API key and network connectivity

```python
# Test Gemini connection
from reasoning import ReasoningEngine
reasoning = ReasoningEngine()
print(f"Gemini available: {reasoning.model is not None}")
```

### Debug Tools

#### Debug Gemini Prompts

```bash
python debug_gemini_prompt.py
```

This shows exactly what Gemini receives and responds with.

#### Test Individual Components

```python
# Test perception
from perception import PerceptionEngine
perception = PerceptionEngine()
signals = perception.discover_ui_signals("System Settings")
print(f"Found {len(signals)} signals")

# Test reasoning
from reasoning import ReasoningEngine
reasoning = ReasoningEngine()
# ... test reasoning logic

# Test actions
from action import ActionEngine
action_engine = ActionEngine()
# ... test action execution
```

#### Memory Analysis

```python
# Analyze memory patterns
memory = MemorySystem()
patterns = memory.get_patterns("success")
print(f"Success patterns: {patterns}")

# Export memories for analysis
memory.export_memories("analysis.json")
```

## Performance Optimization

### Scanning Optimization

```python
# Limit elements to prevent performance issues
perception.max_elements = 50
perception.max_windows = 2
```

### Memory Optimization

```python
# Configure memory limits
memory = MemorySystem(max_memories=1000)
memory.learning_enabled = True
```

### Action Optimization

```python
# Configure action timeouts
action_engine.action_timeout = 5.0
action_engine.max_retries = 3
```

## Best Practices

### 1. Goal Definition

- Be specific: "optimize battery life" vs "save power"
- Include context: "enable Low Power Mode when battery is low"
- Consider constraints: "without affecting performance"

### 2. Error Handling

- Always check return values
- Handle KeyboardInterrupt gracefully
- Implement retry logic for transient failures

### 3. Memory Management

- Export memories regularly
- Monitor memory usage
- Clean up old memories when needed

### 4. Testing

- Test with different applications
- Test with different system states
- Test error conditions

### 5. Security

- Never commit API keys
- Use environment variables
- Validate user inputs

## Examples

### Example 1: Battery Optimization

```python
from agent_core import AgentCore

agent = AgentCore()
result = agent.run_autonomous_loop(
    goal="optimize battery life",
    target_app="System Settings",
    max_iterations=5
)

if result['success']:
    print("Battery optimization completed successfully")
else:
    print(f"Failed after {result['iterations']} iterations")
```

### Example 2: Security Enhancement

```python
from agent_core import AgentCore

agent = AgentCore()
result = agent.run_autonomous_loop(
    goal="enhance security settings",
    target_app="System Settings",
    max_iterations=3
)

print(f"Security enhancement: {result['success']}")
```

### Example 3: Custom Workflow

```python
from agent_core import AgentCore
from perception import PerceptionEngine
from reasoning import ReasoningEngine
from action import ActionEngine

# Create components
agent = AgentCore()
perception = agent.perception
reasoning = agent.reasoning
action = agent.action

# Custom workflow
perception_data = perception.discover_ui_signals("Calculator")
knowledge = reasoning.gather_knowledge("calculate 1+2", perception_data)
plan = reasoning.analyze_situation("calculate 1+2", perception_data, knowledge, agent.state)

# Execute plan
for action_item in plan['plan']:
    result = action.execute_action(action_item)
    print(f"Action {action_item['action']}: {result['success']}")
```

## Support

### Getting Help

1. Check the troubleshooting section above
2. Run debug tools to identify issues
3. Check the architecture documentation
4. Review error messages and logs

### Contributing

1. Follow the modular architecture
2. Add comprehensive error handling
3. Include tests for new features
4. Update documentation

### Reporting Issues

When reporting issues, include:

1. Error messages and stack traces
2. System information (macOS version, Python version)
3. Steps to reproduce
4. Debug output from tools

This usage guide provides comprehensive information for using the agent system effectively. The system is designed to be robust, intelligent, and easy to use while providing powerful automation capabilities.
