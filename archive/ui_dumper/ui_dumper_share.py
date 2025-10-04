#!/usr/bin/env python3
# Requires: pip install pyatomac (or atomacos)
import time, sys
import atomac  # pyatomac import name

BUNDLE_ID = "com.google.Chrome"

def get_chrome():
    try:
        return atomac.getAppRefByBundleId(BUNDLE_ID)
    except Exception:
        # Fallback by localized name
        return atomac.getAppRefByLocalizedName("Google Chrome")

def bring_front(app):
    try:
        app.activate()
        time.sleep(0.2)
    except Exception:
        pass

def first_window(app):
    wins = [w for w in app.windows() if getattr(w, "AXRole", None) == "AXWindow"]
    if not wins:
        sys.exit("No Chrome windows found.")
    # Prefer the main/front window if marked
    mains = [w for w in wins if getattr(w, "AXMain", False)]
    return mains[0] if mains else wins[0]

def focus_first_tab(win):
    tg = win.findFirstR(AXRole="AXTabGroup")
    if not tg: 
        return
    tabs = tg.findAllR(AXRole="AXTab")
    if not tabs:
        return
    try:
        tabs[0].AXPress()
        time.sleep(0.1)
    except Exception:
        pass

def find_share_button_in_toolbar(win):
    tb = win.findFirstR(AXRole="AXToolbar")
    if not tb:
        return None
    buttons = tb.findAllR(AXRole="AXButton") or []
    for b in buttons:
        title = (getattr(b, "AXTitle", None) or "").strip()
        desc  = (getattr(b, "AXDescription", None) or "").strip()
        name  = f"{title} {desc}".lower()
        if "share" in name:
            return b
    return None

def find_share_button_anywhere(win):
    # Try some common attribute combos
    for kwargs in (
        {"AXRole":"AXButton", "AXTitle":"Share"},
        {"AXRole":"AXButton", "AXDescription":"Share"},
    ):
        try:
            el = win.findFirstR(**kwargs)
            if el: 
                return el
        except Exception:
            pass
    return None

def press_file_share_menu(app):
    try:
        menubar = app.menuBar()
        if not menubar:
            return False
        file_item = menubar.findFirstR(AXRole="AXMenuBarItem", AXTitle="File")
        if not file_item:
            return False
        file_item.AXPress()
        time.sleep(0.1)

        # The first AXChild should be the File menu
        menus = file_item.AXChildren or []
        if not menus:
            return False
        file_menu = menus[0]

        # Look for "Share" or items that start with "Share"
        items = file_menu.findAllR(AXRole="AXMenuItem") or []
        for it in items:
            title = (getattr(it, "AXTitle", None) or "").strip()
            if title.lower().startswith("share"):
                it.AXPress()
                return True
    except Exception:
        pass
    return False

def main():
    app = get_chrome()
    if not app:
        sys.exit("Chrome not found (is it running?).")

    bring_front(app)
    win = first_window(app)
    # Mark as main/front if possible
    try:
        win.AXMain = True
    except Exception:
        pass

    # Ensure we're on the first tab
    focus_first_tab(win)

    # Try toolbar button first
    share = find_share_button_in_toolbar(win)
    if not share:
        share = find_share_button_anywhere(win)

    if share:
        try:
            share.AXPress()
            print("✅ Pressed the Share button.")
            return
        except Exception as e:
            print(f"Found Share but failed to press: {e}")

    # Fallback: File → Share…
    if press_file_share_menu(app):
        print("✅ Invoked File → Share… from the menu.")
        return

    sys.exit("❌ Could not find a Share control. Try enabling Chrome accessibility or switch Chrome UI language to English.")

if __name__ == "__main__":
    main()
