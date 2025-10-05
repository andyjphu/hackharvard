# Agent System Architecture

## Overview

This is a complete rearchitecture of the autonomous agent system, built from scratch with all learned knowledge from previous iterations. The system implements a modular perceive-reason-act loop with intelligent reasoning powered by Gemini 2.0 Flash.

## Core Components

### 1. Agent Core (`agent_core.py`)

**Main orchestration system that coordinates all components**

- **Purpose**: Implements the perceive-reason-act loop
- **Key Features**:
  - Autonomous operation with configurable iterations
  - Error handling and recovery
  - State management (goal, progress, confidence, errors)
  - Memory integration for learning
  - Goal achievement detection

**Key Classes**:

- `AgentCore`: Main agent orchestrator
- `AgentState`: Tracks agent's current state (goal, progress, errors, etc.)

**Critical Methods**:

- `run_autonomous_loop()`: Main execution loop
- `perceive()`: Delegates to perception engine
- `reason()`: Delegates to reasoning engine
- `act()`: Delegates to action engine
- `_is_goal_achieved()`: Checks if goal is completed

### 2. Perception Engine (`perception.py`)

**Handles all environmental perception and signal discovery**

- **Purpose**: Discovers UI elements and monitors system state
- **Key Features**:
  - UI element scanning with position-based IDs
  - System state monitoring (battery, CPU, memory)
  - Context analysis (current app, focused elements)
  - Constraint identification (low battery, high resource usage)

**Key Classes**:

- `PerceptionEngine`: Main perception coordinator
- `UISignal`: Represents discovered UI elements
- `SystemState`: Current system information

**Critical Methods**:

- `discover_ui_signals()`: Scans for interactive UI elements
- `get_system_state()`: Monitors battery, CPU, memory
- `get_context()`: Analyzes current application context
- `_create_ui_signal()`: Generates position-based element IDs

**Element ID Generation**:

- Uses `AXIdentifier` when available
- Falls back to position-based IDs: `{role}_{x}_{y}` (e.g., `AXButton_533.0_310.0`)
- Ensures unique, findable element identifiers

### 3. Reasoning Engine (`reasoning.py`)

**Handles intelligent reasoning and plan generation using Gemini 2.0 Flash**

- **Purpose**: Analyzes situation and generates action plans
- **Key Features**:
  - Gemini 2.0 Flash integration
  - Comprehensive prompt engineering
  - JSON response parsing
  - Knowledge integration (domain knowledge, best practices)
  - Confidence scoring and alternative planning

**Key Classes**:

- `ReasoningEngine`: Main reasoning coordinator
- `ReasoningResult`: Structured reasoning output

**Critical Methods**:

- `analyze_situation()`: Main reasoning entry point
- `_build_reasoning_prompt()`: Comprehensive prompt engineering
- `_parse_gemini_response()`: Extracts JSON from Gemini responses
- `gather_knowledge()`: Integrates domain knowledge and best practices

**Prompt Engineering**:

- Explicitly instructs Gemini to use exact element IDs from perception
- Includes comprehensive context (UI elements, system state, knowledge)
- Requests structured JSON responses with plans, confidence, alternatives
- Emphasizes "USE THESE EXACT IDs" to prevent ID generation

### 4. Action Engine (`action.py`)

**Executes actions on UI elements using accessibility APIs**

- **Purpose**: Executes planned actions on discovered UI elements
- **Key Features**:
  - Position-based element finding with tolerance
  - Multiple action types (click, type, select, scroll, wait, key)
  - Action validation and error handling
  - Retry logic for failed actions

**Key Classes**:

- `ActionEngine`: Main action coordinator
- `ActionResult`: Structured action results

**Critical Methods**:

- `execute_action()`: Main action execution
- `_find_element()`: **CRITICAL** - Finds elements using multiple strategies
- `_execute_click()`, `_execute_type()`, etc.: Specific action implementations

**Element Finding Strategy** (CRITICAL):

1. **By Identifier**: `findAllR(AXIdentifier=target)` - Primary method
2. **By Title**: `findAllR(AXTitle=target)` - Fallback
3. **Position-based**: Parse `{role}_{x}_{y}` and find within 10-pixel tolerance
4. **Role + Title**: Search by role and title combination

**Fixed Critical Bug**:

- Changed from `findFirst()` to `findAllR()` for better compatibility
- `findFirst()` doesn't work reliably with `AXIdentifier`
- `findAllR()` works perfectly and returns list of matching elements

### 5. Memory System (`memory.py`)

**Manages experience storage, retrieval, and learning**

- **Purpose**: Stores and learns from agent experiences
- **Key Features**:
  - Multiple memory types (perception, reasoning, actions, episodes)
  - Importance scoring and relevance-based retrieval
  - Pattern recognition (success/failure patterns)
  - Learning from experience
  - Memory export/import capabilities

**Key Classes**:

- `MemorySystem`: Main memory coordinator
- `MemoryEntry`: Individual memory entries

**Critical Methods**:

- `store_perception()`, `store_reasoning()`, `store_actions()`: Store different memory types
- `retrieve_relevant_memories()`: Context-aware memory retrieval
- `get_patterns()`: Identify success/failure patterns
- `learn_from_experience()`: Extract insights from stored experiences

## Data Flow

