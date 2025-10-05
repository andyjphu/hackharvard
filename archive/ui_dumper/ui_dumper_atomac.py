#!/usr/bin/env python3
import time

# Prefer maintained fork 'atomacos'; fall back to legacy name if present
try:
    import atomacos as atomac
except ImportError:
    import atomac  # legacy

BUNDLE_ID = "com.google.Chrome"  # or "com.brave.Browser"

def main():
    app = atomac.getAppRefByBundleId(BUNDLE_ID)
    if not app:
        raise SystemExit("Chrome not found. Is it running?")

    # Bring to front
    app.activate()
    time.sleep(0.25)

    # Pick a usable window
    wins = [w for w in app.windows()
            if getattr(w, "AXRole", None) == "AXWindow"
            and getattr(w, "AXMinimized", False) is not True]
    if not wins:
        raise SystemExit("No Chrome windows found.")

    win = next((w for w in wins if getattr(w, "AXMain", False)), wins[0])
    try:
        win.AXMain = True
    except Exception:
        pass

    # Find toolbar (may be None on some builds)
    tb = win.findFirstR(AXRole="AXToolbar")
    if not tb:
        raise SystemExit("No AXToolbar found. Try enabling Chrome accessibility: chrome://accessibility → Global.")

    print("Toolbar buttons:")
    buttons = tb.findAllR(AXRole="AXButton") or []
    if not buttons:
        print("(none)")
        return

    for b in buttons:
        title = (getattr(b, "AXTitle", None) or "").strip()
        desc  = (getattr(b, "AXDescription", None) or "").strip()
        print(f"- {title or '(no title)'} | {desc or '(no desc)'}")

if __name__ == "__main__":
    main()
