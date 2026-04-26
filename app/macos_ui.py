"""
macOS UI components for Sunny Whisper.
"""

import os
from AppKit import (
    NSApplication, NSStatusBar, NSVariableStatusItemLength, NSImage,
    NSObject, NSMenu, NSMenuItem, NSApplicationActivationPolicyAccessory,
    NSTextField, NSButton, NSWindow, NSPopUpButton,
    NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
    NSBackingStoreBuffered, NSAffineTransform, NSCompositingOperationSourceOver,
    NSTableView, NSTableColumn, NSScrollView, NSBezelBorder,
    NSImageView, NSWorkspace, NSTextAlignmentCenter,
)
from Foundation import NSTimer
from PyObjCTools import AppHelper
from config import get_config_value, GITHUB_URL, get_icons_dir, log

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
_dictionary_window_controller = None
_dictionary_menu_controller = None
_statistics_window_controller = None
_statistics_menu_controller = None
_about_window_controller = None
_about_menu_controller = None
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
    rotated.setTemplate_(True)
    return rotated

def _start_loader_animation():
    global _loader_base_image, _loader_angle, _loader_timer
    icon_path = os.path.join(get_icons_dir(), "icon-loader.png")
    _loader_base_image = NSImage.alloc().initByReferencingFile_(icon_path)
    _loader_base_image.setSize_(_LOADER_SIZE)
    _loader_base_image.setTemplate_(True)
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
    icon_path = os.path.join(get_icons_dir(), filename)
    icon = NSImage.alloc().initByReferencingFile_(icon_path)
    icon.setSize_(size)
    icon.setTemplate_(True)
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
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
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
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
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


class DictionaryWindowController(NSObject):
    """Manages the Custom Dictionary modal window."""

    def openDictionaryWindow_(self, sender):
        global _dictionary_window_controller
        if _dictionary_window_controller is not None:
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            _dictionary_window_controller._window.makeKeyAndOrderFront_(None)
            return
        ctrl = DictionaryWindowController.alloc().init()
        _dictionary_window_controller = ctrl
        ctrl._show()

    def _show(self):
        import listener_manager
        from config import get_config_value
        self._words = list(get_config_value("dictionary"))

        listener_manager.set_capture_callback(lambda key: None)

        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((0, 0), (380, 420)),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )
        self._window.setTitle_("Custom Dictionary")
        self._window.center()
        self._window.setDelegate_(self)
        self._window.setReleasedWhenClosed_(False)

        content = self._window.contentView()

        # Instruction label
        label = NSTextField.alloc().initWithFrame_(((20, 375), (340, 32)))
        label.setStringValue_("Add words to improve recognition accuracy or provide a style example")
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        label.cell().setWraps_(True)
        content.addSubview_(label)

        # Add word field + button
        self._add_field = NSTextField.alloc().initWithFrame_(((20, 335), (260, 28)))
        self._add_field.setPlaceholderString_("New word...")
        self._add_field.setTarget_(self)
        self._add_field.setAction_("addWord:")
        content.addSubview_(self._add_field)

        add_btn = NSButton.alloc().initWithFrame_(((290, 335), (70, 28)))
        add_btn.setTitle_("Add")
        add_btn.setTarget_(self)
        add_btn.setAction_("addWord:")
        content.addSubview_(add_btn)

        # Table inside scroll view
        scroll = NSScrollView.alloc().initWithFrame_(((20, 80), (340, 240)))
        scroll.setHasVerticalScroller_(True)
        scroll.setBorderType_(NSBezelBorder)
        scroll.setAutohidesScrollers_(True)

        self._table = NSTableView.alloc().initWithFrame_(((0, 0), (340, 240)))
        self._table.setAllowsMultipleSelection_(False)
        self._table.setUsesAlternatingRowBackgroundColors_(True)
        col = NSTableColumn.alloc().initWithIdentifier_("word")
        col.setWidth_(320)
        col.setEditable_(True)
        col.headerCell().setStringValue_("Word")
        self._table.addTableColumn_(col)
        self._table.setDataSource_(self)
        self._table.setDelegate_(self)

        scroll.setDocumentView_(self._table)
        content.addSubview_(scroll)

        # Remove button (right-aligned, above table)
        remove_btn = NSButton.alloc().initWithFrame_(((285, 48), (75, 26)))
        remove_btn.setTitle_("Remove")
        remove_btn.setTarget_(self)
        remove_btn.setAction_("removeWord:")
        content.addSubview_(remove_btn)

        # Cancel / Save buttons
        cancel_btn = NSButton.alloc().initWithFrame_(((185, 15), (85, 32)))
        cancel_btn.setTitle_("Cancel")
        cancel_btn.setTarget_(self)
        cancel_btn.setAction_("cancel:")
        content.addSubview_(cancel_btn)

        save_btn = NSButton.alloc().initWithFrame_(((280, 15), (80, 32)))
        save_btn.setTitle_("Save")
        save_btn.setTarget_(self)
        save_btn.setAction_("save:")
        content.addSubview_(save_btn)

        self._window.setDefaultButtonCell_(save_btn.cell())
        self._window.makeKeyAndOrderFront_(None)
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)

    # NSTableViewDataSource
    def numberOfRowsInTableView_(self, tv):
        return len(self._words)

    def tableView_objectValueForTableColumn_row_(self, tv, col, row):
        if 0 <= row < len(self._words):
            return self._words[row]
        return ""

    def tableView_setObjectValue_forTableColumn_row_(self, tv, value, col, row):
        if value and 0 <= row < len(self._words):
            self._words[row] = value.strip()

    def addWord_(self, sender):
        word = self._add_field.stringValue().strip()
        if word and word not in self._words and len(self._words) < 100:
            self._words.append(word)
            self._table.reloadData()
            self._add_field.setStringValue_("")

    def removeWord_(self, sender):
        row = self._table.selectedRow()
        if row >= 0:
            del self._words[row]
            self._table.reloadData()

    def save_(self, sender):
        seen = set()
        clean = []
        for w in self._words:
            w = w.strip()
            if w and w not in seen and len(clean) < 100:
                seen.add(w)
                clean.append(w)
        try:
            from config import update_config
            update_config("dictionary", clean)
            log(f"Dictionary saved: {len(clean)} words")
        except Exception as e:
            log(f"Error saving dictionary: {e}")
        self._window.close()

    def cancel_(self, sender):
        self._window.close()

    def windowWillClose_(self, notification):
        import listener_manager
        listener_manager.clear_capture_callback()
        AppHelper.callAfter(_clear_dictionary_window_controller)


