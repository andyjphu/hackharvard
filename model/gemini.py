import mss
import webbrowser
import time
import base64
import json
import os
import cv2
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BrowserScreenshotAnalyzer:
    """
    Analyzes browser screenshots using Gemini API to identify interactive elements
    and provide step-by-step instructions for completing tasks.
    """

    def __init__(self):
        """Initialize the analyzer with Gemini API configuration."""
        self.api_key = "your_api_key_here"

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self.screenshot_path = "browser_screenshot.png"
        self.annotated_screenshot_path = "browser_screenshot_annotated.png"

    def capture_screenshot(self, target_app: str = None) -> str:
        """
        Capture a screenshot of the focused window or specific app.
        Always attempts to capture only the focused window, never falls back to full screen.

        Args:
            target_app: Target application name for focused window capture

        Returns:
            Path to the saved screenshot
        """
        try:
            # Always try to capture focused window first
            if target_app:
                # Try multiple approaches to get the app and window
                app = None
                front_window = None

                # Approach 1: Direct app lookup
                try:
                    import atomacos as atomac

                    app = atomac.getAppRefByLocalizedName(target_app)
                    print(f"   🎯 Found app: {target_app}")
                except Exception as e:
                    print(f"   ⚠️  Direct app lookup failed: {e}")

                # Approach 2: Try with normalized app name
                if not app:
                    try:
                        normalized_names = {
                            "iTerm": "iTerm2",
                            "iTerm2": "iTerm2",
                            "Terminal": "Terminal",
                            "Google Chrome": "Google Chrome",
                            "Chrome": "Google Chrome",
                            "Safari": "Safari",
                            "Calculator": "Calculator",
                            "System Settings": "System Settings",
                            "System Preferences": "System Settings",
                        }
                        normalized_name = normalized_names.get(target_app, target_app)
                        if normalized_name != target_app:
                            app = atomac.getAppRefByLocalizedName(normalized_name)
                            print(
                                f"   🎯 Found app with normalized name: {normalized_name}"
                            )
                    except Exception as e:
                        print(f"   ⚠️  Normalized app lookup failed: {e}")

                # Approach 3: Try to get frontmost app if target app not found
                if not app:
                    try:
                        frontmost_app = atomac.getFrontmostApp()
                        if frontmost_app:
                            app_name = getattr(frontmost_app, "AXTitle", "")
                            if app_name:
                                print(f"   🎯 Using frontmost app: {app_name}")
                                app = frontmost_app
                    except Exception as e:
                        print(f"   ⚠️  Frontmost app lookup failed: {e}")

                if app:
                    # Get the frontmost window of the app
                    try:
                        windows = app.windows()
                        if windows:
                            # Find the frontmost window (usually the first one)
                            front_window = windows[0]
                            print(
                                f"   📊 Found {len(windows)} windows, using frontmost"
                            )
                        else:
                            print(f"   ⚠️  No windows found for app: {target_app}")
                    except Exception as e:
                        print(f"   ⚠️  Error getting windows: {e}")

                if front_window:
                    try:
                        # Get window bounds
                        bounds = front_window.AXFrame
                        if bounds:
                            # Capture specific window area
                            with mss.mss() as sct:
                                # Convert window bounds to monitor coordinates
                                monitor = {
                                    "top": int(bounds.y),
                                    "left": int(bounds.x),
                                    "width": int(bounds.width),
                                    "height": int(bounds.height),
                                }

                                screenshot = sct.grab(monitor)
                                mss.tools.to_png(
                                    screenshot.rgb,
                                    screenshot.size,
                                    output=self.screenshot_path,
                                )

                                print(
                                    f"✅ Focused window screenshot captured: {target_app} ({monitor['width']}x{monitor['height']})"
                                )
                                return self.screenshot_path
                        else:
                            print(f"   ⚠️  No window bounds available")
                    except Exception as e:
                        print(f"   ⚠️  Window bounds capture failed: {e}")
                else:
                    print(f"   ⚠️  No frontmost window found for app: {target_app}")

            # If we get here, we couldn't capture the focused window
            print(f"   ❌ Failed to capture focused window for: {target_app}")
            print(
                f"   💡 This is intentional - we only capture focused windows, not full screen"
            )
            return None

        except Exception as e:
            print(f"❌ Error capturing screenshot: {e}")
            return None

    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64 for Gemini API."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            print(f"❌ Error encoding image: {e}")
            return None

    def analyze_screenshot(
        self, image_path: str, user_task: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze screenshot using Gemini API to identify interactive elements.

        Args:
            image_path: Path to the screenshot
            user_task: Optional user task description

        Returns:
            Dictionary containing analysis results
        """
        try:
            # Encode image
            image_base64 = self.encode_image_to_base64(image_path)
            if not image_base64:
                return {"error": "Failed to encode image"}

            # Create prompt for Gemini
            prompt = f"""
            Analyze this browser screenshot and identify all interactive elements. 
            
            User Task: {user_task if user_task else "General browser analysis"}
            
            Please provide a detailed analysis including:
            
            1. SCREEN DESCRIPTION: What you see on the screen (website, page type, main content)
            
            2. INTERACTIVE ELEMENTS: Identify and locate all interactive elements with their approximate positions:
               - Search bars/input fields
               - Buttons (submit, login, navigation, etc.)
               - Links
               - Dropdown menus
               - Checkboxes/radio buttons
               - Forms
               - Navigation elements
               - Any other clickable elements
            
            3. ELEMENT DETAILS: For each element, provide:
               - Type (button, input, link, etc.)
               - Approximate position (top-left, center, bottom-right, etc.)
               - Visible text or labels
               - Likely purpose/function
               - Color or visual characteristics
            
            4. SAFETY WARNINGS: Any potential risks or things to be careful about:
               - Sensitive information fields
               - Destructive actions
               - Payment/transaction elements
               - Login/authentication areas
               - Pop-ups or overlays
            
            5. ALTERNATIVE METHODS: Suggest alternative approaches if direct interaction isn't possible
            
            Format your response as JSON with the following structure:
            {{
                "screen_description": "Description of what's visible",
                "interactive_elements": [
                    {{
                        "type": "button",
                        "position": "top-right",
                        "text": "Login",
                        "purpose": "User authentication",
                        "characteristics": "Blue button with white text"
                    }}
                ],
                "safety_warnings": [
                    "Warning about sensitive information"
                ],
                "alternative_methods": [
                    "Alternative approach description"
                ]
            }}
            """

            # Prepare image for Gemini
            image_data = {"mime_type": "image/png", "data": image_base64}

            # Generate response
            response = self.model.generate_content([prompt, image_data])

            # Parse JSON response
            try:
                # Extract JSON from response text
                import re

                json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    result = json.loads(json_str)
                    return result
                else:
                    # Fallback if JSON parsing fails
                    return {
                        "screen_description": "Analysis completed but JSON parsing failed",
                        "raw_response": response.text,
                        "interactive_elements": [],
                        "safety_warnings": ["Could not parse structured response"],
                        "alternative_methods": [],
                    }
            except json.JSONDecodeError as e:
                return {
                    "error": f"JSON parsing error: {e}",
                    "raw_response": response.text,
                }

        except Exception as e:
            return {"error": f"Analysis failed: {e}"}

    def get_user_task_input(self) -> str:
        """Get user task description through terminal input."""
        print("\n" + "=" * 60)
        print("🎯 TASK INPUT")
        print("=" * 60)
        print("What would you like to accomplish on this webpage?")
        print("Examples:")
        print("- 'Search for information about...'")
        print("- 'Fill out a form to...'")
        print("- 'Navigate to a specific section'")
        print("- 'Complete a purchase'")
        print("- 'Login to my account'")
        print()

        task = input("Enter your task: ").strip()
        return task if task else "General webpage analysis"

    def _draw_border(self, text: str, border_char: str = "═", width: int = 60) -> str:
        """Draw a visual border around text."""
        border_line = border_char * width
        return f"\n{border_line}\n{text}\n{border_line}"

    def _highlight_task_relevant(
        self, elements: List[Dict], user_task: str
    ) -> List[Dict]:
        """Highlight elements that are most relevant to the user's task and add coordinates."""
        if not user_task:
            return elements

        task_lower = user_task.lower()
        relevant_elements = []
        other_elements = []

        for element in elements:
            element_text = element.get("text", "").lower()
            element_type = element.get("type", "").lower()
            element_purpose = element.get("purpose", "").lower()
            element_position = element.get("position", "center")

            # Check if element is relevant to task
            is_relevant = False

            if "search" in task_lower and element_type in ["input", "search"]:
                is_relevant = True
            elif "login" in task_lower and (
                "login" in element_text
                or "sign" in element_text
                or "auth" in element_purpose
            ):
                is_relevant = True
            elif "form" in task_lower and element_type in [
                "input",
                "textarea",
                "select",
            ]:
                is_relevant = True
            elif "button" in task_lower and element_type == "button":
                is_relevant = True
            elif "submit" in task_lower and (
                "submit" in element_text or "submit" in element_purpose
            ):
                is_relevant = True
            elif "navigate" in task_lower and element_type in ["link", "button"]:
                is_relevant = True
            elif "click" in task_lower and element_type in ["button", "link"]:
                is_relevant = True

            if is_relevant:
                element["task_relevant"] = True
                relevant_elements.append(element)
            else:
                element["task_relevant"] = False
                other_elements.append(element)

        # Return relevant elements first, then others
        return relevant_elements + other_elements

    def display_analysis_results(self, analysis: Dict[str, Any], user_task: str = ""):
        """Display the analysis results in a formatted way with task-relevant highlighting."""
        print(self._draw_border("📊 SCREENSHOT ANALYSIS RESULTS", "═", 60))

        if "error" in analysis:
            print(f"❌ Error: {analysis['error']}")
            if "raw_response" in analysis:
                print(f"Raw response: {analysis['raw_response']}")
            return

        # Screen Description with border
        screen_desc = analysis.get("screen_description", "No description available")
        print(self._draw_border(f"🖥️  SCREEN DESCRIPTION", "─", 50))
        print(f"   {screen_desc}")

        # Interactive Elements with task relevance highlighting
        elements = analysis.get("interactive_elements", [])
        if elements:
            # Sort elements by task relevance
            sorted_elements = self._highlight_task_relevant(elements, user_task)

            print(
                self._draw_border(
                    f"🔘 INTERACTIVE ELEMENTS FOUND ({len(elements)})", "─", 50
                )
            )

            # Display task-relevant elements first with special highlighting
            relevant_elements = [
                e for e in sorted_elements if e.get("task_relevant", False)
            ]
            other_elements = [
                e for e in sorted_elements if not e.get("task_relevant", False)
            ]

            if relevant_elements:
                print(f"\n🎯 TASK-RELEVANT ELEMENTS ({len(relevant_elements)}):")
                print("┌" + "─" * 78 + "┐")
                for i, element in enumerate(relevant_elements, 1):

                    print(
                        f"│ {i}. {element.get('type', 'Unknown').upper():<12} │ {element.get('text', 'No text')[:35]:<35} │"
                    )
                    print(f"│    Position: {element.get('position', 'Unknown'):<43} │")
                    print(
                        f"│    Purpose:  {element.get('purpose', 'Unknown')[:43]:<43} │"
                    )
                    print(
                        f"│    Visual:   {element.get('characteristics', 'None')[:43]:<43} │"
                    )

                    if i < len(relevant_elements):
                        print("├" + "─" * 78 + "┤")
                print("└" + "─" * 78 + "┘")

            if other_elements:
                print(f"\n📋 OTHER INTERACTIVE ELEMENTS ({len(other_elements)}):")
                for i, element in enumerate(other_elements, 1):
                    print(f"   {i}. {element.get('type', 'Unknown').upper()}")
                    print(f"      Position: {element.get('position', 'Unknown')}")
                    print(f"      Text: {element.get('text', 'No text')}")
                    print(f"      Purpose: {element.get('purpose', 'Unknown')}")
                    print(
                        f"      Characteristics: {element.get('characteristics', 'None')}"
                    )
                    print()
        else:
            print(self._draw_border("🔘 NO INTERACTIVE ELEMENTS IDENTIFIED", "─", 50))

        # Safety Warnings with enhanced border
        warnings = analysis.get("safety_warnings", [])
        if warnings:
            print(self._draw_border("⚠️  SAFETY WARNINGS", "⚠", 50))
            print("┌" + "─" * 58 + "┐")
            for warning in warnings:
                # Wrap long warnings
                wrapped_warning = [
                    warning[i : i + 56] for i in range(0, len(warning), 56)
                ]
                for line in wrapped_warning:
                    print(f"│ {line:<56} │")
            print("└" + "─" * 58 + "┘")
        else:
            print(self._draw_border("✅ NO SPECIFIC SAFETY WARNINGS", "─", 50))

        # Alternative Methods with border
        alternatives = analysis.get("alternative_methods", [])
        if alternatives:
            print(self._draw_border("🔄 ALTERNATIVE METHODS", "─", 50))
            print("┌" + "─" * 58 + "┐")
            for alt in alternatives:
                # Wrap long alternatives
                wrapped_alt = [alt[i : i + 56] for i in range(0, len(alt), 56)]
                for line in wrapped_alt:
                    print(f"│ {line:<56} │")
            print("└" + "─" * 58 + "┘")
        else:
            print(self._draw_border("💡 NO ALTERNATIVE METHODS SUGGESTED", "─", 50))

    def generate_step_by_step_instructions(
        self, analysis: Dict[str, Any], user_task: str
    ) -> List[str]:
        """Generate step-by-step instructions based on analysis and user task."""
        print(self._draw_border("📋 STEP-BY-STEP INSTRUCTIONS", "═", 60))

        elements = analysis.get("interactive_elements", [])
        instructions = []

        if not elements:
            instructions.append(
                "No interactive elements found to provide specific instructions."
            )
            return instructions

        # Generate instructions based on task and available elements
        task_lower = user_task.lower()

        if "search" in task_lower:
            search_elements = [
                e for e in elements if e.get("type") in ["input", "search"]
            ]
            if search_elements:
                element = search_elements[0]
                coords = element.get("coordinates", {})
                click_x = coords.get("click_x", 0)
                click_y = coords.get("click_y", 0)
                instructions.append(
                    f"1. Locate the search bar at position ({click_x}, {click_y})"
                )
                instructions.append(
                    f"2. Click at coordinates ({click_x}, {click_y}) to activate the search bar"
                )
                instructions.append("3. Type your search query")
                instructions.append("4. Press Enter or click the search button")
            else:
                instructions.append(
                    "1. No search bar found - look for a search icon or menu option"
                )

        elif "login" in task_lower or "sign in" in task_lower:
            login_elements = [
                e
                for e in elements
                if "login" in e.get("text", "").lower()
                or "sign" in e.get("text", "").lower()
            ]
            if login_elements:
                element = login_elements[0]
                coords = element.get("coordinates", {})
                click_x = coords.get("click_x", 0)
                click_y = coords.get("click_y", 0)
                instructions.append(
                    f"1. Click the login/sign-in button at coordinates ({click_x}, {click_y})"
                )
                instructions.append(
                    "2. Enter your username/email in the username field"
                )
                instructions.append("3. Enter your password in the password field")
                instructions.append("4. Click the submit/login button")
            else:
                instructions.append("1. Look for a login or account section")
                instructions.append("2. Find username/email and password fields")
                instructions.append("3. Enter your credentials and submit")

        elif "form" in task_lower or "fill" in task_lower:
            form_elements = [
                e for e in elements if e.get("type") in ["input", "textarea", "select"]
            ]
            if form_elements:
                instructions.append("1. Locate the form fields on the page")
                for i, element in enumerate(form_elements[:5], 2):  # Limit to 5 fields
                    coords = element.get("coordinates", {})
                    click_x = coords.get("click_x", 0)
                    click_y = coords.get("click_y", 0)
                    instructions.append(
                        f"{i}. Click at ({click_x}, {click_y}) and fill in the {element.get('text', 'form field')}"
                    )
                instructions.append(
                    f"{len(form_elements) + 2}. Review all information before submitting"
                )
                instructions.append(
                    f"{len(form_elements) + 3}. Click the submit button"
                )
            else:
                instructions.append("1. Look for input fields and forms on the page")
                instructions.append("2. Fill in the required information")
                instructions.append("3. Submit the form")

        else:
            # General instructions with coordinates
            relevant_elements = [e for e in elements if e.get("task_relevant", False)]
            if relevant_elements:
                element = relevant_elements[0]
                coords = element.get("coordinates", {})
                click_x = coords.get("click_x", 0)
                click_y = coords.get("click_y", 0)
                instructions.append(
                    f"1. Click on the {element.get('type', 'element')} at coordinates ({click_x}, {click_y})"
                )
                instructions.append(
                    "2. Follow any prompts or fill in required information"
                )
                instructions.append(
                    "3. Complete the action by clicking submit/confirm buttons"
                )
            else:
                instructions.append(
                    "1. Review the available interactive elements on the page"
                )
                instructions.append("2. Click on the element that matches your goal")
                instructions.append(
                    "3. Follow any prompts or fill in required information"
                )
                instructions.append(
                    "4. Complete the action by clicking submit/confirm buttons"
                )

        # Add safety reminders
        if analysis.get("safety_warnings"):
            instructions.append("\n⚠️  SAFETY REMINDERS:")
            for warning in analysis.get("safety_warnings", []):
                instructions.append(f"   • {warning}")

        return instructions

    def display_instructions(self, instructions: List[str]):
        """Display the generated instructions with enhanced formatting."""
        if not instructions:
            print("No instructions available.")
            return

        # Separate main instructions from safety reminders
        main_instructions = []
        safety_reminders = []

        for instruction in instructions:
            if instruction.startswith("⚠️") or instruction.startswith("   •"):
                safety_reminders.append(instruction)
            else:
                main_instructions.append(instruction)

        # Display main instructions with border
        if main_instructions:
            print("┌" + "─" * 58 + "┐")
            for i, instruction in enumerate(main_instructions, 1):
                # Wrap long instructions
                wrapped_instruction = [
                    instruction[i : i + 56] for i in range(0, len(instruction), 56)
                ]
                for j, line in enumerate(wrapped_instruction):
                    if j == 0:
                        print(f"│ {line:<56} │")
                    else:
                        print(f"│   {line:<54} │")
                if i < len(main_instructions):
                    print("├" + "─" * 58 + "┤")
            print("└" + "─" * 58 + "┘")

        # Display safety reminders with special border
        if safety_reminders:
            print(self._draw_border("⚠️  SAFETY REMINDERS", "⚠", 50))
            print("┌" + "─" * 58 + "┐")
            for reminder in safety_reminders:
                # Wrap long reminders
                wrapped_reminder = [
                    reminder[i : i + 56] for i in range(0, len(reminder), 56)
                ]
                for line in wrapped_reminder:
                    print(f"│ {line:<56} │")
            print("└" + "─" * 58 + "┘")

    def run_analysis(self, user_task: str = None):
        """Run the complete screenshot analysis workflow."""
        print(self._draw_border("🚀 STARTING BROWSER SCREENSHOT ANALYSIS", "═", 60))

        # Get user task if not provided
        if not user_task:
            user_task = self.get_user_task_input()

        # Display current task with border
        print(self._draw_border(f"🎯 CURRENT TASK: {user_task}", "─", 50))

        # Capture screenshot
        print("\n📸 Capturing screenshot...")
        screenshot_path = self.capture_screenshot()
        if not screenshot_path:
            print("❌ Failed to capture screenshot. Exiting.")
            return

        # Analyze screenshot
        print("\n🤖 Analyzing screenshot with Gemini AI...")
        analysis = self.analyze_screenshot(screenshot_path, user_task)

        # Display results
        self.display_analysis_results(analysis, user_task)

        # Draw borders around elements in the screenshot
        elements = analysis.get("interactive_elements", [])
        if elements:
            print("\n🎨 Drawing borders around interactive elements...")

        # Generate and display instructions
        instructions = self.generate_step_by_step_instructions(analysis, user_task)
        self.display_instructions(instructions)

        print(self._draw_border("✅ ANALYSIS COMPLETE!", "═", 60))


def main():
    """Main function to run the browser screenshot analyzer."""
    try:
        analyzer = BrowserScreenshotAnalyzer()
        analyzer.run_analysis()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have:")
        print("1. GEMINI_API_KEY set in your .env file")
        print("2. Required dependencies installed (pip install -r requirements.txt)")
        print("3. A browser window open to analyze")


if __name__ == "__main__":
    main()
