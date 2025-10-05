#!/usr/bin/env python3
"""
macOS System Settings Mapping
Maps user prompts to System Settings panels and their interactive elements
"""

# Comprehensive mapping of macOS System Settings
MACOS_SETTINGS_MAP = {
    # Appearance & Display
    "appearance": {
        "panel": "Appearance",
        "keywords": ["appearance", "theme", "dark mode", "light mode", "accent color"],
        "elements": {
            "light_mode": "Light appearance button",
            "dark_mode": "Dark appearance button",
            "auto_mode": "Auto appearance button",
            "accent_color": "Accent color dropdown",
            "highlight_color": "Highlight color dropdown",
            "sidebar_icon_size": "Sidebar icon size dropdown",
            "show_scroll_bars": "Show scroll bars dropdown",
            "click_scroll_bar": "Click in scroll bar dropdown",
        },
    },
    # Wi-Fi & Network
    "wifi": {
        "panel": "Wi-Fi",
        "keywords": ["wifi", "wi-fi", "wireless", "network", "internet connection"],
        "elements": {
            "wifi_toggle": "Wi-Fi on/off toggle",
            "network_list": "Available networks list",
            "details_button": "Details button",
            "advanced_button": "Advanced button",
        },
    },
    "network": {
        "panel": "Network",
        "keywords": ["network", "ethernet", "vpn", "proxy"],
        "elements": {
            "ethernet": "Ethernet connection",
            "vpn": "VPN configuration",
            "firewall": "Firewall settings",
        },
    },
    # Bluetooth
    "bluetooth": {
        "panel": "Bluetooth",
        "keywords": ["bluetooth", "wireless devices", "pairing"],
        "elements": {
            "bluetooth_toggle": "Bluetooth on/off toggle",
            "devices_list": "Paired devices list",
            "connect_button": "Connect button",
        },
    },
    # Sound
    "sound": {
        "panel": "Sound",
        "keywords": ["sound", "audio", "volume", "speakers", "microphone"],
        "elements": {
            "output_device": "Output device dropdown",
            "input_device": "Input device dropdown",
            "output_volume": "Output volume slider",
            "input_volume": "Input volume slider",
            "play_sound_on_startup": "Play sound on startup checkbox",
            "play_feedback": "Play feedback checkbox",
        },
    },
    # Focus & Notifications
    "focus": {
        "panel": "Focus",
        "keywords": ["focus", "do not disturb", "dnd", "concentration"],
        "elements": {
            "do_not_disturb": "Do Not Disturb toggle",
            "personal": "Personal focus",
            "work": "Work focus",
            "sleep": "Sleep focus",
        },
    },
    "notifications": {
        "panel": "Notifications",
        "keywords": ["notifications", "alerts", "banners"],
        "elements": {
            "show_previews": "Show previews dropdown",
            "allow_notifications": "Allow notifications toggle",
            "app_notifications": "Per-app notification settings",
        },
    },
    # Display
    "displays": {
        "panel": "Displays",
        "keywords": ["display", "monitor", "screen", "resolution", "brightness"],
        "elements": {
            "brightness": "Brightness slider",
            "resolution": "Resolution dropdown",
            "refresh_rate": "Refresh rate dropdown",
            "night_shift": "Night Shift toggle",
            "true_tone": "True Tone toggle",
            "auto_brightness": "Automatically adjust brightness checkbox",
        },
    },
    # Battery & Energy
    "battery": {
        "panel": "Battery",
        "keywords": ["battery", "power", "energy", "low power mode", "power saver"],
        "elements": {
            "low_power_mode": "Low Power Mode dropdown",
            "battery_percentage": "Show battery percentage checkbox",
            "optimize_video_streaming": "Optimize video streaming checkbox",
            "power_adapter": "Power adapter settings",
            "battery_health": "Battery health info",
        },
    },
    # Screen Saver & Lock Screen
    "screen_saver": {
        "panel": "Screen Saver",
        "keywords": ["screen saver", "screensaver", "idle"],
        "elements": {
            "screen_saver_dropdown": "Screen saver style dropdown",
            "start_after": "Start after dropdown",
            "show_with_clock": "Show with clock checkbox",
        },
    },
    "lock_screen": {
        "panel": "Lock Screen",
        "keywords": ["lock screen", "login", "password", "auto lock"],
        "elements": {
            "require_password": "Require password dropdown",
            "show_message": "Show message checkbox",
            "lock_message": "Lock message text field",
        },
    },
    # Touch ID & Password
    "touch_id": {
        "panel": "Touch ID & Password",
        "keywords": ["touch id", "fingerprint", "biometric", "password"],
        "elements": {
            "add_fingerprint": "Add fingerprint button",
            "unlock_mac": "Use Touch ID to unlock checkbox",
            "apple_pay": "Use Touch ID for Apple Pay checkbox",
            "password_button": "Change password button",
        },
    },
    # Users & Groups
    "users": {
        "panel": "Users & Groups",
        "keywords": ["users", "accounts", "login", "guest"],
        "elements": {
            "current_user": "Current user",
            "add_user": "Add user button",
            "login_options": "Login options",
            "guest_user": "Guest user toggle",
        },
    },
    # Wallet & Apple Pay
    "wallet": {
        "panel": "Wallet & Apple Pay",
        "keywords": ["wallet", "apple pay", "payment", "cards"],
        "elements": {
            "add_card": "Add card button",
            "cards_list": "Saved cards list",
            "default_card": "Default card dropdown",
        },
    },
    # Internet Accounts
    "internet_accounts": {
        "panel": "Internet Accounts",
        "keywords": ["email", "accounts", "icloud", "google", "microsoft"],
        "elements": {
            "add_account": "Add account button",
            "accounts_list": "Accounts list",
            "account_details": "Account details",
        },
    },
    # Game Center
    "game_center": {
        "panel": "Game Center",
        "keywords": ["game center", "gaming", "games"],
        "elements": {
            "sign_in": "Sign in button",
            "profile": "Profile settings",
            "friends": "Friends list",
        },
    },
    # Passwords
    "passwords": {
        "panel": "Passwords",
        "keywords": ["passwords", "keychain", "credentials"],
        "elements": {
            "passwords_list": "Passwords list",
            "add_password": "Add password button",
            "search_passwords": "Search passwords field",
        },
    },
    # General
    "general": {
        "panel": "General",
        "keywords": ["general", "about", "software update", "storage"],
        "sub_panels": {
            "about": {
                "keywords": ["about", "mac info", "system info"],
                "elements": {
                    "name": "Computer name",
                    "overview": "System overview",
                },
            },
            "software_update": {
                "keywords": ["software update", "update", "upgrade", "macos update"],
                "elements": {
                    "check_now": "Check Now button",
                    "automatic_updates": "Automatic updates checkbox",
                },
            },
            "storage": {
                "keywords": ["storage", "disk space", "hard drive"],
                "elements": {
                    "storage_breakdown": "Storage breakdown",
                    "manage": "Manage button",
                },
            },
            "airdrop": {
                "keywords": ["airdrop", "file sharing"],
                "elements": {
                    "airdrop_dropdown": "AirDrop visibility dropdown",
                },
            },
            "login_items": {
                "keywords": ["login items", "startup", "launch at login"],
                "elements": {
                    "login_items_list": "Login items list",
                    "add_item": "Add item button",
                },
            },
            "language_region": {
                "keywords": ["language", "region", "locale"],
                "elements": {
                    "preferred_languages": "Preferred languages list",
                    "region": "Region dropdown",
                },
            },
            "date_time": {
                "keywords": ["date", "time", "clock", "timezone"],
                "elements": {
                    "set_automatically": "Set date and time automatically checkbox",
                    "timezone": "Time zone dropdown",
                    "24_hour": "24-hour time checkbox",
                },
            },
            "sharing": {
                "keywords": ["sharing", "file sharing", "screen sharing", "remote"],
                "elements": {
                    "screen_sharing": "Screen Sharing checkbox",
                    "file_sharing": "File Sharing checkbox",
                    "remote_login": "Remote Login checkbox",
                },
            },
            "time_machine": {
                "keywords": ["time machine", "backup"],
                "elements": {
                    "select_disk": "Select Backup Disk button",
                    "back_up_automatically": "Back Up Automatically checkbox",
                },
            },
            "transfer_reset": {
                "keywords": ["transfer", "reset", "erase", "migrate"],
                "elements": {
                    "transfer_data": "Transfer or Reset button",
                    "erase_content": "Erase All Content and Settings button",
                },
            },
        },
    },
    # Accessibility
    "accessibility": {
        "panel": "Accessibility",
        "keywords": ["accessibility", "voiceover", "zoom", "display", "hearing"],
        "sub_panels": {
            "voiceover": {
                "keywords": ["voiceover", "screen reader"],
                "elements": {
                    "voiceover_toggle": "VoiceOver toggle",
                    "voiceover_training": "VoiceOver Training button",
                },
            },
            "zoom": {
                "keywords": ["zoom", "magnify", "magnification"],
                "elements": {
                    "zoom_toggle": "Use keyboard shortcuts to zoom checkbox",
                    "zoom_style": "Zoom style dropdown",
                },
            },
            "display": {
                "keywords": ["display accessibility", "contrast", "cursor size"],
                "elements": {
                    "increase_contrast": "Increase contrast checkbox",
                    "reduce_motion": "Reduce motion checkbox",
                    "cursor_size": "Cursor size slider",
                },
            },
            "speech": {
                "keywords": ["speech", "text to speech", "speak"],
                "elements": {
                    "speak_selection": "Speak selection checkbox",
                    "speak_items": "Speak items under pointer checkbox",
                },
            },
        },
    },
    # Control Center
    "control_center": {
        "panel": "Control Center",
        "keywords": ["control center", "menu bar", "widgets"],
        "elements": {
            "wifi_menu": "Wi-Fi in menu bar dropdown",
            "bluetooth_menu": "Bluetooth in menu bar dropdown",
            "airdrop_menu": "AirDrop in menu bar dropdown",
            "focus_menu": "Focus in menu bar dropdown",
            "screen_mirroring": "Screen Mirroring in menu bar dropdown",
            "display": "Display in menu bar dropdown",
            "sound": "Sound in menu bar dropdown",
            "battery_menu": "Battery in menu bar dropdown",
        },
    },
    # Siri & Spotlight
    "siri": {
        "panel": "Siri & Spotlight",
        "keywords": ["siri", "voice assistant", "hey siri"],
        "elements": {
            "ask_siri": "Ask Siri toggle",
            "listen_for": "Listen for dropdown",
            "keyboard_shortcut": "Keyboard shortcut",
            "language": "Language dropdown",
            "siri_voice": "Siri voice dropdown",
        },
    },
    "spotlight": {
        "panel": "Siri & Spotlight",
        "keywords": ["spotlight", "search"],
        "elements": {
            "search_results": "Search results checkboxes",
            "spotlight_privacy": "Spotlight Privacy button",
        },
    },
    # Privacy & Security
    "privacy": {
        "panel": "Privacy & Security",
        "keywords": [
            "privacy",
            "security",
            "permissions",
            "location",
            "camera",
            "microphone",
        ],
        "sub_panels": {
            "location_services": {
                "keywords": ["location", "gps"],
                "elements": {
                    "location_toggle": "Location Services toggle",
                    "app_permissions": "Per-app location permissions",
                },
            },
            "camera": {
                "keywords": ["camera", "webcam"],
                "elements": {
                    "app_permissions": "Apps that can access camera",
                },
            },
            "microphone": {
                "keywords": ["microphone", "mic", "audio input"],
                "elements": {
                    "app_permissions": "Apps that can access microphone",
                },
            },
            "files_folders": {
                "keywords": ["files", "folders", "disk access"],
                "elements": {
                    "full_disk_access": "Full Disk Access list",
                },
            },
            "analytics": {
                "keywords": ["analytics", "diagnostics", "crash reports"],
                "elements": {
                    "share_analytics": "Share analytics checkbox",
                },
            },
        },
    },
    # Desktop & Dock
    "desktop_dock": {
        "panel": "Desktop & Dock",
        "keywords": ["desktop", "dock", "menu bar", "windows", "mission control"],
        "elements": {
            "dock_size": "Size slider",
            "magnification": "Magnification checkbox and slider",
            "position": "Position on screen dropdown",
            "minimize_effect": "Minimize windows using dropdown",
            "show_recent": "Show recent applications checkbox",
            "automatically_hide": "Automatically hide and show Dock checkbox",
            "show_indicators": "Show indicators for open applications checkbox",
        },
    },
    # Trackpad
    "trackpad": {
        "panel": "Trackpad",
        "keywords": ["trackpad", "touchpad", "gestures", "tap to click"],
        "elements": {
            "tap_to_click": "Tap to click checkbox",
            "tracking_speed": "Tracking speed slider",
            "force_click": "Force Click and haptic feedback checkbox",
            "natural_scrolling": "Natural scrolling checkbox",
        },
    },
    # Mouse
    "mouse": {
        "panel": "Mouse",
        "keywords": ["mouse", "pointer", "cursor", "scroll"],
        "elements": {
            "tracking_speed": "Tracking speed slider",
            "scrolling_speed": "Scrolling speed slider",
            "natural_scrolling": "Natural scrolling checkbox",
            "secondary_click": "Secondary click dropdown",
        },
    },
    # Keyboard
    "keyboard": {
        "panel": "Keyboard",
        "keywords": ["keyboard", "shortcuts", "typing", "input"],
        "elements": {
            "key_repeat_rate": "Key repeat rate slider",
            "delay_until_repeat": "Delay until repeat slider",
            "adjust_brightness": "Adjust keyboard brightness checkbox",
            "keyboard_shortcuts": "Keyboard Shortcuts button",
            "input_sources": "Input Sources button",
            "text_input": "Text Input button",
        },
    },
    # Printers & Scanners
    "printers": {
        "panel": "Printers & Scanners",
        "keywords": ["printer", "scanner", "print", "scan"],
        "elements": {
            "printers_list": "Printers list",
            "add_printer": "Add printer button",
            "default_printer": "Default printer dropdown",
        },
    },
}