```
1. PERCEIVE
   ├── Scan UI elements → Generate position-based IDs
   ├── Monitor system state → Battery, CPU, memory
   └── Analyze context → Current app, focused elements

2. REASON
   ├── Gather knowledge → Domain knowledge, best practices
   ├── Build prompt → Include exact element IDs, system state
   ├── Query Gemini → Generate structured plan
   └── Parse response → Extract plan, confidence, alternatives

3. ACT
   ├── Find elements → Use multiple finding strategies
   ├── Execute actions → Click, type, select, etc.
   └── Store results → Success/failure tracking

4. MEMORY
   ├── Store perception → UI elements, system state
   ├── Store reasoning → Plans, confidence, alternatives
   ├── Store actions → Results, errors, timestamps
   └── Learn patterns → Success/failure analysis
```

## Critical Design Decisions

### 1. Element ID Matching (CRITICAL)

- **Problem**: Gemini must use exact IDs from perception, not generate new ones
- **Solution**:
  - Perception generates robust position-based IDs when `AXIdentifier` missing
  - Prompt explicitly instructs "USE THESE EXACT IDs"
  - Action engine uses multiple finding strategies with tolerance

### 2. Element Finding (CRITICAL)

- **Problem**: `findFirst()` doesn't work reliably with `AXIdentifier`
- **Solution**: Use `findAllR()` which works perfectly
- **Implementation**: `findAllR(AXIdentifier=target)` returns list, take first element

### 3. Position-Based Matching

- **Problem**: Some elements lack `AXIdentifier` attributes
- **Solution**: Generate position-based IDs `{role}_{x}_{y}` with 10-pixel tolerance
- **Implementation**: Parse coordinates, find elements within tolerance

### 4. Prompt Engineering

- **Problem**: Gemini generates abstract IDs instead of using perceived ones
- **Solution**: Explicit instructions and comprehensive context
- **Implementation**: "IMPORTANT: You MUST use the exact element IDs provided above"

## Error Handling

### Perception Errors

- Graceful degradation when apps not found
- Timeout protection for UI scanning
- Element limit enforcement to prevent performance issues

### Reasoning Errors

- Gemini API error handling with fallbacks
- JSON parsing with text fallback
- Network error recovery

### Action Errors

- Element finding with multiple strategies
- Action validation before execution
- Retry logic for transient failures
- Comprehensive error reporting

### Memory Errors

- Safe memory operations with exception handling
- Memory limit enforcement
- Export/import error recovery

## Performance Optimizations

### UI Scanning

- Limit total elements scanned (50 max)
- Limit windows scanned (2 max)
- Limit elements per role (10 max)
- Timeout protection for deep recursion

### Memory Management

- Deque with maxlen limits
- Importance-based memory retention
- Efficient relevance scoring

### Action Execution

- Small delays between actions (0.5s)
- Element finding with early returns
- Action validation to prevent unnecessary execution

## Dependencies

### Core Dependencies

- `atomacos`: macOS accessibility APIs
- `psutil`: System monitoring
- `google-generativeai`: Gemini 2.0 Flash integration
- `python-dotenv`: Environment variable loading

### Optional Dependencies

- `requests`: Web search integration (future)
- `json`: Built-in JSON handling
- `time`: Built-in timing functions

## Configuration

### Environment Variables

- `GEMINI_API_KEY`: Required for Gemini integration
- Loaded from `.env` file using `python-dotenv`

### System Requirements

- macOS with accessibility APIs enabled
- Terminal/IDE with accessibility permissions
- Python 3.7+ with virtual environment

## Testing Strategy

### Unit Testing

- Test each component individually
- Mock external dependencies (Gemini, atomacos)
- Validate data structures and error handling

### Integration Testing

- Test full perceive-reason-act loop
- Test with different goals and applications
- Test error recovery and edge cases

### End-to-End Testing

- Test with real applications (System Settings, Calculator)
- Test with different system states (low battery, high CPU)
- Test learning and memory functionality

## Future Enhancements

### Planned Features

- Web search integration for external knowledge
- Advanced learning algorithms
- Multi-agent coordination
- Custom action types
- Enhanced error recovery

### Scalability Considerations

- Distributed memory systems
- Cloud-based reasoning
- Real-time collaboration
- Performance monitoring

## Security Considerations

### API Key Management

- Store `GEMINI_API_KEY` in `.env` file
- Never commit API keys to version control
- Use environment-specific configurations

### Accessibility Permissions

- Require explicit user permission for accessibility APIs
- Handle permission errors gracefully
- Provide clear setup instructions

### Data Privacy

- Memory export/import for data portability
- No external data transmission except to Gemini
- Local processing of all UI interactions

## Troubleshooting

### Common Issues

1. **Element not found**: Check element finding strategies, verify element exists
2. **Gemini errors**: Verify API key, check network connectivity
3. **Permission errors**: Grant accessibility permissions to terminal/IDE
4. **Performance issues**: Check element limits, optimize scanning

### Debug Tools

- `debug_gemini_prompt.py`: Inspect Gemini input/output
- `test_agent.py`: Run comprehensive tests
- Memory export for analysis
- Detailed logging throughout system

## Conclusion

This architecture represents a complete reimplementation of the agent system with all critical issues resolved. The modular design ensures maintainability, the robust error handling ensures reliability, and the intelligent reasoning ensures effectiveness. The system is now ready for production use with autonomous UI automation capabilities.
