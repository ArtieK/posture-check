#!/usr/bin/env python3
"""
Stretch Reminder - A macOS menu bar app that reminds you to stretch every 20 minutes.
Uses PyObjC directly for better macOS compatibility.
"""

import objc
from Foundation import NSObject, NSTimer, NSRunLoop, NSDefaultRunLoopMode
from AppKit import (
    NSApplication,
    NSStatusBar,
    NSMenu,
    NSMenuItem,
    NSVariableStatusItemLength,
    NSApplicationActivationPolicyAccessory,
)
import UserNotifications

# Configuration
REMINDER_INTERVAL_SECONDS = 1 * 60  # 1 minute for testing (change to 20 * 60 for production)
CHECK_INTERVAL_SECONDS = 5          # How often to check/update timer


class StretchReminderApp(NSObject):
    def init(self):
        self = objc.super(StretchReminderApp, self).init()
        if self is None:
            return None

        self.timer_enabled = False
        self.timer_paused = False
        self.elapsed_active_seconds = 0
        self.cycles_completed = 0
        self.menu_is_open = False
        self.live_update_timer = None

        # Create status bar item
        self.status_bar = NSStatusBar.systemStatusBar()
        self.status_item = self.status_bar.statusItemWithLength_(NSVariableStatusItemLength)
        self.status_item.setTitle_("posture")

        # Create menu
        self.menu = NSMenu.alloc().init()

        # Timer display (non-clickable)
        self.timer_menu_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Timer Off", None, ""
        )
        self.menu.addItem_(self.timer_menu_item)

        # Cycles display (non-clickable)
        self.cycles_menu_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Cycles completed: 0", None, ""
        )
        self.menu.addItem_(self.cycles_menu_item)

        # Separator
        self.menu.addItem_(NSMenuItem.separatorItem())

        # Toggle button (Enable/Disable)
        self.toggle_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Enable Timer", "toggleTimer:", ""
        )
        self.toggle_item.setTarget_(self)
        self.menu.addItem_(self.toggle_item)

        # Pause/Resume button
        self.pause_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Pause Timer", "pauseTimer:", ""
        )
        self.pause_item.setTarget_(self)
        self.pause_item.setHidden_(True)
        self.menu.addItem_(self.pause_item)

        # Reset button
        self.reset_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Reset Timer", "resetTimer:", ""
        )
        self.reset_item.setTarget_(self)
        self.menu.addItem_(self.reset_item)

        # Separator
        self.menu.addItem_(NSMenuItem.separatorItem())

        # Quit button
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "quitApp:", ""
        )
        quit_item.setTarget_(self)
        self.menu.addItem_(quit_item)

        self.status_item.setMenu_(self.menu)
        self.menu.setDelegate_(self)

        # Start update timer
        self.update_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            CHECK_INTERVAL_SECONDS, self, "tick:", None, True
        )
        NSRunLoop.currentRunLoop().addTimer_forMode_(self.update_timer, NSDefaultRunLoopMode)

        # Request notification permission
        self.request_notification_permission()

        return self

    def request_notification_permission(self):
        """Request permission to send notifications."""
        center = UserNotifications.UNUserNotificationCenter.currentNotificationCenter()
        center.requestAuthorizationWithOptions_completionHandler_(
            UserNotifications.UNAuthorizationOptionAlert | UserNotifications.UNAuthorizationOptionSound,
            lambda granted, error: print(f"Notification permission: {'granted' if granted else 'denied'}")
        )

    @objc.typedSelector(b"v@:@")
    def menuWillOpen_(self, menu):
        """Called when menu opens - start live updates."""
        self.menu_is_open = True
        self.update_display()
        self.live_update_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0, self, "liveUpdate:", None, True
        )
        NSRunLoop.currentRunLoop().addTimer_forMode_(self.live_update_timer, NSDefaultRunLoopMode)

    @objc.typedSelector(b"v@:@")
    def menuDidClose_(self, menu):
        """Called when menu closes - stop live updates."""
        self.menu_is_open = False
        if self.live_update_timer:
            self.live_update_timer.invalidate()
            self.live_update_timer = None

    @objc.typedSelector(b"v@:@")
    def liveUpdate_(self, timer):
        """Called every second when menu is open for live display updates."""
        self.update_display()

    def format_time_elapsed(self):
        """Format elapsed time as MM:SS."""
        elapsed = min(self.elapsed_active_seconds, REMINDER_INTERVAL_SECONDS)
        minutes = elapsed // 60
        seconds = elapsed % 60
        return f"{minutes:02d}:{seconds:02d}"

    def format_progress_bar(self, segments=10):
        """Create a progress bar showing elapsed time."""
        progress = self.elapsed_active_seconds / REMINDER_INTERVAL_SECONDS
        progress = min(1.0, max(0.0, progress))
        filled = int(progress * segments)
        empty = segments - filled
        return f"[{'█' * filled}{'░' * empty}]"

    @objc.typedSelector(b"v@:@")
    def tick_(self, timer):
        """Called every CHECK_INTERVAL_SECONDS."""
        if not self.timer_enabled or self.timer_paused:
            return

        self.elapsed_active_seconds += CHECK_INTERVAL_SECONDS

        if self.elapsed_active_seconds >= REMINDER_INTERVAL_SECONDS:
            self.send_reminder()
            self.cycles_completed += 1
            self.elapsed_active_seconds = 0

        self.update_display()

    def update_display(self):
        """Update menu display with progress bar, elapsed time, and cycles."""
        if self.timer_enabled:
            progress_bar = self.format_progress_bar()
            elapsed = self.format_time_elapsed()
            if self.timer_paused:
                self.timer_menu_item.setTitle_(f"⏸ {progress_bar} {elapsed} (paused)")
            else:
                self.timer_menu_item.setTitle_(f"⏱ {progress_bar} {elapsed}")
        else:
            self.timer_menu_item.setTitle_("Timer Off")

        self.cycles_menu_item.setTitle_(f"Cycles completed: {self.cycles_completed}")

    def send_reminder(self):
        """Send notification."""
        elapsed = self.format_time_elapsed()
        content = UserNotifications.UNMutableNotificationContent.alloc().init()
        content.setTitle_("Check your posture")
        content.setBody_(f"{elapsed} elapsed")
        content.setSound_(UserNotifications.UNNotificationSound.defaultSound())

        request = UserNotifications.UNNotificationRequest.requestWithIdentifier_content_trigger_(
            "stretch_reminder", content, None
        )

        center = UserNotifications.UNUserNotificationCenter.currentNotificationCenter()
        center.addNotificationRequest_withCompletionHandler_(request, None)

    @objc.typedSelector(b"v@:@")
    def toggleTimer_(self, sender):
        """Enable or disable timer."""
        self.timer_enabled = not self.timer_enabled

        if self.timer_enabled:
            self.toggle_item.setTitle_("Disable Timer")
            self.pause_item.setHidden_(False)
            self.pause_item.setTitle_("Pause Timer")
            self.timer_paused = False
            self.elapsed_active_seconds = 0
        else:
            self.toggle_item.setTitle_("Enable Timer")
            self.pause_item.setHidden_(True)
            self.timer_paused = False

        self.update_display()

    @objc.typedSelector(b"v@:@")
    def pauseTimer_(self, sender):
        """Pause or resume the timer."""
        self.timer_paused = not self.timer_paused

        if self.timer_paused:
            self.pause_item.setTitle_("Resume Timer")
        else:
            self.pause_item.setTitle_("Pause Timer")

        self.update_display()

    @objc.typedSelector(b"v@:@")
    def resetTimer_(self, sender):
        """Reset timer and cycle count to zero."""
        self.elapsed_active_seconds = 0
        self.cycles_completed = 0
        self.timer_paused = False
        if self.timer_enabled:
            self.pause_item.setTitle_("Pause Timer")
        self.update_display()

    @objc.typedSelector(b"v@:@")
    def quitApp_(self, sender):
        """Quit the application."""
        NSApplication.sharedApplication().terminate_(None)


if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

    delegate = StretchReminderApp.alloc().init()
    app.setDelegate_(delegate)

    print("Stretch Reminder started - check your menu bar for 'Stretch'!")
    app.run()
