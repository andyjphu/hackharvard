#!/usr/bin/env python3
# Dump ALL Chrome toolbars, including non-focused windows (macOS).
# Uses AX (ApplicationServices) + CoreGraphics window list as fallback.

import sys, time, subprocess, math
from typing import Any, Iterable, Optional
from collections import deque

# ---- AX imports (PyObjC) ----
from ApplicationServices import (
    AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt,
    AXUIElementCreateApplication, AXUIElementCreateSystemWide,
    AXUIElementCopyAttributeNames, AXUIElementCopyAttributeValue,
    AXUIElementCopyMultipleAttributeValues,
    AXUIElementCopyParameterizedAttributeNames, AXUIElementCopyActionNames,
    # attrs/roles
    kAXRoleAttribute, kAXRoleDescriptionAttribute, kAXSubroleAttribute,
    kAXIdentifierAttribute, kAXTitleAttribute, kAXDescriptionAttribute, kAXHelpAttribute,
    kAXValueAttribute, kAXEnabledAttribute, kAXFocusedAttribute,
    kAXPositionAttribute, kAXSizeAttribute, kAXParentAttribute, kAXChildrenAttribute,
    kAXWindowsAttribute, kAXToolbarRole,
)

# ---- CoreGraphics window listing (PyObjC) ----
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID,
    kCGWindowOwnerPID,
    kCGWindowOwnerName,
    kCGWindowName,
    kCGWindowBounds,
    kCGWindowLayer,
)

CHROME_OWNER_NAMES = {"Google Chrome", "Google Chrome Beta", "Google Chrome Canary"}

# ---------- perms ----------
def ensure_accessibility_trust():
    if not AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True}):
        print("⚠️  Grant Accessibility permission to your terminal/IDE, then re-run.", file=sys.stderr)

# ---------- safe helpers ----------
def _safe(f, *a, **kw):
    try: return f(*a, **kw)
    except Exception as e: return f"<error: {e}>"

def ax_names(el):
    v = _safe(AXUIElementCopyAttributeNames, el)
    return list(v) if isinstance(v, (list, tuple)) else []

def ax_param_names(el):
    v = _safe(AXUIElementCopyParameterizedAttributeNames, el)
    return list(v) if isinstance(v, (list, tuple)) else []

def ax_actions(el):
    v = _safe(AXUIElementCopyActionNames, el)
    return list(v) if isinstance(v, (list, tuple)) else []

PRIORITY = [
    kAXRoleAttribute, kAXRoleDescriptionAttribute, kAXSubroleAttribute,
    kAXIdentifierAttribute, kAXTitleAttribute, kAXDescriptionAttribute,
    kAXHelpAttribute, kAXValueAttribute, kAXEnabledAttribute,
    kAXFocusedAttribute, kAXPositionAttribute, kAXSizeAttribute,
]

def fmt(v: Any, max_list=8):
    if getattr(v, "__class__", None) and v.__class__.__name__ == "AXUIElementRef":
        return "<AXUIElement>"
    if isinstance(v, (list, tuple)):
        s = ", ".join(fmt(x) for x in v[:max_list])
        return f"[{s}{'' if len(v)<=max_list else f', …(+{len(v)-max_list})'}]"
    return repr(v)

def print_el(el, indent=0, header=None):
    pad = "  " * indent
    if header: print(f"{pad}{header}")
    names = ax_names(el)
    ordered = [a for a in PRIORITY if a in names] + [a for a in names if a not in PRIORITY]
    batch = [a for a in ordered if a not in (kAXChildrenAttribute, kAXParentAttribute)]
    multi = _safe(AXUIElementCopyMultipleAttributeValues, el, batch, True)
    mmap = multi if isinstance(multi, dict) else {}
    for a in ordered:
        if a == kAXChildrenAttribute: continue
        val = mmap.get(a, _safe(AXUIElementCopyAttributeValue, el, a))
        print(f"{pad}- {a}: {fmt(val)}")
    pa = ax_param_names(el)
    if pa: print(f"{pad}- ParameterizedAttributes: {pa}")
    acts = ax_actions(el)
    if acts: print(f"{pad}- Actions: {acts}")
    kids = _safe(AXUIElementCopyAttributeValue, el, kAXChildrenAttribute)
    if isinstance(kids, (list, tuple)):
        for i, c in enumerate(kids):
            print_el(c, indent+1, header=f"Child[{i}]")

# ---------- discovery helpers ----------
def get_chrome_pid() -> Optional[int]:
    try:
        out = subprocess.check_output(
            ["bash","-lc", "pgrep -f 'Google Chrome( Beta| Canary)?$'"]
        ).splitlines()
        return int(out[0]) if out else None
    except Exception:
        return None

def app_ax(pid: int):
    return AXUIElementCreateApplication(pid)

