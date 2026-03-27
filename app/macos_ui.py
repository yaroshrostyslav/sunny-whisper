"""
macOS UI components for Sunny Whisper.
"""

import os
import sys
from AppKit import (
    NSApplication, NSStatusBar, NSVariableStatusItemLength, NSImage,
    NSObject, NSMenu, NSMenuItem, NSApplicationActivationPolicyAccessory,
    NSTextField, NSButton, NSWindow, NSPopUpButton,
    NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
    NSBackingStoreBuffered, NSAffineTransform, NSCompositingOperationSourceOver,
)
from Foundation import NSTimer
from PyObjCTools import AppHelper
from config import get_config_value
from utils import log, get_base_dir

# Language options: (display_name, config_value)
_LANGUAGE_OPTIONS = [
    ("Not selected", "Not selected"),
    ("English", "en"),
    ("Russian", "ru"),
    ("Ukrainian", "uk"),
]
_LANGUAGE_DISPLAY = {v: name for name, v in _LANGUAGE_OPTIONS}

# Module-level references to prevent GC and allow updates
_shortcut_display_item = None
_language_display_item = None
_menu_controller = None
_language_menu_controller = None
_shortcut_window_controller = None
_language_window_controller = None
_status_button = None

_ICON_STATES = {
    "idle": ("icon-menu-bar.png", (18, 18)),
    "recording": ("icon-recording.png", (23, 23)),
}
_LOADER_SIZE = (22, 22)
_LOADER_STEP = 4  # degrees per tick
_LOADER_INTERVAL = 0.016  # seconds per tick (~60fps, full rotation in ~1.5s)

_loader_base_image = None
_loader_angle = 0.0
_loader_timer = None

class _LoaderAnimator(NSObject):
    def tick_(self, timer):
        global _loader_angle
        if _status_button is None or _loader_base_image is None:
            return
        _loader_angle = (_loader_angle - _LOADER_STEP) % 360
        _status_button.setImage_(_rotated_image(_loader_base_image, _loader_angle))

_loader_animator = _LoaderAnimator.alloc().init()

def _rotated_image(source, degrees):
    """Return a new NSImage that is source rotated by degrees."""
    w, h = _LOADER_SIZE
    rotated = NSImage.alloc().initWithSize_((w, h))
    rotated.lockFocus()
    t = NSAffineTransform.transform()
    t.translateXBy_yBy_(w / 2, h / 2)
    t.rotateByDegrees_(degrees)
    t.translateXBy_yBy_(-w / 2, -h / 2)
    t.concat()
    source.drawAtPoint_fromRect_operation_fraction_(
        (0, 0), ((0, 0), (0, 0)), NSCompositingOperationSourceOver, 1.0
    )
    rotated.unlockFocus()
    return rotated

def _start_loader_animation():
    global _loader_base_image, _loader_angle, _loader_timer
    base_dir = get_base_dir()
    if getattr(sys, "frozen", False):
        icon_path = os.path.join(base_dir, "icon-loader.png")
    else:
        icon_path = os.path.join(base_dir, "..", "icons", "icon-loader.png")
    _loader_base_image = NSImage.alloc().initByReferencingFile_(icon_path)
    _loader_base_image.setSize_(_LOADER_SIZE)
    _loader_angle = 0.0
    _loader_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
        _LOADER_INTERVAL, _loader_animator, "tick:", None, True
    )

def _stop_loader_animation():
    global _loader_timer, _loader_base_image
    if _loader_timer is not None:
        _loader_timer.invalidate()
        _loader_timer = None
    _loader_base_image = None

def set_status_icon(state):
    """Switch status bar icon. Safe to call from any thread."""
    AppHelper.callAfter(_set_status_icon_main, state)

def _set_status_icon_main(state):
    if _status_button is None:
        return
    _stop_loader_animation()
    if state == "transcribing":
        _start_loader_animation()
        return
    filename, size = _ICON_STATES.get(state, _ICON_STATES["idle"])
    base_dir = get_base_dir()
    if getattr(sys, "frozen", False):
        icon_path = os.path.join(base_dir, filename)
    else:
        icon_path = os.path.join(base_dir, "..", "icons", filename)
    icon = NSImage.alloc().initByReferencingFile_(icon_path)
    icon.setSize_(size)
    _status_button.setImage_(icon)

class KeyCaptureField(NSTextField):
    """NSTextField subclass that displays a captured key name (read-only)."""

    def initWithFrame_(self, frame):
        self = super().initWithFrame_(frame)
        if self is None:
            return None
        self._captured_key = None
        self.setEditable_(False)
        self.setSelectable_(False)
        return self

    def updateKey_(self, key_name):
        """Update displayed key. Called on main thread via AppHelper.callAfter."""
        self._captured_key = key_name
        self.setStringValue_(key_name)

