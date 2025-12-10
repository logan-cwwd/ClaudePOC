#!/usr/bin/env python3
"""A simple command-line stopwatch application."""

import time


class Stopwatch:
    """A stopwatch class with start, stop, lap, and reset functionality."""

    def __init__(self):
        self._start_time = None
        self._elapsed = 0.0
        self._running = False
        self._laps = []

    def start(self):
        """Start or resume the stopwatch."""
        if not self._running:
            self._start_time = time.perf_counter()
            self._running = True

    def stop(self):
        """Stop the stopwatch."""
        if self._running:
            self._elapsed += time.perf_counter() - self._start_time
            self._running = False

    def reset(self):
        """Reset the stopwatch to zero."""
        self._start_time = None
        self._elapsed = 0.0
        self._running = False
        self._laps = []

    def lap(self):
        """Record a lap time and return it."""
        current = self.elapsed
        self._laps.append(current)
        return current

    @property
    def elapsed(self):
        """Return the total elapsed time in seconds."""
        if self._running:
            return self._elapsed + (time.perf_counter() - self._start_time)
        return self._elapsed

    @property
    def laps(self):
        """Return a copy of recorded lap times."""
        return self._laps.copy()

    @property
    def is_running(self):
        """Return True if stopwatch is currently running."""
        return self._running


def format_time(seconds):
    """Format seconds into HH:MM:SS.mmm format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def main():
    """Run the interactive stopwatch."""
    sw = Stopwatch()

    print("=" * 40)
    print("          PYTHON STOPWATCH")
    print("=" * 40)
    print("\nCommands:")
    print("  [s] Start/Stop")
    print("  [l] Lap")
    print("  [r] Reset")
    print("  [q] Quit")
    print("-" * 40)

    try:
        while True:
            status = "RUNNING" if sw.is_running else "STOPPED"
            print(f"\rTime: {format_time(sw.elapsed)} [{status}]", end="", flush=True)

            # Non-blocking input check
            import sys
            import select

            if select.select([sys.stdin], [], [], 0.1)[0]:
                cmd = sys.stdin.readline().strip().lower()

                if cmd == 's':
                    if sw.is_running:
                        sw.stop()
                        print(f"\n>> Stopped at {format_time(sw.elapsed)}")
                    else:
                        sw.start()
                        print("\n>> Started")

                elif cmd == 'l':
                    if sw.is_running:
                        lap_time = sw.lap()
                        print(f"\n>> Lap {len(sw.laps)}: {format_time(lap_time)}")
                    else:
                        print("\n>> Start the stopwatch first")

                elif cmd == 'r':
                    sw.reset()
                    print("\n>> Reset")

                elif cmd == 'q':
                    print("\n>> Goodbye!")
                    break

    except KeyboardInterrupt:
        print("\n\n>> Interrupted. Goodbye!")

    # Show final summary
    if sw.laps:
        print("\n" + "=" * 40)
        print("LAP SUMMARY:")
        for i, lap in enumerate(sw.laps, 1):
            print(f"  Lap {i}: {format_time(lap)}")
        print("=" * 40)


if __name__ == "__main__":
    main()