# Reverse mapping: keyword -> panel
KEYWORD_TO_PANEL = {}
for panel_key, panel_data in MACOS_SETTINGS_MAP.items():
    for keyword in panel_data.get("keywords", []):
        KEYWORD_TO_PANEL[keyword.lower()] = panel_data["panel"]

    # Handle sub-panels
    if "sub_panels" in panel_data:
        for sub_key, sub_data in panel_data["sub_panels"].items():
            for keyword in sub_data.get("keywords", []):
                KEYWORD_TO_PANEL[keyword.lower()] = panel_data["panel"]


def find_settings_panel(user_prompt: str) -> dict:
    """
    Find the appropriate System Settings panel based on user prompt.

    Args:
        user_prompt: Natural language prompt from user

    Returns:
        Dict with panel name and confidence
    """
    prompt_lower = user_prompt.lower()

    # Direct keyword matching
    for keyword, panel in KEYWORD_TO_PANEL.items():
        if keyword in prompt_lower:
            return {
                "panel": panel,
                "confidence": 0.9,
                "matched_keyword": keyword,
            }

    # Fuzzy matching for common variations
    fuzzy_matches = {
        "dark": "Appearance",
        "light": "Appearance",
        "power": "Battery",
        "internet": "Wi-Fi",
        "wireless": "Wi-Fi",
        "volume": "Sound",
        "mute": "Sound",
        "update": "General",
        "backup": "General",
    }

    for fuzzy_key, panel in fuzzy_matches.items():
        if fuzzy_key in prompt_lower:
            return {
                "panel": panel,
                "confidence": 0.7,
                "matched_keyword": fuzzy_key,
            }

    return {
        "panel": None,
        "confidence": 0.0,
        "matched_keyword": None,
    }


def get_panel_elements(panel_name: str) -> dict:
    """
    Get all interactive elements for a specific panel.

    Args:
        panel_name: Name of the System Settings panel

    Returns:
        Dict with element information
    """
    for panel_key, panel_data in MACOS_SETTINGS_MAP.items():
        if panel_data["panel"] == panel_name:
            return {
                "panel": panel_name,
                "elements": panel_data.get("elements", {}),
                "sub_panels": panel_data.get("sub_panels", {}),
            }

    return {"panel": panel_name, "elements": {}, "sub_panels": {}}


if __name__ == "__main__":
    # Test the mapping
    test_prompts = [
        "turn on dark mode",
        "disable wifi",
        "turn off bluetooth",
        "enable low power mode",
        "change volume",
        "update macos",
    ]

    print("Testing Settings Mapping:")
    print("=" * 60)
    for prompt in test_prompts:
        result = find_settings_panel(prompt)
        print(f"\nPrompt: {prompt}")
        print(f"  → Panel: {result['panel']}")
        print(f"  → Confidence: {result['confidence']}")
        print(f"  → Matched: {result['matched_keyword']}")

