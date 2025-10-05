# Intelligent UI Automation System - Usage Guide

## 🎯 Overview

The Intelligent UI Automation System combines UI element discovery, web search capabilities, and Gemini 2.5 Flash-Lite for intelligent automation planning. It presents all available signals to an LLM, allowing it to construct optimal automation plans based on current state, user goals, and external knowledge.

## 🚀 Quick Start

### 1. Set up your Gemini API Key

```bash
export GEMINI_API_KEY="your_actual_gemini_api_key_here"
```

### 2. Run the system

```bash
# Basic usage
python intelligent_automation.py "optimize battery life" "System Settings"

# Test different goals
python intelligent_automation.py "enhance security" "System Settings"
python intelligent_automation.py "improve accessibility" "System Settings"
```

## 🏗️ Architecture Components

### 1. Signal Discovery Engine

- **Discovers UI elements**: Buttons, toggles, dropdowns, text fields
- **System state monitoring**: Battery level, power source, memory usage
- **Context analysis**: Current app, focused elements, constraints

### 2. Knowledge Integration Engine

- **Web search integration**: Gathers relevant information about the task
- **Domain knowledge base**: Pre-built knowledge about common automation tasks
- **Best practices engine**: Provides recommendations based on system behavior

### 3. LLM Decision Engine (Gemini 2.5 Flash-Lite)

- **Goal parsing**: Understands user intent and objectives
- **Plan generation**: Creates step-by-step automation sequences
- **Risk assessment**: Evaluates potential issues and side effects
- **Optimization**: Finds most efficient paths

## 📊 Example Output

```
🎯 Intelligent Automation System
Goal: optimize battery life
Target App: System Settings
============================================================
🔍 Discovering UI signals...
✅ Discovered 34 interactive elements
🧠 Gathering contextual knowledge...
🤖 Generating automation plan...

📊 DISCOVERED SIGNALS:
   Interactive Elements: 34
   System State: SystemState(battery_level=39, power_source='battery', network_status='connected', time='07:51', memory_usage=76.5, cpu_usage=22.7)
   Constraints: []

🧠 KNOWLEDGE INTEGRATION:
   Web Search Results: 4
   Domain Knowledge: 3
   Best Practices: 4
   Recommendations: 0

🤖 LLM GENERATED PLAN:
   Steps: 5
   Confidence: 0.9
   Reasoning: Based on battery level and available power settings

📋 AUTOMATION STEPS:
   1. click on low_power_mode
   2. select "Only on Battery" from dropdown
   3. adjust screen brightness slider
   4. disable background app refresh
   5. verify settings applied
```

## 🔧 Available Commands

### Main System

```bash
# Run intelligent automation
python intelligent_automation.py "goal" "target_app"

# Test system without API key
python test_intelligent_automation.py
```

### Specialized Tools

```bash
# Low Power Mode automation
python low_power_automation.py --on
python low_power_automation.py --off
python low_power_automation.py --status

# UI element discovery
python ui_dumper_main.py "System Settings"
python ui_dumper_main.py Calculator
python ui_dumper_main.py --chrome
```

## 🎯 Use Cases

### 1. Battery Optimization

**Goal**: "optimize battery life"
**System discovers**:

- Low Power Mode toggle
- Screen brightness controls
- Background app settings
- Battery usage statistics

**LLM generates plan**:

- Enable Low Power Mode (Only on Battery)
- Reduce screen brightness
- Disable unnecessary background apps
- Configure power management

### 2. Security Enhancement

**Goal**: "enhance security"
**System discovers**:

- FileVault encryption settings
- Firewall controls
- Touch ID configuration
- Password requirements

**LLM generates plan**:

- Enable FileVault if not enabled
- Configure strong password requirements
- Enable two-factor authentication
- Review firewall settings

### 3. Accessibility Setup

**Goal**: "improve accessibility"
**System discovers**:

- VoiceOver settings
- Display contrast options
- Text size controls
- Zoom functionality

**LLM generates plan**:

- Enable VoiceOver with optimal settings
- Increase text size
- Enable high contrast mode
- Configure zoom shortcuts

## 🧠 How the LLM Makes Decisions

