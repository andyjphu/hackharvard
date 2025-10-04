# Browser Screenshot Analysis with Gemini AI

This module provides intelligent browser screenshot analysis using Google's Gemini AI to identify interactive elements and generate step-by-step instructions for completing tasks.

## Features

### 🖥️ Screenshot Capture
- Captures full-screen screenshots using the `mss` library
- Supports multiple monitor configurations
- Saves screenshots as PNG files for analysis

### 🤖 AI-Powered Analysis
- Uses Gemini 2.0 Flash for advanced image understanding
- Identifies interactive elements (buttons, forms, links, etc.)
- Provides detailed element descriptions with positions and characteristics
- Generates contextual analysis based on user tasks

### 📋 Smart Instructions
- Creates clear, step-by-step instructions for completing tasks
- Adapts instructions based on the type of task (search, login, form filling, etc.)
- Includes safety warnings and alternative methods

### ⚠️ Safety Features
- Identifies potentially sensitive areas (login forms, payment fields)
- Warns about destructive actions
- Suggests alternative approaches when needed

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Gemini API Key**
   Create a `.env` file in your project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. **Get Gemini API Key**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key to your `.env` file

## Usage

### Basic Usage

```python
from model.gemini import BrowserScreenshotAnalyzer

# Initialize the analyzer
analyzer = BrowserScreenshotAnalyzer()

# Run complete analysis workflow
analyzer.run_analysis()
```

### Advanced Usage

```python
from model.gemini import BrowserScreenshotAnalyzer

# Initialize with custom settings
analyzer = BrowserScreenshotAnalyzer()

# Capture screenshot
screenshot_path = analyzer.capture_screenshot()

# Analyze with specific task
analysis = analyzer.analyze_screenshot(screenshot_path, "Search for information about AI")

# Generate instructions
instructions = analyzer.generate_step_by_step_instructions(analysis, "Search for information about AI")

# Display results
analyzer.display_analysis_results(analysis)
analyzer.display_instructions(instructions)
```

### Command Line Usage

```bash
# Run the example script
python example_browser_analysis.py

# Run tests
python test_gemini_analysis.py
```

## API Reference

### BrowserScreenshotAnalyzer Class

#### Methods

**`__init__()`**
- Initializes the analyzer with Gemini API configuration
- Requires `GEMINI_API_KEY` environment variable

**`capture_screenshot(monitor: int = 1) -> str`**
- Captures screenshot of specified monitor
- Returns path to saved screenshot file
- Default monitor is 1 (primary monitor)

**`analyze_screenshot(image_path: str, user_task: str = "") -> Dict[str, Any]`**
- Analyzes screenshot using Gemini AI
- Returns structured analysis with elements, warnings, and alternatives
- Includes user task context for better analysis

**`generate_step_by_step_instructions(analysis: Dict[str, Any], user_task: str) -> List[str]`**
- Generates task-specific instructions based on analysis
- Adapts to different task types (search, login, forms, etc.)
- Includes safety reminders

**`run_analysis(user_task: str = None)`**
- Complete workflow: capture → analyze → display → instruct
- Prompts for user task if not provided
- Handles all error cases gracefully

## Analysis Output Format

The analyzer returns structured JSON with the following format:

```json
{
    "screen_description": "Description of what's visible on screen",
    "interactive_elements": [
        {
            "type": "button|input|link|select|textarea",
            "position": "top-left|center|bottom-right|etc",
            "text": "Visible text or label",
            "purpose": "Intended function",
            "characteristics": "Visual description"
        }
    ],
    "safety_warnings": [
        "Warning about sensitive information or risks"
    ],
    "alternative_methods": [
        "Alternative approaches if direct interaction fails"
    ]
}
```

## Supported Task Types

The analyzer automatically adapts instructions based on task keywords:

- **Search Tasks**: "search for", "find information about"
- **Login Tasks**: "login", "sign in", "authenticate"
- **Form Tasks**: "fill out", "complete form", "submit"
- **Navigation Tasks**: "navigate to", "go to", "visit"
- **General Tasks**: Fallback to general interaction instructions

## Safety Features

### Automatic Warnings
- Identifies login/authentication areas
- Flags payment/transaction elements
- Warns about destructive actions
- Highlights sensitive information fields

### Alternative Methods
- Suggests voice search when available
- Recommends password managers for login
- Proposes different navigation paths
- Offers fallback interaction methods

## Error Handling

The analyzer includes comprehensive error handling:

- **API Errors**: Graceful fallback with error messages
- **Screenshot Failures**: Clear error reporting and troubleshooting
- **JSON Parsing**: Fallback to raw response display
- **Missing Dependencies**: Helpful setup instructions

## Examples

### Example 1: Search Task
```python
analyzer = BrowserScreenshotAnalyzer()
analyzer.run_analysis("Search for information about machine learning")
```

**Output:**
```
📋 STEP-BY-STEP INSTRUCTIONS
1. Locate the search bar (center)
2. Click on the search bar to activate it
3. Type your search query
4. Press Enter or click the search button
```

### Example 2: Login Task
```python
analyzer.run_analysis("Login to my account")
```

**Output:**
```
📋 STEP-BY-STEP INSTRUCTIONS
1. Click the login/sign-in button (top-right)
2. Enter your username/email in the username field
3. Enter your password in the password field
4. Click the submit/login button

⚠️ SAFETY REMINDERS:
   • Ensure you're on the correct website before entering credentials
   • Check for HTTPS in the URL
```

## Troubleshooting

### Common Issues

**1. "GEMINI_API_KEY not found"**
- Ensure `.env` file exists in project root
- Verify API key is correctly formatted
- Check for typos in environment variable name

**2. "Screenshot capture failed"**
- Run as administrator (Windows) or with appropriate permissions
- Ensure at least one monitor is connected
- Check if `mss` library is properly installed

**3. "Analysis failed"**
- Verify internet connection for Gemini API calls
- Check API key validity and quota
- Ensure screenshot file exists and is readable

**4. "No interactive elements found"**
- Try capturing a different part of the screen
- Ensure browser window is visible and not minimized
- Check if the page has fully loaded

### Performance Tips

- **Screenshot Size**: Larger screenshots take longer to analyze
- **API Quota**: Monitor your Gemini API usage to avoid rate limits
- **Caching**: Consider caching analysis results for repeated tasks
- **Batch Processing**: Analyze multiple screenshots in sequence

## Integration with Agent System

This module integrates seamlessly with the existing agent system:

```python
# In your agent workflow
from model.gemini import BrowserScreenshotAnalyzer

class WebAgent:
    def __init__(self):
        self.analyzer = BrowserScreenshotAnalyzer()
    
    def analyze_webpage(self, task):
        analysis = self.analyzer.run_analysis(task)
        return analysis
```

## Future Enhancements

- **Multi-language Support**: Instructions in different languages
- **Voice Integration**: Audio instructions and feedback
- **Automation Integration**: Direct action execution
- **Learning System**: Improve instructions based on user feedback
- **Advanced Element Detection**: More precise element positioning

## Contributing

To contribute to this module:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This module is part of the autonomous agent system and follows the same licensing terms.
