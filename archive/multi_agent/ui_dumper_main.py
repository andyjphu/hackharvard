#!/usr/bin/env python3
"""
Final Comprehensive UI Element Dumper
The ultimate tool for dumping all UI elements in a beautiful tree format.
Combines all the best approaches from the existing files.
"""

import sys
import time
import subprocess
import json
from typing import Any, Optional, List, Dict, Tuple
from collections import deque

# Try to import accessibility modules
try:
    from ApplicationServices import (
        AXIsProcessTrustedWithOptions,
        kAXTrustedCheckOptionPrompt,
        AXUIElementCreateApplication,
        AXUIElementCreateSystemWide,
        AXUIElementCopyAttributeNames,
        AXUIElementCopyAttributeValue,
        AXUIElementCopyMultipleAttributeValues,
        AXUIElementCopyParameterizedAttributeNames,
        AXUIElementCopyActionNames,
        kAXRoleAttribute,
        kAXRoleDescriptionAttribute,
        kAXSubroleAttribute,
        kAXIdentifierAttribute,
        kAXTitleAttribute,
        kAXDescriptionAttribute,
        kAXHelpAttribute,
        kAXValueAttribute,
        kAXEnabledAttribute,
        kAXFocusedAttribute,
        kAXPositionAttribute,
        kAXSizeAttribute,
        kAXParentAttribute,
        kAXChildrenAttribute,
        kAXWindowsAttribute,
        kAXToolbarRole,
        kAXButtonRole,
        kAXTabGroupRole,
        kAXWindowRole,
        kAXApplicationRole,
        kAXMenuBarRole,
        kAXMenuItemRole,
        kAXStaticTextRole,
        kAXTextFieldRole,
        kAXTextAreaRole,
        kAXScrollAreaRole,
        kAXGroupRole,
        kAXListRole,
        kAXTableRole,
        kAXRowRole,
        kAXColumnRole,
        kAXCellRole,
        kAXImageRole,
        kAXCheckBoxRole,
        kAXRadioButtonRole,
        kAXSliderRole,
        kAXProgressIndicatorRole,
        kAXComboBoxRole,
        kAXPopUpButtonRole,
        kAXMenuRole,
        kAXMenuBarItemRole,
        kAXSplitGroupRole,
        kAXDisclosureTriangleRole,
        kAXOutlineRole,
        kAXBrowserRole,
        kAXSystemWideRole,
    )
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGWindowListOptionAll,
        kCGNullWindowID,
        kCGWindowOwnerPID,
        kCGWindowOwnerName,
        kCGWindowName,
        kCGWindowBounds,
        kCGWindowLayer,
    )
    from AppKit import NSRunningApplication

    ACCESSIBILITY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Accessibility modules not available: {e}")
    ACCESSIBILITY_AVAILABLE = False

# Try to import atomacos for alternative approach
try:
    import atomacos as atomac

    ATOMAC_AVAILABLE = True
except ImportError:
    ATOMAC_AVAILABLE = False