### Input to Gemini

```
GOAL: optimize battery life

AVAILABLE UI ELEMENTS:
- ID: low_power_mode
  Type: AXPopUpButton
  Position: (1343, 86)
  Current Value: Never
  Available Options: ['Never', 'Always', 'Only on Battery']
  Actions: ['click']

SYSTEM STATE:
Battery Level: 39%
Power Source: battery
Network: connected
Time: 07:51
Memory Usage: 76.5%
CPU Usage: 22.7%

EXTERNAL KNOWLEDGE:
battery_optimization: {
  "low_power_mode": "Reduces background activity and performance",
  "screen_brightness": "Major battery drain factor",
  "background_apps": "Can significantly impact battery life"
}
```

### LLM Response

```json
{
  "plan": [
    {
      "action": "click",
      "target": "low_power_mode",
      "reason": "Enable Low Power Mode for battery optimization"
    },
    {
      "action": "select",
      "target": "Only on Battery",
      "reason": "Optimal setting for battery life"
    }
  ],
  "reasoning": "Battery is at 39% and on battery power. Low Power Mode will significantly extend battery life.",
  "alternatives": ["Manual configuration", "Gradual implementation"],
  "risks": ["May require user confirmation", "Could affect system performance"],
  "confidence": 0.9
}
```

## 🔍 Signal Discovery Details

### UI Element Types Discovered

- **Buttons**: Clickable elements with actions
- **Pop-up Buttons**: Dropdown menus (like Low Power Mode)
- **Checkboxes**: Toggle switches
- **Text Fields**: Input areas
- **Sliders**: Value controls
- **Menu Items**: Dropdown options

### System State Monitored

- **Battery Level**: Current charge percentage
- **Power Source**: Battery or AC power
- **Network Status**: Connected/disconnected
- **Memory Usage**: RAM utilization
- **CPU Usage**: Processor load
- **Time**: Current system time

### Constraints Identified

- **Low Battery**: < 20% charge
- **High Memory Usage**: > 80% RAM
- **High CPU Usage**: > 80% processor
- **Network Issues**: Connectivity problems

## 🚨 Error Handling

### Common Issues

1. **API Key Invalid**: Set `GEMINI_API_KEY` environment variable
2. **App Not Found**: Ensure target application is open
3. **No UI Elements**: Check accessibility permissions
4. **Network Issues**: Verify internet connection

### Fallback Behavior

- **Mock Planning**: Uses rule-based planning when Gemini unavailable
- **Graceful Degradation**: Continues with partial information
- **Error Recovery**: Provides alternative approaches

## 📁 File Structure

```
/Users/andyphu/hackharvard/
├── ARCHITECTURE.md              # System architecture documentation
├── USAGE_GUIDE.md              # This usage guide
├── intelligent_automation.py   # Main system implementation
├── test_intelligent_automation.py  # Test script
├── ui_dumper_main.py           # UI element discovery tool
├── low_power_automation.py     # Specialized Low Power Mode automation
├── calculator_debug.py         # Calculator automation example
└── automation_result.json      # Generated automation plans
```

## 🔮 Future Enhancements

### Planned Features

- **Real-time execution**: Execute generated plans automatically
- **Learning system**: Improve from user feedback
- **Cross-platform support**: Windows and Linux compatibility
- **Voice commands**: Natural language interface
- **Workflow orchestration**: Complex multi-step automations

### Integration Possibilities

- **Calendar integration**: Schedule automations
- **Cloud sync**: Share automation across devices
- **API access**: Third-party automation integration
- **Predictive automation**: Anticipate user needs

## 🎉 Success Metrics

The system successfully:

- ✅ **Discovers 34+ UI elements** in System Settings
- ✅ **Monitors system state** in real-time
- ✅ **Integrates external knowledge** for context
- ✅ **Generates intelligent plans** with Gemini 2.5 Flash-Lite
- ✅ **Handles errors gracefully** with fallback mechanisms
- ✅ **Provides detailed reasoning** for automation decisions

This architecture provides a foundation for intelligent, context-aware UI automation that can adapt to user needs and system conditions while maintaining security and privacy.
