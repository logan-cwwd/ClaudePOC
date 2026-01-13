#!/usr/bin/env python3
"""
Modern Countdown Timer for Windows
A clean, simple countdown timer that can be pinned to the taskbar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
import winsound
import sys
import ctypes
from datetime import datetime, timedelta


class CountdownTimer:
    """A countdown timer with modern GUI."""

    # Color scheme - Modern dark theme
    COLORS = {
        'bg': '#1a1a2e',
        'bg_secondary': '#16213e',
        'accent': '#0f3460',
        'highlight': '#e94560',
        'text': '#eaeaea',
        'text_dim': '#8b8b8b',
        'success': '#00d26a',
        'warning': '#ffc107',
    }

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Countdown Timer")
        self.root.geometry("420x580")
        self.root.minsize(380, 520)
        self.root.configure(bg=self.COLORS['bg'])

        # Make window stay on top by default (can be toggled)
        self.always_on_top = tk.BooleanVar(value=False)

        # Timer state
        self.total_seconds = 0
        self.remaining_seconds = 0
        self.is_running = False
        self.is_paused = False
        self.timer_thread = None
        self.stop_event = threading.Event()
        self.target_datetime = None  # For date/time mode

        # Mode: 'duration' or 'datetime'
        self.mode = tk.StringVar(value='duration')

        # Set app icon for taskbar (uses default if no icon file)
        try:
            self.root.iconbitmap(default='')
        except:
            pass

        # Apply dark title bar on Windows
        self._set_dark_title_bar()

        self._setup_styles()
        self._create_widgets()
        self._bind_events()

        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")

    def _set_dark_title_bar(self):
        """Apply dark mode to Windows title bar."""
        try:
            # Get the window handle
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())

            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Windows 10 20H1+ and Windows 11)
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20

            # Try the modern attribute first (Windows 10 20H1+)
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_int(1)),
                ctypes.sizeof(ctypes.c_int)
            )

            # If that didn't work, try the older attribute (Windows 10 pre-20H1)
            if result != 0:
                DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_USE_IMMERSIVE_DARK_MODE_OLD,
                    ctypes.byref(ctypes.c_int(1)),
                    ctypes.sizeof(ctypes.c_int)
                )
        except:
            pass  # Silently fail on non-Windows or older Windows versions

    def _setup_styles(self):
        """Configure ttk styles for modern look."""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure entry style
        style.configure(
            'Modern.TEntry',
            fieldbackground=self.COLORS['bg_secondary'],
            foreground=self.COLORS['text'],
            insertcolor=self.COLORS['text'],
            borderwidth=0,
            padding=10
        )

        # Configure checkbutton
        style.configure(
            'Modern.TCheckbutton',
            background=self.COLORS['bg'],
            foreground=self.COLORS['text_dim'],
            focuscolor=self.COLORS['bg']
        )
        style.map('Modern.TCheckbutton',
            background=[('active', self.COLORS['bg'])],
            foreground=[('active', self.COLORS['text'])]
        )

        # Configure radiobutton for tabs
        style.configure(
            'Tab.TRadiobutton',
            background=self.COLORS['bg'],
            foreground=self.COLORS['text_dim'],
            focuscolor=self.COLORS['bg'],
            font=('Segoe UI', 10)
        )
        style.map('Tab.TRadiobutton',
            background=[('active', self.COLORS['bg']), ('selected', self.COLORS['bg'])],
            foreground=[('active', self.COLORS['text']), ('selected', self.COLORS['highlight'])]
        )

    def _create_widgets(self):
        """Create all GUI widgets."""
        # Main container with padding
        self.main_frame = tk.Frame(self.root, bg=self.COLORS['bg'])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title section
        title_frame = tk.Frame(self.main_frame, bg=self.COLORS['bg'])
        title_frame.pack(fill=tk.X, pady=(0, 15))

        title_label = tk.Label(
            title_frame,
            text="COUNTDOWN TIMER",
            font=('Segoe UI', 12, 'bold'),
            fg=self.COLORS['text_dim'],
            bg=self.COLORS['bg'],
            anchor='center'
        )
        title_label.pack()

        # Timer title input
        timer_title_frame = tk.Frame(self.main_frame, bg=self.COLORS['bg_secondary'])
        timer_title_frame.pack(fill=tk.X, pady=(0, 15))

        self.timer_title = tk.Entry(
            timer_title_frame,
            font=('Segoe UI', 14),
            fg=self.COLORS['text'],
            bg=self.COLORS['bg_secondary'],
            insertbackground=self.COLORS['text'],
            relief='flat',
            justify='center'
        )
        self.timer_title.pack(fill=tk.X, padx=10, pady=10)
        self.timer_title.insert(0, "My Timer")

        # Display frame for countdown
        display_frame = tk.Frame(self.main_frame, bg=self.COLORS['accent'], padx=3, pady=3)
        display_frame.pack(fill=tk.X, pady=(0, 15))

        display_inner = tk.Frame(display_frame, bg=self.COLORS['bg_secondary'])
        display_inner.pack(fill=tk.BOTH, expand=True)

        self.time_display = tk.Label(
            display_inner,
            text="00:00:00",
            font=('Segoe UI', 48, 'bold'),
            fg=self.COLORS['text'],
            bg=self.COLORS['bg_secondary'],
            pady=15
        )
        self.time_display.pack()

        self.status_label = tk.Label(
            display_inner,
            text="Ready",
            font=('Segoe UI', 10),
            fg=self.COLORS['text_dim'],
            bg=self.COLORS['bg_secondary']
        )
        self.status_label.pack(pady=(0, 10))

        # Mode selector (tabs)
        mode_frame = tk.Frame(self.main_frame, bg=self.COLORS['bg'])
        mode_frame.pack(fill=tk.X, pady=(0, 10))

        duration_rb = tk.Radiobutton(
            mode_frame,
            text="Duration",
            variable=self.mode,
            value='duration',
            font=('Segoe UI', 10, 'bold'),
            fg=self.COLORS['text'],
            bg=self.COLORS['bg'],
            selectcolor=self.COLORS['bg'],
            activebackground=self.COLORS['bg'],
            activeforeground=self.COLORS['highlight'],
            indicatoron=0,
            padx=20,
            pady=8,
            relief='flat',
            command=self._switch_mode
        )
        duration_rb.pack(side=tk.LEFT, expand=True, fill=tk.X)

        datetime_rb = tk.Radiobutton(
            mode_frame,
            text="Date & Time",
            variable=self.mode,
            value='datetime',
            font=('Segoe UI', 10, 'bold'),
            fg=self.COLORS['text'],
            bg=self.COLORS['bg'],
            selectcolor=self.COLORS['bg'],
            activebackground=self.COLORS['bg'],
            activeforeground=self.COLORS['highlight'],
            indicatoron=0,
            padx=20,
            pady=8,
            relief='flat',
            command=self._switch_mode
        )
        datetime_rb.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Container for input modes
        self.input_container = tk.Frame(self.main_frame, bg=self.COLORS['bg'])
        self.input_container.pack(fill=tk.X, pady=(0, 15))

        # Duration input frame
        self.duration_frame = tk.Frame(self.input_container, bg=self.COLORS['bg'])
        self._create_duration_inputs()

        # DateTime input frame
        self.datetime_frame = tk.Frame(self.input_container, bg=self.COLORS['bg'])
        self._create_datetime_inputs()

        # Show duration mode by default
        self.duration_frame.pack(fill=tk.X)

        # Control buttons
        buttons_frame = tk.Frame(self.main_frame, bg=self.COLORS['bg'])
        buttons_frame.pack(fill=tk.X, pady=(10, 15))

        # Start button
        self.start_btn = tk.Button(
            buttons_frame,
            text="START",
            font=('Segoe UI', 11, 'bold'),
            fg=self.COLORS['text'],
            bg=self.COLORS['success'],
            activebackground='#00b359',
            activeforeground=self.COLORS['text'],
            relief='flat',
            cursor='hand2',
            width=10,
            pady=10,
            command=self.start_timer
        )
        self.start_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        # Pause button
        self.pause_btn = tk.Button(
            buttons_frame,
            text="PAUSE",
            font=('Segoe UI', 11, 'bold'),
            fg=self.COLORS['text'],
            bg=self.COLORS['warning'],
            activebackground='#e6ac00',
            activeforeground=self.COLORS['text'],
            relief='flat',
            cursor='hand2',
            width=10,
            pady=10,
            command=self.pause_timer,
            state='disabled'
        )
        self.pause_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        # Reset button
        self.reset_btn = tk.Button(
            buttons_frame,
            text="RESET",
            font=('Segoe UI', 11, 'bold'),
            fg=self.COLORS['text'],
            bg=self.COLORS['highlight'],
            activebackground='#cc3a52',
            activeforeground=self.COLORS['text'],
            relief='flat',
            cursor='hand2',
            width=10,
            pady=10,
            command=self.reset_timer
        )
        self.reset_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

        # Options section
        options_frame = tk.Frame(self.main_frame, bg=self.COLORS['bg'])
        options_frame.pack(fill=tk.X, pady=(10, 0))

        # Always on top checkbox
        self.on_top_check = ttk.Checkbutton(
            options_frame,
            text="Always on top",
            variable=self.always_on_top,
            style='Modern.TCheckbutton',
            command=self._toggle_on_top
        )
        self.on_top_check.pack(side=tk.LEFT)

        # Quick preset buttons (for duration mode)
        self.presets_frame = tk.Frame(self.main_frame, bg=self.COLORS['bg'])
        self.presets_frame.pack(fill=tk.X, pady=(15, 0))

        tk.Label(
            self.presets_frame,
            text="Quick presets:",
            font=('Segoe UI', 9),
            fg=self.COLORS['text_dim'],
            bg=self.COLORS['bg']
        ).pack(side=tk.LEFT, padx=(0, 10))

        presets = [("5m", 5, 0), ("10m", 10, 0), ("15m", 15, 0), ("30m", 30, 0), ("1h", 0, 1)]
        for label, mins, hours in presets:
            btn = tk.Button(
                self.presets_frame,
                text=label,
                font=('Segoe UI', 9),
                fg=self.COLORS['text'],
                bg=self.COLORS['accent'],
                activebackground=self.COLORS['bg_secondary'],
                activeforeground=self.COLORS['text'],
                relief='flat',
                cursor='hand2',
                padx=10,
                pady=3,
                command=lambda m=mins, h=hours: self._set_preset(m, h)
            )
            btn.pack(side=tk.LEFT, padx=2)

    def _create_duration_inputs(self):
        """Create duration input widgets (hours, minutes, seconds)."""
        time_inputs = tk.Frame(self.duration_frame, bg=self.COLORS['bg'])
        time_inputs.pack()

        # Hours
        hours_frame = tk.Frame(time_inputs, bg=self.COLORS['bg'])
        hours_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(
            hours_frame,
            text="Hours",
            font=('Segoe UI', 9),
            fg=self.COLORS['text_dim'],
            bg=self.COLORS['bg']
        ).pack()

        self.hours_var = tk.StringVar(value="0")
        self.hours_spin = tk.Spinbox(
            hours_frame,
            from_=0, to=99,
            textvariable=self.hours_var,
            width=5,
            font=('Segoe UI', 16),
            fg=self.COLORS['text'],
            bg=self.COLORS['bg_secondary'],
            buttonbackground=self.COLORS['accent'],
            relief='flat',
            justify='center'
        )
        self.hours_spin.pack(pady=5)

        # Minutes
        mins_frame = tk.Frame(time_inputs, bg=self.COLORS['bg'])
        mins_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(
            mins_frame,
            text="Minutes",
            font=('Segoe UI', 9),
            fg=self.COLORS['text_dim'],
            bg=self.COLORS['bg']
        ).pack()

        self.mins_var = tk.StringVar(value="5")
        self.mins_spin = tk.Spinbox(
            mins_frame,
            from_=0, to=59,
            textvariable=self.mins_var,
            width=5,
            font=('Segoe UI', 16),
            fg=self.COLORS['text'],
            bg=self.COLORS['bg_secondary'],
            buttonbackground=self.COLORS['accent'],
            relief='flat',
            justify='center'
        )
        self.mins_spin.pack(pady=5)

        # Seconds
        secs_frame = tk.Frame(time_inputs, bg=self.COLORS['bg'])
        secs_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(
            secs_frame,
            text="Seconds",
            font=('Segoe UI', 9),
            fg=self.COLORS['text_dim'],
            bg=self.COLORS['bg']
        ).pack()

        self.secs_var = tk.StringVar(value="0")
        self.secs_spin = tk.Spinbox(
            secs_frame,
            from_=0, to=59,
            textvariable=self.secs_var,
            width=5,
            font=('Segoe UI', 16),
            fg=self.COLORS['text'],
            bg=self.COLORS['bg_secondary'],
            buttonbackground=self.COLORS['accent'],
            relief='flat',
            justify='center'
        )
        self.secs_spin.pack(pady=5)

    def _create_datetime_inputs(self):
        """Create date/time input widgets."""
        now = datetime.now()

        # Date row
        date_frame = tk.Frame(self.datetime_frame, bg=self.COLORS['bg'])
        date_frame.pack(pady=(0, 10))

        # Month
        month_frame = tk.Frame(date_frame, bg=self.COLORS['bg'])
        month_frame.pack(side=tk.LEFT, padx=5)

        tk.Label(
            month_frame,
            text="Month",
            font=('Segoe UI', 9),
            fg=self.COLORS['text_dim'],
            bg=self.COLORS['bg']
        ).pack()

        self.month_var = tk.StringVar(value=str(now.month))
        self.month_spin = tk.Spinbox(
            month_frame,
            from_=1, to=12,
            textvariable=self.month_var,
            width=4,
            font=('Segoe UI', 14),
            fg=self.COLORS['text'],
            bg=self.COLORS['bg_secondary'],
            buttonbackground=self.COLORS['accent'],
            relief='flat',
            justify='center'
        )
        self.month_spin.pack(pady=3)

        # Day
        day_frame = tk.Frame(date_frame, bg=self.COLORS['bg'])
        day_frame.pack(side=tk.LEFT, padx=5)

        tk.Label(
            day_frame,
            text="Day",
            font=('Segoe UI', 9),
            fg=self.COLORS['text_dim'],
            bg=self.COLORS['bg']
        ).pack()

        self.day_var = tk.StringVar(value=str(now.day))
        self.day_spin = tk.Spinbox(
            day_frame,
            from_=1, to=31,
            textvariable=self.day_var,
            width=4,
            font=('Segoe UI', 14),
            fg=self.COLORS['text'],
            bg=self.COLORS['bg_secondary'],
            buttonbackground=self.COLORS['accent'],
            relief='flat',
            justify='center'
        )
        self.day_spin.pack(pady=3)

        # Year
        year_frame = tk.Frame(date_frame, bg=self.COLORS['bg'])
        year_frame.pack(side=tk.LEFT, padx=5)

        tk.Label(
            year_frame,
            text="Year",
            font=('Segoe UI', 9),
            fg=self.COLORS['text_dim'],
            bg=self.COLORS['bg']
        ).pack()

        self.year_var = tk.StringVar(value=str(now.year))
        self.year_spin = tk.Spinbox(
            year_frame,
            from_=now.year, to=now.year + 10,
            textvariable=self.year_var,
            width=6,
            font=('Segoe UI', 14),
            fg=self.COLORS['text'],
            bg=self.COLORS['bg_secondary'],
            buttonbackground=self.COLORS['accent'],
            relief='flat',
            justify='center'
        )
        self.year_spin.pack(pady=3)

        # Time row (optional)
        time_label = tk.Label(
            self.datetime_frame,
            text="Time (optional)",
            font=('Segoe UI', 9),
            fg=self.COLORS['text_dim'],
            bg=self.COLORS['bg']
        )
        time_label.pack(pady=(5, 0))

        time_frame = tk.Frame(self.datetime_frame, bg=self.COLORS['bg'])
        time_frame.pack(pady=(0, 5))

        # Hour
        hour_frame = tk.Frame(time_frame, bg=self.COLORS['bg'])
        hour_frame.pack(side=tk.LEFT, padx=5)

        tk.Label(
            hour_frame,
            text="Hour",
            font=('Segoe UI', 9),
            fg=self.COLORS['text_dim'],
            bg=self.COLORS['bg']
        ).pack()

        self.hour_var = tk.StringVar(value="12")
        self.hour_spin = tk.Spinbox(
            hour_frame,
            from_=0, to=23,
            textvariable=self.hour_var,
            width=4,
            font=('Segoe UI', 14),
            fg=self.COLORS['text'],
            bg=self.COLORS['bg_secondary'],
            buttonbackground=self.COLORS['accent'],
            relief='flat',
            justify='center'
        )
        self.hour_spin.pack(pady=3)

        # Minute
        minute_frame = tk.Frame(time_frame, bg=self.COLORS['bg'])
        minute_frame.pack(side=tk.LEFT, padx=5)

        tk.Label(
            minute_frame,
            text="Minute",
            font=('Segoe UI', 9),
            fg=self.COLORS['text_dim'],
            bg=self.COLORS['bg']
        ).pack()

        self.minute_var = tk.StringVar(value="0")
        self.minute_spin = tk.Spinbox(
            minute_frame,
            from_=0, to=59,
            textvariable=self.minute_var,
            width=4,
            font=('Segoe UI', 14),
            fg=self.COLORS['text'],
            bg=self.COLORS['bg_secondary'],
            buttonbackground=self.COLORS['accent'],
            relief='flat',
            justify='center'
        )
        self.minute_spin.pack(pady=3)

    def _switch_mode(self):
        """Switch between duration and datetime input modes."""
        if self.mode.get() == 'duration':
            self.datetime_frame.pack_forget()
            self.duration_frame.pack(fill=tk.X)
            self.presets_frame.pack(fill=tk.X, pady=(15, 0))
        else:
            self.duration_frame.pack_forget()
            self.presets_frame.pack_forget()
            self.datetime_frame.pack(fill=tk.X)

    def _bind_events(self):
        """Bind keyboard and window events."""
        self.root.bind('<Return>', lambda e: self.start_timer())
        self.root.bind('<space>', lambda e: self.pause_timer() if self.is_running else self.start_timer())
        self.root.bind('<Escape>', lambda e: self.reset_timer())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _toggle_on_top(self):
        """Toggle always-on-top mode."""
        self.root.attributes('-topmost', self.always_on_top.get())

    def _set_preset(self, mins, hours):
        """Set time from a preset button."""
        self.hours_var.set(str(hours))
        self.mins_var.set(str(mins))
        self.secs_var.set("0")

    def _format_time(self, seconds):
        """Format seconds into HH:MM:SS or D days HH:MM:SS."""
        if seconds >= 86400:  # More than a day
            days = int(seconds // 86400)
            remaining = seconds % 86400
            hours = int(remaining // 3600)
            mins = int((remaining % 3600) // 60)
            secs = int(remaining % 60)
            return f"{days}d {hours:02d}:{mins:02d}:{secs:02d}"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours:02d}:{mins:02d}:{secs:02d}"

    def _get_input_seconds(self):
        """Get total seconds from input fields (duration mode)."""
        try:
            hours = int(self.hours_var.get() or 0)
            mins = int(self.mins_var.get() or 0)
            secs = int(self.secs_var.get() or 0)
            return hours * 3600 + mins * 60 + secs
        except ValueError:
            return 0

    def _get_target_datetime(self):
        """Get target datetime from input fields (datetime mode)."""
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            hour = int(self.hour_var.get() or 0)
            minute = int(self.minute_var.get() or 0)
            return datetime(year, month, day, hour, minute, 0)
        except (ValueError, TypeError):
            return None

    def _update_display(self):
        """Update the time display."""
        self.time_display.config(text=self._format_time(self.remaining_seconds))

        # Update window title with timer name and time
        title = self.timer_title.get() or "Countdown Timer"
        self.root.title(f"{title} - {self._format_time(self.remaining_seconds)}")

    def _enable_inputs(self, enabled):
        """Enable or disable time input fields."""
        state = 'normal' if enabled else 'disabled'
        # Duration inputs
        self.hours_spin.config(state=state)
        self.mins_spin.config(state=state)
        self.secs_spin.config(state=state)
        # DateTime inputs
        self.month_spin.config(state=state)
        self.day_spin.config(state=state)
        self.year_spin.config(state=state)
        self.hour_spin.config(state=state)
        self.minute_spin.config(state=state)
        # Title
        self.timer_title.config(state=state)

    def start_timer(self):
        """Start or resume the countdown."""
        if self.is_paused:
            # Resume from pause
            self.is_paused = False
            self.is_running = True
            self.stop_event.clear()
            self._run_timer()
            self.status_label.config(text="Running", fg=self.COLORS['success'])
            self.start_btn.config(state='disabled')
            self.pause_btn.config(state='normal', text="PAUSE")
            return

        # Calculate total seconds based on mode
        if self.mode.get() == 'duration':
            total = self._get_input_seconds()
            if total <= 0:
                messagebox.showwarning("Invalid Time", "Please set a time greater than 0.")
                return
            self.target_datetime = None
        else:  # datetime mode
            target = self._get_target_datetime()
            if target is None:
                messagebox.showwarning("Invalid Date", "Please enter a valid date.")
                return
            now = datetime.now()
            if target <= now:
                messagebox.showwarning("Invalid Date", "Target date/time must be in the future.")
                return
            total = int((target - now).total_seconds())
            self.target_datetime = target

        self.total_seconds = total
        self.remaining_seconds = total
        self.is_running = True
        self.is_paused = False
        self.stop_event.clear()

        self._enable_inputs(False)
        self._update_display()
        self.status_label.config(text="Running", fg=self.COLORS['success'])

        self.start_btn.config(state='disabled')
        self.pause_btn.config(state='normal')

        self._run_timer()

    def _run_timer(self):
        """Run the countdown in the main thread using after()."""
        if not self.is_running or self.is_paused:
            return

        # For datetime mode, recalculate from target to handle drift
        if self.target_datetime:
            remaining = (self.target_datetime - datetime.now()).total_seconds()
            self.remaining_seconds = max(0, int(remaining))

        if self.remaining_seconds <= 0:
            self._timer_complete()
            return

        self._update_display()

        # Change color when almost done
        if self.remaining_seconds <= 10:
            self.time_display.config(fg=self.COLORS['highlight'])
        elif self.remaining_seconds <= 60:
            self.time_display.config(fg=self.COLORS['warning'])
        else:
            self.time_display.config(fg=self.COLORS['text'])

        # For duration mode, decrement; for datetime mode, we recalculate above
        if not self.target_datetime:
            self.remaining_seconds -= 1

        # Schedule next tick
        self.root.after(1000, self._run_timer)

    def _timer_complete(self):
        """Handle timer completion."""
        self.is_running = False
        self.target_datetime = None
        self.time_display.config(text="00:00:00", fg=self.COLORS['highlight'])
        self.status_label.config(text="Complete!", fg=self.COLORS['highlight'])

        self.start_btn.config(state='normal')
        self.pause_btn.config(state='disabled')
        self._enable_inputs(True)

        # Flash the window and play sound
        self._flash_window()
        self._play_alarm()

        # Show notification
        title = self.timer_title.get() or "Timer"
        messagebox.showinfo("Time's Up!", f'"{title}" has finished!')

    def _flash_window(self):
        """Flash the window to get attention."""
        def flash(count=0):
            if count < 6:
                bg = self.COLORS['highlight'] if count % 2 == 0 else self.COLORS['bg']
                self.time_display.config(bg=bg)
                self.root.after(200, lambda: flash(count + 1))
            else:
                self.time_display.config(bg=self.COLORS['bg_secondary'])

        flash()

    def _play_alarm(self):
        """Play alarm sound (Windows only)."""
        try:
            # Play Windows default notification sound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            # Play a series of beeps
            for _ in range(3):
                winsound.Beep(1000, 200)
                time.sleep(0.1)
        except:
            pass  # Silently fail on non-Windows systems

    def pause_timer(self):
        """Pause the countdown."""
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.is_running = False
            # If datetime mode, convert remaining time to duration for pause
            if self.target_datetime:
                self.target_datetime = None  # Switch to duration-based tracking
            self.status_label.config(text="Paused", fg=self.COLORS['warning'])
            self.pause_btn.config(text="RESUME")
            self.start_btn.config(state='normal')
        elif self.is_paused:
            # Resume
            self.start_timer()

    def reset_timer(self):
        """Reset the timer to initial state."""
        self.is_running = False
        self.is_paused = False
        self.stop_event.set()
        self.remaining_seconds = 0
        self.target_datetime = None

        self.time_display.config(text="00:00:00", fg=self.COLORS['text'])
        self.status_label.config(text="Ready", fg=self.COLORS['text_dim'])

        self.start_btn.config(state='normal')
        self.pause_btn.config(state='disabled', text="PAUSE")
        self._enable_inputs(True)

        self.root.title("Countdown Timer")

    def _on_close(self):
        """Handle window close."""
        self.is_running = False
        self.stop_event.set()
        self.root.destroy()

    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Entry point for the countdown timer."""
    app = CountdownTimer()
    app.run()


if __name__ == "__main__":
    main()