class FinalUIDumper:
    def __init__(self):
        self.seen_elements = set()
        self.depth_limit = 20
        self.max_children_per_level = 30

    def _safe(self, f, *a, **kw):
        """Safely execute a function, returning error message on exception."""
        try:
            return f(*a, **kw)
        except Exception as e:
            return f"<error: {e}>"

    def format_value(self, v: Any, max_list=3):
        """Format a value for display."""
        if hasattr(v, "__class__") and "AXUIElement" in str(v.__class__):
            return f"<AXUIElement {id(v)}>"
        if isinstance(v, (list, tuple)):
            s = ", ".join(self.format_value(x) for x in v[:max_list])
            return f"[{s}{'' if len(v)<=max_list else f', …(+{len(v)-max_list})'}]"
        return repr(v)

    def get_element_info(self, el):
        """Get comprehensive information about a UI element."""
        if not ACCESSIBILITY_AVAILABLE:
            return {"error": "Accessibility not available"}

        # Get all available attributes
        all_attrs = self._safe(AXUIElementCopyAttributeNames, el)
        if isinstance(all_attrs, (list, tuple)):
            # Get all attributes in one call for efficiency
            multi_values = self._safe(
                AXUIElementCopyMultipleAttributeValues, el, all_attrs, True
            )
            if isinstance(multi_values, dict):
                return multi_values
            else:
                # Fallback to individual calls
                return self._get_element_info_individual(el)
        else:
            return self._get_element_info_individual(el)

    def _get_element_info_individual(self, el):
        """Get element info using individual attribute calls."""
        return {
            "role": self._safe(AXUIElementCopyAttributeValue, el, kAXRoleAttribute),
            "role_description": self._safe(
                AXUIElementCopyAttributeValue, el, kAXRoleDescriptionAttribute
            ),
            "subrole": self._safe(
                AXUIElementCopyAttributeValue, el, kAXSubroleAttribute
            ),
            "title": self._safe(AXUIElementCopyAttributeValue, el, kAXTitleAttribute),
            "description": self._safe(
                AXUIElementCopyAttributeValue, el, kAXDescriptionAttribute
            ),
            "identifier": self._safe(
                AXUIElementCopyAttributeValue, el, kAXIdentifierAttribute
            ),
            "value": self._safe(AXUIElementCopyAttributeValue, el, kAXValueAttribute),
            "enabled": self._safe(
                AXUIElementCopyAttributeValue, el, kAXEnabledAttribute
            ),
            "focused": self._safe(
                AXUIElementCopyAttributeValue, el, kAXFocusedAttribute
            ),
            "position": self._safe(
                AXUIElementCopyAttributeValue, el, kAXPositionAttribute
            ),
            "size": self._safe(AXUIElementCopyAttributeValue, el, kAXSizeAttribute),
            "help": self._safe(AXUIElementCopyAttributeValue, el, kAXHelpAttribute),
        }

    def print_beautiful_tree(self, el, indent=0, max_depth=None, prefix=""):
        """Print a beautiful tree structure."""
        if max_depth is not None and indent >= max_depth:
            return

        if id(el) in self.seen_elements:
            print("  " * indent + f"{prefix}↻ (circular reference)")
            return

        self.seen_elements.add(id(el))

        info = self.get_element_info(el)

        # Create a beautiful header
        role = info.get("role", "Unknown")
        title = info.get("title", "")
        desc = info.get("description", "")

        # Choose emoji based on role
        emoji_map = {
            "AXWindow": "🪟",
            "AXButton": "🔘",
            "AXToolbar": "🔧",
            "AXTabGroup": "📑",
            "AXTab": "📄",
            "AXMenuBar": "📋",
            "AXMenuItem": "📝",
            "AXTextField": "📝",
            "AXStaticText": "📄",
            "AXGroup": "📦",
            "AXList": "📋",
            "AXTable": "📊",
            "AXImage": "🖼️",
            "AXCheckBox": "☑️",
            "AXRadioButton": "🔘",
            "AXSlider": "🎚️",
            "AXComboBox": "📋",
            "AXPopUpButton": "📋",
            "AXMenu": "📋",
            "AXScrollArea": "📜",
            "AXBrowser": "🌐",
            "AXApplication": "🚀",
        }

        emoji = emoji_map.get(role, "🔹")

        # Build the display text
        parts = [f"{emoji} {role}"]
        if title:
            parts.append(f'"{title}"')
        if desc and desc != title:
            parts.append(f"({desc})")

        display_text = " ".join(parts)

        # Add position and size info if available
        pos = info.get("position")
        size = info.get("size")
        if (
            isinstance(pos, tuple)
            and isinstance(size, tuple)
            and len(pos) == 2
            and len(size) == 2
        ):
            display_text += f" [{pos[0]:.0f},{pos[1]:.0f} {size[0]:.0f}x{size[1]:.0f}]"

        # Add status indicators
        status = []
        if info.get("enabled") is False:
            status.append("❌")
        if info.get("focused") is True:
            status.append("🎯")
        if status:
            display_text += f" {' '.join(status)}"

        # Print with beautiful formatting
        print("  " * indent + f"{prefix}{display_text}")

        # Process children
        children = self._safe(AXUIElementCopyAttributeValue, el, kAXChildrenAttribute)
        if isinstance(children, (list, tuple)) and children:
            # Process ALL children - no limiting
            for i, child in enumerate(children):
                is_last = i == len(children) - 1
                child_prefix = "└─ " if is_last else "├─ "
                self.print_beautiful_tree(child, indent + 1, max_depth, child_prefix)

    def get_running_applications(self):
        """Get all running applications."""
        try:
            result = subprocess.run(
                ["ps", "-ax", "-o", "pid,comm"], capture_output=True, text=True
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]
                apps = []
                for line in lines:
                    parts = line.strip().split(None, 1)
                    if len(parts) == 2:
                        pid, comm = parts
                        if comm and not comm.startswith("["):
                            apps.append({"pid": int(pid), "name": comm})
                return apps
        except Exception as e:
            print(f"Error getting applications: {e}")
        return []

    def get_window_list(self):
        """Get window list using system commands."""
        try:
            # Use system_profiler to get display information
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print("🖥️  Display information available")
                return True
        except Exception as e:
            print(f"Error getting window info: {e}")
        return False

    def dump_application_with_atomac(self, app_name="Chrome"):
        """Dump application using atomac library."""
        if not ATOMAC_AVAILABLE:
            print("❌ Atomac not available")
            return False

        print(f"\n{'='*80}")
        print(f"🌳 BEAUTIFUL UI TREE FOR: {app_name.upper()}")
        print(f"{'='*80}")

        try:
            # Try to get the application
            if app_name.lower() == "chrome":
                app = atomac.getAppRefByBundleId("com.google.Chrome")
            else:
                app = atomac.getAppRefByLocalizedName(app_name)

            if not app:
                print(f"❌ Application not found: {app_name}")
                return False

            # Activate the app
            app.activate()
            time.sleep(0.5)

            # Get windows
            windows = [
                w
                for w in app.windows()
                if getattr(w, "AXRole", None) == "AXWindow"
                and getattr(w, "AXMinimized", False) is not True
            ]

            if not windows:
                print("❌ No windows found")
                return False

            print(f"🎯 Found {len(windows)} windows")

            for i, window in enumerate(windows):
                print(f"\n{'─'*60}")
                print(f"🪟 WINDOW {i+1}: {getattr(window, 'AXTitle', 'Untitled')}")
                print(f"{'─'*60}")

                # Create a mock element for the window to use with our tree printer
                class MockElement:
                    def __init__(self, atomac_element):
                        self.atomac_element = atomac_element

                    def get_info(self):
                        return {
                            "role": getattr(self.atomac_element, "AXRole", "Unknown"),
                            "title": getattr(self.atomac_element, "AXTitle", ""),
                            "description": getattr(
                                self.atomac_element, "AXDescription", ""
                            ),
                            "position": getattr(
                                self.atomac_element, "AXPosition", None
                            ),
                            "size": getattr(self.atomac_element, "AXSize", None),
                            "enabled": getattr(self.atomac_element, "AXEnabled", True),
                            "focused": getattr(self.atomac_element, "AXFocused", False),
                        }

                # Print window info
                window_info = MockElement(window).get_info()
                print(f"📊 Window Info:")
                for key, value in window_info.items():
                    if value is not None:
                        print(f"   {key}: {value}")

                # Find and display specific UI elements
                self.find_and_display_elements(window, "Toolbars", "AXToolbar")
                self.find_and_display_elements(window, "Buttons", "AXButton")
                self.find_and_display_elements(window, "Tab Groups", "AXTabGroup")
                self.find_and_display_elements(window, "Text Fields", "AXTextField")
                self.find_and_display_elements(window, "Static Text", "AXStaticText")
                self.find_and_display_elements(window, "Groups", "AXGroup")
                self.find_and_display_elements(window, "Lists", "AXList")
                self.find_and_display_elements(window, "Tables", "AXTable")
                self.find_and_display_elements(window, "Images", "AXImage")
                self.find_and_display_elements(window, "Checkboxes", "AXCheckBox")
                self.find_and_display_elements(window, "Radio Buttons", "AXRadioButton")
                self.find_and_display_elements(window, "Sliders", "AXSlider")
                self.find_and_display_elements(window, "Combo Boxes", "AXComboBox")
                self.find_and_display_elements(
                    window, "Pop-up Buttons", "AXPopUpButton"
                )
                self.find_and_display_elements(window, "Menus", "AXMenu")
                self.find_and_display_elements(window, "Scroll Areas", "AXScrollArea")
                self.find_and_display_elements(window, "Browsers", "AXBrowser")

                # Additional element types that might be in Cursor/VS Code
                self.find_and_display_elements(window, "Menu Items", "AXMenuItem")
                self.find_and_display_elements(
                    window, "Menu Bar Items", "AXMenuBarItem"
                )
                self.find_and_display_elements(window, "Split Groups", "AXSplitGroup")
                self.find_and_display_elements(window, "Outlines", "AXOutline")
                self.find_and_display_elements(
                    window, "Disclosure Triangles", "AXDisclosureTriangle"
                )
                self.find_and_display_elements(
                    window, "Progress Indicators", "AXProgressIndicator"
                )

                # Try to find any elements with titles or descriptions
                self.find_elements_with_content(window)

        except Exception as e:
            print(f"❌ Error with atomac: {e}")
            return False

        return True

    def find_and_display_elements(self, window, element_type, role):
        """Find and display elements of a specific type with full details."""
        try:
            elements = window.findAllR(AXRole=role) or []
            if elements:
                print(f"\n🔍 {element_type} ({len(elements)} found):")
                for i, el in enumerate(elements):  # Show ALL elements
                    # Get comprehensive element information
                    title = getattr(el, "AXTitle", None) or ""
                    desc = getattr(el, "AXDescription", None) or ""
                    identifier = getattr(el, "AXIdentifier", None) or ""
                    value = getattr(el, "AXValue", None) or ""
                    help_text = getattr(el, "AXHelp", None) or ""
                    enabled = getattr(el, "AXEnabled", True)
                    focused = getattr(el, "AXFocused", False)
                    position = getattr(el, "AXPosition", None)
                    size = getattr(el, "AXSize", None)
                    role_desc = getattr(el, "AXRoleDescription", None) or ""

                    # Build status indicators
                    status = []
                    if not enabled:
                        status.append("❌")
                    if focused:
                        status.append("🎯")
                    status_str = " " + " ".join(status) if status else ""

                    # Primary display line
                    display_parts = []
                    if title:
                        display_parts.append(f"Title: '{title}'")
                    if desc and desc != title:
                        display_parts.append(f"Desc: '{desc}'")
                    if identifier:
                        display_parts.append(f"ID: '{identifier}'")
                    if value:
                        display_parts.append(f"Value: '{value}'")
                    if help_text:
                        display_parts.append(f"Help: '{help_text}'")

                    if display_parts:
                        display_text = (
                            f"   {i+1}. {' | '.join(display_parts)}{status_str}"
                        )
                    else:
                        display_text = f"   {i+1}. (no title/desc/id/value){status_str}"

                    print(display_text)

                    # Additional details line
                    detail_parts = []
                    if position:
                        detail_parts.append(
                            f"Pos: ({position.x:.0f}, {position.y:.0f})"
                        )
                    if size:
                        detail_parts.append(
                            f"Size: ({size.width:.0f}x{size.height:.0f})"
                        )
                    if role_desc:
                        detail_parts.append(f"Role: {role_desc}")

                    if detail_parts:
                        print(f"       {' | '.join(detail_parts)}")

        except Exception as e:
            print(f"   Error finding {element_type}: {e}")

    def find_elements_with_content(self, window):
        """Find any elements that have titles, descriptions, or other content."""
        try:
            print(f"\n🔍 Elements with Content:")

            # Get all elements recursively
            all_elements = []
            self._collect_all_elements(window, all_elements)

            # Filter elements that have meaningful content
            content_elements = []
            for el in all_elements:
                title = getattr(el, "AXTitle", None) or ""
                desc = getattr(el, "AXDescription", None) or ""
                role = getattr(el, "AXRole", None) or ""

                # Skip empty or generic elements
                if (title.strip() or desc.strip()) and role not in [
                    "AXGroup",
                    "AXUnknown",
                ]:
                    content_elements.append((el, title, desc, role))

            if content_elements:
                print(f"   Found {len(content_elements)} elements with content:")
                for i, (el, title, desc, role) in enumerate(
                    content_elements[:50]
                ):  # Limit to 50 for readability
                    # Get additional details
                    identifier = getattr(el, "AXIdentifier", None) or ""
                    value = getattr(el, "AXValue", None) or ""
                    help_text = getattr(el, "AXHelp", None) or ""
                    position = getattr(el, "AXPosition", None)
                    size = getattr(el, "AXSize", None)
                    enabled = getattr(el, "AXEnabled", True)
                    focused = getattr(el, "AXFocused", False)

                    # Build status indicators
                    status = []
                    if not enabled:
                        status.append("❌")
                    if focused:
                        status.append("🎯")
                    status_str = " " + " ".join(status) if status else ""

                    # Primary display line
                    display_parts = [f"[{role}]"]
                    if title:
                        display_parts.append(f"Title: '{title}'")
                    if desc and desc != title:
                        display_parts.append(f"Desc: '{desc}'")
                    if identifier:
                        display_parts.append(f"ID: '{identifier}'")
                    if value:
                        display_parts.append(f"Value: '{value}'")
                    if help_text:
                        display_parts.append(f"Help: '{help_text}'")

                    display_text = f"   {i+1}. {' | '.join(display_parts)}{status_str}"
                    print(display_text)

                    # Additional details line
                    detail_parts = []
                    if position:
                        detail_parts.append(
                            f"Pos: ({position.x:.0f}, {position.y:.0f})"
                        )
                    if size:
                        detail_parts.append(
                            f"Size: ({size.width:.0f}x{size.height:.0f})"
                        )

                    if detail_parts:
                        print(f"       {' | '.join(detail_parts)}")

                if len(content_elements) > 50:
                    print(
                        f"   ... and {len(content_elements) - 50} more elements with content"
                    )
            else:
                print("   No elements with meaningful content found")

        except Exception as e:
            print(f"   Error finding elements with content: {e}")

    def _collect_all_elements(
        self, element, elements_list, max_depth=10, current_depth=0
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

    def dump_system_overview(self):
        """Dump system overview."""
        print(f"\n{'='*80}")
        print("🖥️  SYSTEM OVERVIEW")
        print(f"{'='*80}")

        # Get running processes
        apps = self.get_running_applications()
        print(f"📊 Total processes: {len(apps)}")

        # Group by application
        app_groups = {}
        for app in apps:
            name = app["name"]
            if name not in app_groups:
                app_groups[name] = []
            app_groups[name].append(app)

        print(f"🚀 Unique applications: {len(app_groups)}")

        # Show top applications by process count
        sorted_apps = sorted(app_groups.items(), key=lambda x: len(x[1]), reverse=True)
        print(f"\n🏆 Top applications by process count:")
        for name, procs in sorted_apps[:15]:
            emoji = (
                "🌐"
                if "Chrome" in name
                else "💻" if "Cursor" in name else "🔧" if "System" in name else "📱"
            )
            print(f"   {emoji} {name}: {len(procs)} processes")

        # Get display information
        self.get_window_list()

    def dump_all_applications(self):
        """Dump all applications."""
        print(f"\n{'='*80}")
        print("🌍 ALL APPLICATIONS")
        print(f"{'='*80}")

        apps = self.get_running_applications()
        app_groups = {}
        for app in apps:
            name = app["name"]
            if name not in app_groups:
                app_groups[name] = []
            app_groups[name].append(app)

        print(f"Found {len(app_groups)} unique applications:")

        # Categorize applications
        categories = {
            "Browsers": [],
            "Development": [],
            "System": [],
            "Media": [],
            "Utilities": [],
            "Other": [],
        }

        for name, procs in app_groups.items():
            if any(
                browser in name for browser in ["Chrome", "Safari", "Firefox", "Edge"]
            ):
                categories["Browsers"].append((name, len(procs)))
            elif any(
                dev in name for dev in ["Cursor", "Code", "Xcode", "Terminal", "Python"]
            ):
                categories["Development"].append((name, len(procs)))
            elif any(
                sys in name for sys in ["System", "Library", "usr", "bin", "sbin"]
            ):
                categories["System"].append((name, len(procs)))
            elif any(media in name for media in ["Music", "Video", "Photo", "Discord"]):
                categories["Media"].append((name, len(procs)))
            elif any(
                util in name for util in ["Finder", "Dock", "Control", "Settings"]
            ):
                categories["Utilities"].append((name, len(procs)))
            else:
                categories["Other"].append((name, len(procs)))

        for category, apps in categories.items():
            if apps:
                print(f"\n📂 {category}:")
                for name, count in sorted(apps, key=lambda x: x[1], reverse=True)[:10]:
                    emoji = (
                        "🌐" if "Chrome" in name else "💻" if "Cursor" in name else "🔧"
                    )
                    print(f"   {emoji} {name}: {count} processes")


def main():
    """Main function."""
    dumper = FinalUIDumper()

    print("🎯 Final Comprehensive UI Element Dumper")
    print("The ultimate tool for discovering and displaying UI elements")
    print()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--system":
            dumper.dump_system_overview()
        elif sys.argv[1] == "--all":
            dumper.dump_all_applications()
        elif sys.argv[1] == "--chrome":
            dumper.dump_application_with_atomac("Chrome")
        elif sys.argv[1] == "--safari":
            dumper.dump_application_with_atomac("Safari")
        elif sys.argv[1] == "--cursor":
            dumper.dump_application_with_atomac("Cursor")
        else:
            app_name = sys.argv[1]
            dumper.dump_application_with_atomac(app_name)
    else:
        print("No arguments provided. Usage examples:")
        print("  python final_ui_dumper.py --system")
        print("  python final_ui_dumper.py --all")
        print("  python final_ui_dumper.py --chrome")
        print("  python final_ui_dumper.py --safari")
        print("  python final_ui_dumper.py --cursor")
        print("  python final_ui_dumper.py Chrome")
        print()
        dumper.dump_system_overview()


if __name__ == "__main__":
    main()
