"""
macOS UI components for Sunny Whisper.
"""

import os
from AppKit import NSApplication, NSStatusBar, NSVariableStatusItemLength, NSImage, NSObject
from PyObjCTools import AppHelper
from utils import log, get_base_dir

class AppDelegate(NSObject):
    """Application delegate for macOS app lifecycle management."""

    def applicationShouldTerminate_(self, sender):
        """Handle application termination request."""
        log("applicationShouldTerminate_ called")
        cleanup()
        return 1  # NSTerminateNow

    def applicationWillTerminate_(self, notification):
        """Handle application will terminate event."""
        log("applicationWillTerminate_ called")
        cleanup()

def cleanup():
    """Clean up all application resources."""
    log("Cleanup started...")
    # Clean up recording resources
    from audio_recorder import cleanup_recording
    cleanup_recording()
    # Clean up model resources
    from transcriber import cleanup_model
    cleanup_model()
    log("Cleanup finished")

def setup_app():
    """Setup and configure the macOS application."""
    app = NSApplication.sharedApplication()
    
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    
    return app, delegate

def create_menu_bar():
    """Create menu bar icon in macOS status bar."""
    base_dir = get_base_dir()
    status_bar = NSStatusBar.systemStatusBar()
    status_item = status_bar.statusItemWithLength_(NSVariableStatusItemLength)

    icon_path = os.path.join(base_dir, "icon-menu-bar.png")
    icon = NSImage.alloc().initByReferencingFile_(icon_path)
    icon.setSize_((18, 18))

    status_item.button().setImage_(icon)

    return status_item

def run_event_loop():
    """Run the main application event loop."""
    AppHelper.runEventLoop()