class ShortcutWindowController(NSObject):
    """Manages the Change Shortcut modal window."""

    def openShortcutWindow_(self, sender):
        global _shortcut_window_controller
        if _shortcut_window_controller is not None:
            _shortcut_window_controller._window.makeKeyAndOrderFront_(None)
            return
        ctrl = ShortcutWindowController.alloc().init()
        _shortcut_window_controller = ctrl
        ctrl._show()

    def _start_capture_listener(self):
        import listener_manager
        field = self._capture_field

        def on_press(key):
            name = getattr(key, 'name', None) or getattr(key, 'char', None)
            if name:
                AppHelper.callAfter(field.updateKey_, name)

        listener_manager.set_capture_callback(on_press)

    def _stop_capture_listener(self):
        import listener_manager
        listener_manager.clear_capture_callback()

    def _show(self):
        current_key = get_config_value("RECORD_KEYS")[0]

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
        label.setStringValue_("Press a new shortcut key: ")
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
        self._start_capture_listener()

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
        self._stop_capture_listener()
        AppHelper.callAfter(_clear_window_controller)

def _clear_window_controller():
    global _shortcut_window_controller
    _shortcut_window_controller = None

class LanguageWindowController(NSObject):
    """Manages the Change Language modal window."""

    def openLanguageWindow_(self, sender):
        global _language_window_controller
        if _language_window_controller is not None:
            _language_window_controller._window.makeKeyAndOrderFront_(None)
            return
        ctrl = LanguageWindowController.alloc().init()
        _language_window_controller = ctrl
        ctrl._show()

    def _show(self):
        import listener_manager
        current_lang = get_config_value("language")

        # Pause recording while window is open
        listener_manager.set_capture_callback(lambda key: None)

        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((0, 0), (380, 160)),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )
        self._window.setTitle_("Change Recognition Language")
        self._window.center()
        self._window.setDelegate_(self)
        self._window.setReleasedWhenClosed_(False)

        content = self._window.contentView()

        label = NSTextField.alloc().initWithFrame_(((20, 110), (340, 36)))
        label.setStringValue_("Select the language used for speech recognition")
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        content.addSubview_(label)

        self._popup = NSPopUpButton.alloc().initWithFrame_(((20, 70), (340, 28)))
        for display_name, _ in _LANGUAGE_OPTIONS:
            self._popup.addItemWithTitle_(display_name)
        current_display = _LANGUAGE_DISPLAY.get(current_lang, "Not selected")
        self._popup.selectItemWithTitle_(current_display)
        content.addSubview_(self._popup)

        cancel_btn = NSButton.alloc().initWithFrame_(((185, 20), (85, 32)))
        cancel_btn.setTitle_("Cancel")
        cancel_btn.setTarget_(self)
        cancel_btn.setAction_("cancel:")
        content.addSubview_(cancel_btn)

        save_btn = NSButton.alloc().initWithFrame_(((280, 20), (80, 32)))
        save_btn.setTitle_("Save")
        save_btn.setTarget_(self)
        save_btn.setAction_("save:")
        content.addSubview_(save_btn)

        self._window.setDefaultButtonCell_(save_btn.cell())
        self._window.makeKeyAndOrderFront_(None)
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)

    def save_(self, sender):
        selected_title = self._popup.titleOfSelectedItem()
        lang_value = next(
            (v for name, v in _LANGUAGE_OPTIONS if name == selected_title),
            "Not selected",
        )
        try:
            from config import update_config
            update_config("language", lang_value)
            _update_language_display(lang_value)
            log(f"Language updated to: {lang_value}")
        except Exception as e:
            log(f"Error saving language: {e}")
        self._window.close()

    def cancel_(self, sender):
        self._window.close()

    def windowWillClose_(self, notification):
        import listener_manager
        listener_manager.clear_capture_callback()
        AppHelper.callAfter(_clear_language_window_controller)

def _clear_language_window_controller():
    global _language_window_controller
    _language_window_controller = None

def _update_language_display(lang_value):
    if _language_display_item:
        display = _LANGUAGE_DISPLAY.get(lang_value, "Not selected")
        _language_display_item.setTitle_(f"Language: {display}")

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
    global _shortcut_display_item, _language_display_item, _menu_controller, _language_menu_controller, _status_button

    base_dir = get_base_dir()
    status_bar = NSStatusBar.systemStatusBar()
    status_item = status_bar.statusItemWithLength_(NSVariableStatusItemLength)

    _status_button = status_item.button()

    if getattr(sys, "frozen", False):
        icon_path = os.path.join(base_dir, "icon-menu-bar.png")
    else:
        icon_path = os.path.join(base_dir, "..", "icons", "icon-menu-bar.png")
    icon = NSImage.alloc().initByReferencingFile_(icon_path)
    icon.setSize_((18, 18))
    _status_button.setImage_(icon)

    menu = NSMenu.alloc().init()

    # Language display (non-interactive)
    current_lang = get_config_value("language")
    lang_display = _LANGUAGE_DISPLAY.get(current_lang, "Not selected")
    _language_display_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        f"Language: {lang_display}", None, ""
    )
    _language_display_item.setEnabled_(False)
    menu.addItem_(_language_display_item)

    # Change Language
    _language_menu_controller = LanguageWindowController.alloc().init()
    change_lang_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Change Language", "openLanguageWindow:", ""
    )
    change_lang_item.setTarget_(_language_menu_controller)
    menu.addItem_(change_lang_item)

    # Shortcut display (non-interactive)
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

    # Quit
    quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "terminate:", "q")
    menu.addItem_(quit_item)

    status_item.setMenu_(menu)
    return status_item

def run_event_loop():
    """Run the main application event loop."""
    AppHelper.runEventLoop()
