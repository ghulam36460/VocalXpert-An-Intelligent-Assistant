"""
Timer Module - Set timers and alarms

Provides timer functionality for the voice assistant.
Works with both command-line and GUI interfaces.
"""

from time import sleep
import re
import os
from threading import Thread

# Get the module directory for audio paths
_module_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.dirname(_module_dir)
_audio_path = os.path.join(_project_dir, "assets", "audios", "Timer.mp3")

# Callback for when timer completes (can be set by GUI)
_timer_callback = None


def set_timer_callback(callback):
    """Set a callback function to be called when timer completes."""
    global _timer_callback
    _timer_callback = callback


def parse_time(query):
    """Parse time from query string. Returns seconds or None."""
    nums = re.findall(r"[0-9]+", query)
    if not nums:
        return None

    time_seconds = 0
    query_lower = query.lower()

    if "hour" in query_lower and len(nums) >= 1:
        time_seconds += int(nums[0]) * 3600
        nums = nums[1:]

    if "minute" in query_lower and len(nums) >= 1:
        time_seconds += int(nums[0]) * 60
        nums = nums[1:] if len(nums) > 1 else []

    if "second" in query_lower and len(nums) >= 1:
        time_seconds += int(nums[0])

    # If no specific unit found, assume minutes
    if time_seconds == 0 and nums:
        time_seconds = int(nums[0]) * 60

    return time_seconds if time_seconds > 0 else None


def _timer_thread(seconds):
    """Thread function that waits and triggers callback."""
    sleep(seconds)

    # Try to play sound
    try:
        import playsound

        if os.path.exists(_audio_path):
            playsound.playsound(_audio_path)
    except Exception as e:
        print(f"Could not play timer sound: {e}")

    # Call callback if set
    if _timer_callback:
        _timer_callback()


def startTimer(query):
    """
    Start a timer based on the query.

    Args:
        query: String like "set timer for 5 minutes" or "timer 30 seconds"

    Returns:
        str: Confirmation message or error
    """
    seconds = parse_time(query)

    if seconds is None:
        return "I couldn't understand the time. Try 'set timer for 5 minutes'."

    # Format time for display
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        time_str = f"{hours} hour{'s' if hours > 1 else ''}"
        if minutes > 0:
            time_str += f" {minutes} minute{'s' if minutes > 1 else ''}"
    elif seconds >= 60:
        minutes = seconds // 60
        secs = seconds % 60
        time_str = f"{minutes} minute{'s' if minutes > 1 else ''}"
        if secs > 0:
            time_str += f" {secs} second{'s' if secs > 1 else ''}"
    else:
        time_str = f"{seconds} second{'s' if seconds > 1 else ''}"

    # Start timer thread
    Thread(target=_timer_thread, args=(seconds,), daemon=True).start()

    return f"Timer set for {time_str}. I'll alert you when it's done!"


def stopwatch_format(seconds):
    """Format seconds into HH:MM:SS string."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
