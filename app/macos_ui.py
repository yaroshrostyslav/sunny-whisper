"""
macOS UI components for Sunny Whisper.
"""

import os
import sys
from AppKit import (
    NSApplication, NSStatusBar, NSVariableStatusItemLength, NSImage,
    NSObject, NSMenu, NSMenuItem, NSApplicationActivationPolicyAccessory,
    NSTextField, NSButton, NSWindow,
    NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
    NSBackingStoreBuffered,
)
from PyObjCTools import AppHelper
from config import get_config_value
from utils import log, get_base_dir

# Module-level references to prevent GC and allow updates
_shortcut_display_item = None
_menu_controller = None
_shortcut_window_controller = None

# macOS key code → pynput key name for modifier/special keys
_MODIFIER_KEY_CODES = {
    56: "shift",
    60: "shift_r",
    55: "cmd",
    54: "cmd_r",
    58: "alt",
    61: "alt_r",
    59: "ctrl",
    62: "ctrl_r",
    57: "caps_lock",
}

class KeyCaptureField(NSTextField):
    """NSTextField subclass that captures a single key press instead of typed text."""

    def initWithFrame_(self, frame):
        self = super().initWithFrame_(frame)
        if self is None:
            return None
        self._captured_key = None
        self.setEditable_(False)
        self.setSelectable_(False)
        return self

    def acceptsFirstResponder(self):
        return True

    def keyDown_(self, event):
        key_code = event.keyCode()
        name = _MODIFIER_KEY_CODES.get(key_code)
        if name is None:
            chars = event.characters()
            name = chars if chars else None
        if name:
            self._captured_key = name
            self.setStringValue_(name)

    def flagsChanged_(self, event):
        key_code = event.keyCode()
        name = _MODIFIER_KEY_CODES.get(key_code)
        if name:
            self._captured_key = name
            self.setStringValue_(name)

class ShortcutWindowController(NSObject):
    """Manages the Change Shortcut modal window."""

    def openShortcutWindow_(self, sender):
        global _shortcut_window_controller
        if _shortcut_window_controller is not None:
            if hasattr(_shortcut_window_controller, "_window"):
                _shortcut_window_controller._window.makeKeyAndOrderFront_(None)
            return
        ctrl = ShortcutWindowController.alloc().init()
        _shortcut_window_controller = ctrl
        ctrl._show()

    def _show(self):
        import listener_manager
        current_key = get_config_value("RECORD_KEYS")[0]
        listener_manager.pause()

        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((0, 0), (380, 160)),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )
        self._window.setTitle_("Change Shortcut")
        self._window.center()
        self._window.setDelegate_(self)
        self._window.setReleasedWhenClosed_(False)

        content = self._window.contentView()

        # Instruction label
        label = NSTextField.alloc().initWithFrame_(((20, 110), (340, 36)))
        label.setStringValue_("Click the field below and press a new shortcut key")
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        content.addSubview_(label)

        # Key capture field
        self._capture_field = KeyCaptureField.alloc().initWithFrame_(((20, 70), (340, 28)))
        self._capture_field.setStringValue_(current_key)
        content.addSubview_(self._capture_field)

        # Cancel button
        cancel_btn = NSButton.alloc().initWithFrame_(((185, 20), (85, 32)))
        cancel_btn.setTitle_("Cancel")
        cancel_btn.setTarget_(self)
        cancel_btn.setAction_("cancel:")
        content.addSubview_(cancel_btn)

        # Save button
        save_btn = NSButton.alloc().initWithFrame_(((280, 20), (80, 32)))
        save_btn.setTitle_("Save")
        save_btn.setTarget_(self)
        save_btn.setAction_("save:")
        content.addSubview_(save_btn)

        self._window.setDefaultButtonCell_(save_btn.cell())
        self._window.makeKeyAndOrderFront_(None)
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        self._window.makeFirstResponder_(self._capture_field)

    def save_(self, sender):
        key = self._capture_field._captured_key
        if not key:
            log("No key captured, closing without saving")
            self._window.close()
            return
        try:
            from config import update_config
            update_config("RECORD_KEYS", [key])
            _update_shortcut_display(key)
            log(f"Shortcut updated to: {key}")
        except Exception as e:
            log(f"Error saving shortcut: {e}")
        self._window.close()

    def cancel_(self, sender):
        self._window.close()

    def windowWillClose_(self, notification):
        global _shortcut_window_controller
        _shortcut_window_controller = None
        import listener_manager
        listener_manager.resume()

def _update_shortcut_display(key):
    if _shortcut_display_item:
        _shortcut_display_item.setTitle_(f"Shortcut: {key}")

class AppDelegate(NSObject):
    """Application delegate for macOS app lifecycle management."""

    def applicationShouldTerminate_(self, sender):
        log("applicationShouldTerminate_ called")
        cleanup()
        return 1  # NSTerminateNow

    def applicationWillTerminate_(self, notification):
        log("applicationWillTerminate_ called")
        cleanup()

def cleanup():
    """Clean up all application resources."""
    log("Cleanup started...")
    from audio_recorder import cleanup_recording
    cleanup_recording()
    from transcriber import cleanup_model
    cleanup_model()
    log("Cleanup finished")

def setup_app():
    """Setup and configure the macOS application."""
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)

    return app, delegate

def create_status_bar():
    """Create menu bar icon in macOS status bar."""
    global _shortcut_display_item, _menu_controller

    base_dir = get_base_dir()
    status_bar = NSStatusBar.systemStatusBar()
    status_item = status_bar.statusItemWithLength_(NSVariableStatusItemLength)

    if getattr(sys, "frozen", False):
        icon_path = os.path.join(base_dir, "icon-menu-bar.png")
    else:
        icon_path = os.path.join(base_dir, "..", "icons", "icon-menu-bar.png")
    icon = NSImage.alloc().initByReferencingFile_(icon_path)
    icon.setSize_((18, 18))
    status_item.button().setImage_(icon)

    menu = NSMenu.alloc().init()

    # Current shortcut display (non-interactive)
    current_key = get_config_value("RECORD_KEYS")[0]
    _shortcut_display_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        f"Shortcut: {current_key}", None, ""
    )
    _shortcut_display_item.setEnabled_(False)
    menu.addItem_(_shortcut_display_item)

    # Change Shortcut
    _menu_controller = ShortcutWindowController.alloc().init()
    change_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Change Shortcut", "openShortcutWindow:", ""
    )
    change_item.setTarget_(_menu_controller)
    menu.addItem_(change_item)

    menu.addItem_(NSMenuItem.separatorItem())

    # Quit
    quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "terminate:", "q")
    menu.addItem_(quit_item)

    status_item.setMenu_(menu)
    return status_item

def run_event_loop():
    """Run the main application event loop."""
    AppHelper.runEventLoop()
