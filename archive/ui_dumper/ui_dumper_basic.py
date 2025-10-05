#!/usr/bin/env python3
# Dumps full Accessibility info for Google Chrome's toolbar and its children on macOS.

import sys
import time
from typing import Any
from Quartz import (
    AXUIElementCreateApplication,
    AXUIElementCopyAttributeNames,
    AXUIElementCopyAttributeValue,
    AXUIElementCopyMultipleAttributeValues,
    AXUIElementCopyParameterizedAttributeNames,
    AXUIElementCopyActionNames,
    AXUIElementPerformAction,
    kAXRoleAttribute,
    kAXSubroleAttribute,
    kAXTitleAttribute,
    kAXDescriptionAttribute,
    kAXHelpAttribute,
    kAXIdentifierAttribute,
    kAXValueAttribute,
    kAXEnabledAttribute,
    kAXFocusedAttribute,
    kAXPositionAttribute,
    kAXSizeAttribute,
    kAXParentAttribute,
    kAXChildrenAttribute,
    kAXWindowsAttribute,
    kAXToolbarRole,
    kAXRoleDescriptionAttribute,
)
from AppKit import NSRunningApplication

# -------- Helpers --------

def _safe(callable_, *args, **kwargs):
    try:
        return callable_(*args, **kwargs)
    except Exception as e:
        return f"<error: {e}>"

def attr_names(el) -> list[str]:
    names = _safe(AXUIElementCopyAttributeNames, el)
    return list(names) if isinstance(names, (list, tuple)) else []

def param_attr_names(el) -> list[str]:
    names = _safe(AXUIElementCopyParameterizedAttributeNames, el)
    return list(names) if isinstance(names, (list, tuple)) else []

def action_names(el) -> list[str]:
    names = _safe(AXUIElementCopyActionNames, el)
    return list(names) if isinstance(names, (list, tuple)) else []

PRIORITY_ATTRS = [
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
]

def format_value(v: Any, max_list=8):
    from Quartz import AXUIElementRef
    if hasattr(v, '__class__') and v.__class__.__name__ == 'AXUIElementRef':
        return f"<AXUIElement {id(v)}>"
    if isinstance(v, (list, tuple)):
        items = ", ".join(format_value(x) for x in v[:max_list])
        suffix = "" if len(v) <= max_list else f", …(+{len(v)-max_list})"
        return f"[{items}{suffix}]"
    return repr(v)

def print_element(el, indent=0, header=None):
    pad = "  " * indent
    if header:
        print(f"{pad}{header}")

    # Priority attrs first
    names = attr_names(el)
    ordered = [a for a in PRIORITY_ATTRS if a in names] + [a for a in names if a not in PRIORITY_ATTRS]

    # Batch some common attrs to avoid slow, repeated calls
    batchable = [a for a in ordered if a not in (kAXChildrenAttribute, kAXParentAttribute)]
    multi = _safe(AXUIElementCopyMultipleAttributeValues, el, batchable, True)
    multi_map = {}
    if isinstance(multi, dict):
        multi_map = multi

    for a in ordered:
        if a == kAXChildrenAttribute:
            # children handled later
            continue
        val = multi_map.get(a, _safe(AXUIElementCopyAttributeValue, el, a))
        print(f"{pad}- {a}: {format_value(val)}")

    # Parameterized attributes & actions
    pa = param_attr_names(el)
    if pa:
        print(f"{pad}- ParameterizedAttributes: {pa}")
    acts = action_names(el)
    if acts:
        print(f"{pad}- Actions: {acts}")

    # Recurse into children
    children = _safe(AXUIElementCopyAttributeValue, el, kAXChildrenAttribute)
    if isinstance(children, (list, tuple)):
        for i, c in enumerate(children):
            print_element(c, indent + 1, header=f"Child[{i}]")

def get_chrome_pid() -> int | None:
    # Prefer bundle id for accuracy
    apps = NSRunningApplication.runningApplicationsWithBundleIdentifier_("com.google.Chrome")
    if apps and len(apps) > 0:
        return apps[0].processIdentifier()
    return None

def find_toolbar(el):
    # BFS search for toolbar element by role
    from collections import deque
    q = deque([el])
    seen = set()
    while q:
        node = q.popleft()
        if id(node) in seen:
            continue
        seen.add(id(node))
        role = _safe(AXUIElementCopyAttributeValue, node, kAXRoleAttribute)
        if role == kAXToolbarRole:
            return node
        children = _safe(AXUIElementCopyAttributeValue, node, kAXChildrenAttribute)
        if isinstance(children, (list, tuple)):
            q.extend(children)
    return None

def get_front_window(app_el):
    windows = _safe(AXUIElementCopyAttributeValue, app_el, kAXWindowsAttribute)
    if isinstance(windows, (list, tuple)) and windows:
        return windows[0]
    return None

# -------- Main --------

def main():
    pid = get_chrome_pid()
    if not pid:
        print("❌ Google Chrome not found. Launch Chrome and try again.")
        sys.exit(1)

    app_el = AXUIElementCreateApplication(pid)
    win = get_front_window(app_el)
    if not win:
        print("❌ Could not get Chrome front window via Accessibility API.")
        sys.exit(2)

    toolbar = find_toolbar(win)
    if not toolbar:
        print("❌ Could not find AXToolbar in the front Chrome window.")
        sys.exit(3)

    print("== Google Chrome Toolbar (full accessibility dump) ==")
    print_element(toolbar, indent=0)

if __name__ == "__main__":
    main()
