# Posture Check

A macOS menu bar app that reminds you to check your posture at regular intervals.

## Features

- **Menu bar integration** - Lives in your menu bar, no Dock icon
- **Live progress bar** - Visual countdown with `[████░░░░░░]` style progress
- **Cycle tracking** - Counts how many intervals you've completed
- **Pause/Resume** - Pause the timer when needed
- **Desktop notifications** - Simple reminders when it's time to check posture

## Requirements

- macOS (tested on Sequoia)
- Python 3.11+

## Installation

```bash
cd posture-check
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Start the app
```bash
source venv/bin/activate
python posture_check.py
```

### Menu bar controls
Click "posture" in your menu bar to access:
- **Progress display** - `⏱ [████░░░░░░] 04:15` showing elapsed time
- **Cycles completed** - Track your completed intervals
- **Enable/Disable Timer** - Turn the countdown on/off
- **Pause/Resume Timer** - Temporarily pause without resetting
- **Reset Timer** - Reset elapsed time and cycle count
- **Quit** - Close the app

## Configuration

Edit the constants at the top of `posture_check.py`:

```python
REMINDER_INTERVAL_SECONDS = 20 * 60  # 20 minutes
CHECK_INTERVAL_SECONDS = 5           # How often to update (5 seconds)
```

## Dependencies

- `pyobjc-framework-Cocoa` - For menu bar and app functionality
- `pyobjc-framework-UserNotifications` - For desktop notifications
