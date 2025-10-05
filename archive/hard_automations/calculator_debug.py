#!/usr/bin/env python3
"""
Calculator Debug Dumper - Deep dive into Calculator buttons for LLM automation
"""

import sys
import time
import atomacos as atomac


class CalculatorDebugger:
    def __init__(self):
        pass

    def debug_calculator_buttons(self):
        """Get detailed information about every Calculator button."""
        print("🧮 Calculator Button Debugger")
        print("=" * 60)

        try:
            # Get Calculator app
            app = atomac.getAppRefByLocalizedName("Calculator")
            if not app:
                print("❌ Calculator not found. Please open Calculator first.")
                return False

            print("✅ Found Calculator application")

            # Activate and wait
            app.activate()
            time.sleep(1)

            # Get windows
            windows = [
                w for w in app.windows() if getattr(w, "AXRole", None) == "AXWindow"
            ]

            if not windows:
                print("❌ No Calculator windows found")
                return False

            window = windows[0]
            print(
                f"✅ Found Calculator window: {getattr(window, 'AXTitle', 'Untitled')}"
            )

            # Get all buttons with detailed information
            buttons = window.findAllR(AXRole="AXButton") or []
            print(f"\n🔘 Found {len(buttons)} buttons:")

            for i, button in enumerate(buttons):
                print(f"\n--- BUTTON {i+1} ---")

                # Get all possible attributes
                attrs = [
                    "AXRole",
                    "AXTitle",
                    "AXDescription",
                    "AXValue",
                    "AXHelp",
                    "AXIdentifier",
                    "AXPosition",
                    "AXSize",
                    "AXEnabled",
                    "AXFocused",
                    "AXParent",
                    "AXChildren",
                    "AXSubrole",
                    "AXRoleDescription",
                ]

                button_info = {}
                for attr in attrs:
                    try:
                        value = getattr(button, attr, None)
                        if value is not None:
                            button_info[attr] = value
                    except:
                        pass

                # Print key information
                print(f"  Position: {button_info.get('AXPosition', 'Unknown')}")
                print(f"  Size: {button_info.get('AXSize', 'Unknown')}")
                print(f"  Title: '{button_info.get('AXTitle', '')}'")
                print(f"  Description: '{button_info.get('AXDescription', '')}'")
                print(f"  Value: '{button_info.get('AXValue', '')}'")
                print(f"  Help: '{button_info.get('AXHelp', '')}'")
                print(f"  Identifier: '{button_info.get('AXIdentifier', '')}'")
                print(f"  Enabled: {button_info.get('AXEnabled', 'Unknown')}")
                print(f"  Focused: {button_info.get('AXFocused', 'Unknown')}")

                # Try to get parent information
                try:
                    parent = getattr(button, "AXParent", None)
                    if parent:
                        parent_role = getattr(parent, "AXRole", "Unknown")
                        print(f"  Parent: {parent_role}")
                except:
                    pass

                # Try to get children
                try:
                    children = getattr(button, "AXChildren", None) or []
                    if children:
                        print(f"  Children: {len(children)} found")
                except:
                    pass

            # Try to find the display/input area
            print(f"\n📱 Display/Input Area:")
            scroll_areas = window.findAllR(AXRole="AXScrollArea") or []
            for i, area in enumerate(scroll_areas):
                print(f"  Scroll Area {i+1}:")
                print(f"    Title: '{getattr(area, 'AXTitle', '')}'")
                print(f"    Description: '{getattr(area, 'AXDescription', '')}'")
                print(f"    Value: '{getattr(area, 'AXValue', '')}'")
                print(f"    Position: {getattr(area, 'AXPosition', 'Unknown')}")
                print(f"    Size: {getattr(area, 'AXSize', 'Unknown')}")

            # Try to find static text (display)
            print(f"\n📄 Display Text:")
            static_texts = window.findAllR(AXRole="AXStaticText") or []
            for i, text in enumerate(static_texts):
                print(f"  Static Text {i+1}:")
                print(f"    Title: '{getattr(text, 'AXTitle', '')}'")
                print(f"    Value: '{getattr(text, 'AXValue', '')}'")
                print(f"    Position: {getattr(text, 'AXPosition', 'Unknown')}")
                print(f"    Size: {getattr(text, 'AXSize', 'Unknown')}")

            # Try to find any elements with meaningful content
            print(f"\n🔍 All Elements with Content:")
            all_elements = []
            self._collect_all_elements(window, all_elements)

            content_elements = []
            for el in all_elements:
                title = getattr(el, "AXTitle", None) or ""
                desc = getattr(el, "AXDescription", None) or ""
                value = getattr(el, "AXValue", None) or ""
                role = getattr(el, "AXRole", None) or ""

                if (title.strip() or desc.strip() or value.strip()) and role not in [
                    "AXGroup",
                    "AXUnknown",
                ]:
                    content_elements.append((el, title, desc, value, role))

            for i, (el, title, desc, value, role) in enumerate(content_elements):
                print(
                    f"  {i+1}. [{role}] Title: '{title}' | Desc: '{desc}' | Value: '{value}'"
                )
                print(f"      Position: {getattr(el, 'AXPosition', 'Unknown')}")
                print(f"      Size: {getattr(el, 'AXSize', 'Unknown')}")

            return True

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _collect_all_elements(
        self, element, elements_list, max_depth=5, current_depth=0
    ):
        """Recursively collect all elements."""
        if current_depth >= max_depth:
            return

        try:
            elements_list.append(element)
            children = getattr(element, "AXChildren", None) or []
            for child in children:
                self._collect_all_elements(
                    child, elements_list, max_depth, current_depth + 1
                )
        except Exception:
            pass

    def create_llm_instructions(self):
        """Create instructions for an LLM to use the Calculator."""
        print(f"\n🤖 LLM Instructions for Calculator Automation:")
        print("=" * 60)

        try:
            app = atomac.getAppRefByLocalizedName("Calculator")
            if not app:
                print("❌ Calculator not found")
                return

            window = app.windows()[0]
            buttons = window.findAllR(AXRole="AXButton") or []

            print("To calculate 1+2, an LLM should:")
            print("1. Find the Calculator window")
            print("2. Click buttons in this order:")

            # Try to map button positions to numbers
            button_positions = []
            for i, button in enumerate(buttons):
                pos = getattr(button, "AXPosition", None)
                size = getattr(button, "AXSize", None)
                if pos and size:
                    button_positions.append((i + 1, pos, size))

            # Sort by position (top to bottom, left to right)
            button_positions.sort(key=lambda x: (x[1].y, x[1].x))

            print("Button positions (sorted by screen position):")
            for i, (button_num, pos, size) in enumerate(button_positions):
                print(
                    f"  Button {button_num}: Position ({pos.x}, {pos.y}) Size ({size.width}x{size.height})"
                )

            print("\nFor calculation '1+2=':")
            print("1. Click button at position that looks like '1'")
            print("2. Click button at position that looks like '+'")
            print("3. Click button at position that looks like '2'")
            print("4. Click button at position that looks like '='")

        except Exception as e:
            print(f"❌ Error creating instructions: {e}")


def main():
    debugger = CalculatorDebugger()

    print("🧮 Calculator Debug Tool")
    print("Getting detailed button information for LLM automation")
    print()

    # Debug calculator buttons
    debugger.debug_calculator_buttons()

    # Create LLM instructions
    debugger.create_llm_instructions()


if __name__ == "__main__":
    main()