def _clear_dictionary_window_controller():
    global _dictionary_window_controller
    _dictionary_window_controller = None


class StatisticsWindowController(NSObject):
    """Manages the Statistics window."""

    def openStatisticsWindow_(self, sender):
        global _statistics_window_controller
        if _statistics_window_controller is not None:
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            _statistics_window_controller._window.makeKeyAndOrderFront_(None)
            return
        ctrl = StatisticsWindowController.alloc().init()
        _statistics_window_controller = ctrl
        ctrl._show()

    def _show(self):
        import listener_manager
        from stats import get_today, get_this_week, get_all_time

        listener_manager.set_capture_callback(lambda key: None)

        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((0, 0), (380, 160)),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )
        self._window.setTitle_("Statistics")
        self._window.center()
        self._window.setDelegate_(self)
        self._window.setReleasedWhenClosed_(False)

        content = self._window.contentView()

        def _label(frame, text):
            lbl = NSTextField.alloc().initWithFrame_(frame)
            lbl.setStringValue_(text)
            lbl.setBezeled_(False)
            lbl.setDrawsBackground_(False)
            lbl.setEditable_(False)
            lbl.setSelectable_(False)
            return lbl

        content.addSubview_(_label(((20, 115), (340, 24)), f"Today: {get_today()} words"))
        content.addSubview_(_label(((20, 82), (340, 24)), f"This week: {get_this_week()} words"))
        content.addSubview_(_label(((20, 49), (340, 24)), f"All time: {get_all_time()} words"))

        close_btn = NSButton.alloc().initWithFrame_(((280, 15), (80, 32)))
        close_btn.setTitle_("Close")
        close_btn.setTarget_(self)
        close_btn.setAction_("close:")
        content.addSubview_(close_btn)

        self._window.setDefaultButtonCell_(close_btn.cell())
        self._window.makeKeyAndOrderFront_(None)
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)

    def close_(self, sender):
        self._window.close()

    def windowWillClose_(self, notification):
        import listener_manager
        listener_manager.clear_capture_callback()
        AppHelper.callAfter(_clear_statistics_window_controller)


def _clear_statistics_window_controller():
    global _statistics_window_controller
    _statistics_window_controller = None