def enumerate_ax_windows(app_el) -> list:
    # Preferred: AXWindows (works even when none is focused)
    wins = _safe(AXUIElementCopyAttributeValue, app_el, kAXWindowsAttribute)
    return list(wins) if isinstance(wins, (list, tuple)) else []

def window_geometry(ax_win):
    pos = _safe(AXUIElementCopyAttributeValue, ax_win, kAXPositionAttribute)
    size = _safe(AXUIElementCopyAttributeValue, ax_win, kAXSizeAttribute)
    if isinstance(pos, tuple) and isinstance(size, tuple) and len(pos)==2 and len(size)==2:
        return (float(pos[0]), float(pos[1]), float(size[0]), float(size[1]))
    return None

def cg_chrome_windows_for_pid(pid: int):
    info = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
    out = []
    for w in info or []:
        try:
            owner = w.get(kCGWindowOwnerName)
            if owner not in CHROME_OWNER_NAMES: 
                continue
            if w.get(kCGWindowOwnerPID) != pid:
                continue
            if w.get(kCGWindowLayer, 0) != 0:  # only normal windows
                continue
            b = w.get(kCGWindowBounds) or {}
            x, y = b.get("X"), b.get("Y")
            w_, h_ = b.get("Width"), b.get("Height")
            if None in (x,y,w_,h_): 
                continue
            out.append({
                "number": w.get("kCGWindowNumber"),
                "title": w.get(kCGWindowName),
                "bounds": (float(x), float(y), float(w_), float(h_)),
            })
        except Exception:
            pass
    return out

def almost_eq_rect(a, b, tol=2.0):
    return all(abs(a[i]-b[i]) <= tol for i in range(4))

def find_toolbar(root):
    q, seen = deque([root]), set()
    while q:
        el = q.popleft()
        if id(el) in seen: 
            continue
        seen.add(id(el))
        role = _safe(AXUIElementCopyAttributeValue, el, kAXRoleAttribute)
        if role == kAXToolbarRole:
            return el
        kids = _safe(AXUIElementCopyAttributeValue, el, kAXChildrenAttribute)
        if isinstance(kids, (list, tuple)):
            q.extend(kids)
    return None

# ---------- main ----------
def main():
    ensure_accessibility_trust()

    pid = get_chrome_pid()
    if not pid:
        print("❌ Chrome not found. Open a normal Chrome window and retry.", file=sys.stderr)
        sys.exit(1)

    app = app_ax(pid)

    # Try AXWindows directly
    ax_wins = enumerate_ax_windows(app)

    # If empty, use CoreGraphics to list on-screen windows and match by geometry
    cg_wins = cg_chrome_windows_for_pid(pid) if not ax_wins else []

    if not ax_wins and not cg_wins:
        print("❌ No Chrome windows found (AXWindows empty and no on-screen CG windows).", file=sys.stderr)
        print("   • Ensure a non-minimized Chrome window is visible.", file=sys.stderr)
        sys.exit(2)

    dumps_done = 0

    if ax_wins:
        # Pure-AX path: iterate every AXWindow we can see (focused or not)
        for idx, ax_win in enumerate(ax_wins):
            geom = window_geometry(ax_win)
            title = _safe(AXUIElementCopyAttributeValue, ax_win, kAXTitleAttribute)
            print(f"\n=== Window[{idx}] title={title!r} geom={geom} ===")
            tb = find_toolbar(ax_win)
            if tb:
                print_el(tb)
                dumps_done += 1
            else:
                print("  (no toolbar found under this AXWindow)")
    else:
        # CG fallback: try to pair CG windows to AX windows by bounds
        # We need to build a snapshot of any AX windows we *can* see via BFS from app.
        # (Some builds hide AXWindows attribute; we still might reach them in the tree.)
        # Build a flat list of AX nodes that look like windows (have pos/size).
        candidates = []
        q, seen = deque([app]), set()
        while q:
            el = q.popleft()
            if id(el) in seen: continue
            seen.add(id(el))
            # has geom?
            g = window_geometry(el)
            if g:
                candidates.append((el, g))
            kids = _safe(AXUIElementCopyAttributeValue, el, kAXChildrenAttribute)
            if isinstance(kids, (list, tuple)):
                q.extend(kids)

        for idx, cg in enumerate(cg_wins):
            cg_bounds = cg["bounds"]
            ax_match = None
            for el, g in candidates:
                if almost_eq_rect(g, cg_bounds):
                    ax_match = el
                    break
            print(f"\n=== CGWindow[{idx}] title={cg['title']!r} geom={cg_bounds} ===")
            if ax_match:
                tb = find_toolbar(ax_match) or find_toolbar(app)
                if tb:
                    print_el(tb)
                    dumps_done += 1
                else:
                    print("  (no toolbar found near this window)")
            else:
                print("  (no AX match for geometry; cannot dump toolbar)")

    if dumps_done == 0:
        print("\n⚠️  No toolbars dumped. Try clicking a Chrome window once, ensure it is visible, and re-run.", file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()
