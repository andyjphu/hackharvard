#!/usr/bin/env python3
"""
Low Power Mode Automation
Automates turning Low Power Mode on/off in System Settings
"""

import sys
import time
import atomacos as atomac


class LowPowerAutomation:
    def __init__(self):
        pass

    def find_low_power_toggle(self):
        """Find the Low Power Mode toggle in System Settings."""
        print("🔋 Low Power Mode Automation")
        print("=" * 50)

        try:
            # Get System Settings app
            app = atomac.getAppRefByLocalizedName("System Settings")
            if not app:
                print(
                    "❌ System Settings not found. Please open System Settings first."
                )
                return None

            print("✅ Found System Settings application")

            # Activate and wait
            app.activate()
            time.sleep(2)

            # Get windows
            windows = [
                w for w in app.windows() if getattr(w, "AXRole", None) == "AXWindow"
            ]

            if not windows:
                print("❌ No System Settings windows found")
                return None

            window = windows[0]
            print(
                f"✅ Found System Settings window: {getattr(window, 'AXTitle', 'Untitled')}"
            )

            # Look for Low Power Mode toggle
            print("\n🔍 Searching for Low Power Mode toggle...")

            # Method 1: Look for pop-up button with low_power_mode ID
            popup_buttons = window.findAllR(AXRole="AXPopUpButton") or []
            for i, button in enumerate(popup_buttons):
                identifier = getattr(button, "AXIdentifier", None) or ""
                value = getattr(button, "AXValue", None) or ""
                position = getattr(button, "AXPosition", None)
                size = getattr(button, "AXSize", None)

                print(f"  Pop-up Button {i+1}:")
                print(f"    ID: '{identifier}'")
                print(f"    Value: '{value}'")
                if position and size:
                    print(f"    Position: ({position.x:.0f}, {position.y:.0f})")
                    print(f"    Size: ({size.width:.0f}x{size.height:.0f})")

                if "low_power_mode" in identifier.lower():
                    print(f"✅ Found Low Power Mode toggle!")
                    return button

            # Method 2: Look for static text with "Low Power Mode"
            static_texts = window.findAllR(AXRole="AXStaticText") or []
            for i, text in enumerate(static_texts):
                value = getattr(text, "AXValue", None) or ""
                identifier = getattr(text, "AXIdentifier", None) or ""

                if "Low Power Mode" in value:
                    print(f"✅ Found Low Power Mode text: '{value}'")
                    print(f"    ID: '{identifier}'")

                    # Try to find nearby toggle
                    position = getattr(text, "AXPosition", None)
                    if position:
                        print(f"    Position: ({position.x:.0f}, {position.y:.0f})")
                        # Look for nearby pop-up button
                        for button in popup_buttons:
                            btn_pos = getattr(button, "AXPosition", None)
                            if btn_pos and abs(btn_pos.y - position.y) < 50:
                                print(
                                    f"    Found nearby toggle at ({btn_pos.x:.0f}, {btn_pos.y:.0f})"
                                )
                                return button

            print("❌ Low Power Mode toggle not found")
            return None

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()
            return None

    def get_low_power_status(self):
        """Get current Low Power Mode status."""
        toggle = self.find_low_power_toggle()
        if not toggle:
            return None

        try:
            value = getattr(toggle, "AXValue", None) or ""
            print(f"📊 Current Low Power Mode status: '{value}'")
            return value
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            return None

    def toggle_low_power_mode(self, turn_on=True):
        """Toggle Low Power Mode on or off."""
        toggle = self.find_low_power_toggle()
        if not toggle:
            print("❌ Cannot find Low Power Mode toggle")
            return False

        try:
            current_value = getattr(toggle, "AXValue", None) or ""
            print(f"📊 Current status: '{current_value}'")

            # Check if already in desired state
            if turn_on and current_value.lower() in ["on", "yes", "enabled"]:
                print("✅ Low Power Mode is already ON")
                return True
            elif not turn_on and current_value.lower() in [
                "off",
                "no",
                "disabled",
                "never",
            ]:
                print("✅ Low Power Mode is already OFF")
                return True

            # Click the toggle to open dropdown
            print(f"🔄 {'Turning ON' if turn_on else 'Turning OFF'} Low Power Mode...")
            print("   Clicking toggle to open dropdown menu...")
            toggle.AXPress()
            time.sleep(2)  # Wait for dropdown to appear

            # Look for the dropdown menu
            print("   Looking for dropdown menu options...")
            app = atomac.getAppRefByLocalizedName("System Settings")
            windows = [
                w for w in app.windows() if getattr(w, "AXRole", None) == "AXWindow"
            ]

            # Look for menu items in all windows
            menu_items = []
            for window in windows:
                items = window.findAllR(AXRole="AXMenuItem") or []
                menu_items.extend(items)

            print(f"   Found {len(menu_items)} menu items")

            # Look for the desired option
            target_option = "On" if turn_on else "Never"
            selected_item = None

            for item in menu_items:
                title = getattr(item, "AXTitle", None) or ""
                value = getattr(item, "AXValue", None) or ""
                print(f"     Menu item: '{title}' | Value: '{value}'")

                if (
                    target_option.lower() in title.lower()
                    or target_option.lower() in value.lower()
                ):
                    selected_item = item
                    print(f"   ✅ Found target option: '{title}'")
                    break

            if selected_item:
                print(
                    f"   Clicking '{getattr(selected_item, 'AXTitle', 'Unknown')}'..."
                )
                selected_item.AXPress()
                time.sleep(1)

                # Check new status
                new_value = getattr(toggle, "AXValue", None) or ""
                print(f"📊 New status: '{new_value}'")

                if turn_on and new_value.lower() in ["on", "yes", "enabled"]:
                    print("✅ Low Power Mode is now ON")
                    return True
                elif not turn_on and new_value.lower() in [
                    "off",
                    "no",
                    "disabled",
                    "never",
                ]:
                    print("✅ Low Power Mode is now OFF")
                    return True
                else:
                    print(f"✅ Status changed to '{new_value}'")
                    return True
            else:
                print(f"❌ Could not find '{target_option}' option in dropdown")
                return False

        except Exception as e:
            print(f"❌ Error toggling Low Power Mode: {e}")
            import traceback

            traceback.print_exc()
            return False

    def create_llm_instructions(self):
        """Create instructions for LLM to control Low Power Mode."""
        print(f"\n🤖 LLM Instructions for Low Power Mode Control:")
        print("=" * 60)

        toggle = self.find_low_power_toggle()
        if not toggle:
            print("❌ Cannot create instructions - toggle not found")
            return

        try:
            position = getattr(toggle, "AXPosition", None)
            size = getattr(toggle, "AXSize", None)
            identifier = getattr(toggle, "AXIdentifier", None) or ""
            current_value = getattr(toggle, "AXValue", None) or ""

            print("To control Low Power Mode, an LLM should:")
            print("1. Open System Settings")
            print("2. Navigate to Battery settings")
            print("3. Find the Low Power Mode pop-up button")
            print("4. Click the button to open dropdown menu")
            print("5. Select desired option from the menu")
            print()
            print("Toggle Details:")
            print(f"  - Identifier: '{identifier}'")
            print(f"  - Current Value: '{current_value}'")
            if position and size:
                print(f"  - Position: ({position.x:.0f}, {position.y:.0f})")
                print(f"  - Size: ({size.width:.0f}x{size.height:.0f})")
            print()
            print("Available Options (from dropdown menu):")
            print("  - 'Never' - Low Power Mode is OFF")
            print("  - 'Always' - Low Power Mode is always ON")
            print("  - 'Only on Battery' - Low Power Mode when on battery power")
            print()
            print("To turn ON Low Power Mode:")
            print("  - Click the pop-up button to open dropdown")
            print("  - Select 'Always' or 'Only on Battery' from the menu")
            print()
            print("To turn OFF Low Power Mode:")
            print("  - Click the pop-up button to open dropdown")
            print("  - Select 'Never' from the menu")

        except Exception as e:
            print(f"❌ Error creating instructions: {e}")


def main():
    automation = LowPowerAutomation()

    print("🔋 Low Power Mode Automation Tool")
    print("Automates Low Power Mode toggle in System Settings")
    print()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--on":
            automation.toggle_low_power_mode(turn_on=True)
        elif sys.argv[1] == "--off":
            automation.toggle_low_power_mode(turn_on=False)
        elif sys.argv[1] == "--status":
            automation.get_low_power_status()
        elif sys.argv[1] == "--instructions":
            automation.create_llm_instructions()
        else:
            print("Usage:")
            print(
                "  python low_power_automation.py --on        # Turn ON Low Power Mode"
            )
            print(
                "  python low_power_automation.py --off       # Turn OFF Low Power Mode"
            )
            print("  python low_power_automation.py --status    # Check current status")
            print(
                "  python low_power_automation.py --instructions  # Get LLM instructions"
            )
    else:
        # Default: show status and instructions
        automation.get_low_power_status()
        automation.create_llm_instructions()


if __name__ == "__main__":
    main()