class AboutWindowController(NSObject):
    """Manages the About window."""

    def openAboutWindow_(self, sender):
        global _about_window_controller
        if _about_window_controller is not None:
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            _about_window_controller._window.makeKeyAndOrderFront_(None)
            return
        ctrl = AboutWindowController.alloc().init()
        _about_window_controller = ctrl
        ctrl._show()

    def _show(self):
        w, h = 300, 260
        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((0, 0), (w, h)),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )
        self._window.setTitle_("About")
        self._window.center()
        self._window.setDelegate_(self)
        self._window.setReleasedWhenClosed_(False)

        content = self._window.contentView()

        # Logo
        icon_path = os.path.join(get_icons_dir(), "icon.png")
        icon = NSImage.alloc().initByReferencingFile_(icon_path)
        icon.setSize_((80, 80))
        icon_view = NSImageView.alloc().initWithFrame_(((w // 2 - 40, 160), (80, 80)))
        icon_view.setImage_(icon)
        content.addSubview_(icon_view)

        def _centered_label(y, text, size=13):
            lbl = NSTextField.alloc().initWithFrame_(((0, y), (w, 24)))
            lbl.setStringValue_(text)
            lbl.setBezeled_(False)
            lbl.setDrawsBackground_(False)
            lbl.setEditable_(False)
            lbl.setSelectable_(False)
            lbl.setAlignment_(NSTextAlignmentCenter)
            lbl.setFont_(lbl.font().fontWithSize_(size))
            return lbl

        from config import APP_VERSION, GIT_COMMIT
        content.addSubview_(_centered_label(125, "Sunny Whisper", size=16))
        version_str = f"Version {APP_VERSION} ({GIT_COMMIT})" if GIT_COMMIT else f"Version {APP_VERSION}"
        content.addSubview_(_centered_label(98, version_str))

        # GitHub button
        github_btn = NSButton.alloc().initWithFrame_(((w // 2 - 55, 25), (110, 30)))
        github_btn.setTitle_("GitHub")
        github_btn.setTarget_(self)
        github_btn.setAction_("openGithub:")
        content.addSubview_(github_btn)

        self._window.makeKeyAndOrderFront_(None)
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)

    def openGithub_(self, sender):
        from Foundation import NSURL
        url = NSURL.URLWithString_(GITHUB_URL)
        NSWorkspace.sharedWorkspace().openURL_(url)

    def windowWillClose_(self, notification):
        AppHelper.callAfter(_clear_about_window_controller)


def _clear_about_window_controller():
    global _about_window_controller
    _about_window_controller = None


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
    global _shortcut_display_item, _language_display_item, _menu_controller, _language_menu_controller, _status_button, _dictionary_menu_controller, _statistics_menu_controller, _about_menu_controller

    status_bar = NSStatusBar.systemStatusBar()
    status_item = status_bar.statusItemWithLength_(NSVariableStatusItemLength)

    _status_button = status_item.button()

    icon_path = os.path.join(get_icons_dir(), "icon-menu-bar.png")
    icon = NSImage.alloc().initByReferencingFile_(icon_path)
    icon.setSize_((18, 18))
    icon.setTemplate_(True)
    _status_button.setImage_(icon)

    menu = NSMenu.alloc().init()

    # Shortcut display (non-interactive)
    current_key = get_config_value("RECORD_KEYS")[0]
    _shortcut_display_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        f"Shortcut: {current_key}", None, ""
    )
    _shortcut_display_item.setEnabled_(False)
    menu.addItem_(_shortcut_display_item)

    # Language display (non-interactive)
    current_lang = get_config_value("language")
    lang_display = _LANGUAGE_DISPLAY.get(current_lang, "Not selected")
    _language_display_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        f"Language: {lang_display}", None, ""
    )
    _language_display_item.setEnabled_(False)
    menu.addItem_(_language_display_item)

    # Change Shortcut
    _menu_controller = ShortcutWindowController.alloc().init()
    change_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Change Shortcut", "openShortcutWindow:", ""
    )
    change_item.setTarget_(_menu_controller)
    menu.addItem_(change_item)

    # Change Language
    _language_menu_controller = LanguageWindowController.alloc().init()
    change_lang_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Change Language", "openLanguageWindow:", ""
    )
    change_lang_item.setTarget_(_language_menu_controller)
    menu.addItem_(change_lang_item)

    # Change Dictionary
    _dictionary_menu_controller = DictionaryWindowController.alloc().init()
    dict_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Change Dictionary", "openDictionaryWindow:", ""
    )
    dict_item.setTarget_(_dictionary_menu_controller)
    menu.addItem_(dict_item)

    # Statistics
    _statistics_menu_controller = StatisticsWindowController.alloc().init()
    stats_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Statistics", "openStatisticsWindow:", ""
    )
    stats_item.setTarget_(_statistics_menu_controller)
    menu.addItem_(stats_item)

    # About
    _about_menu_controller = AboutWindowController.alloc().init()
    about_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "About", "openAboutWindow:", ""
    )
    about_item.setTarget_(_about_menu_controller)
    menu.addItem_(about_item)

    # Quit
    quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "terminate:", "q")
    menu.addItem_(quit_item)

    status_item.setMenu_(menu)
    return status_item

def run_event_loop():
    """Run the main application event loop."""
    AppHelper.runEventLoop()
