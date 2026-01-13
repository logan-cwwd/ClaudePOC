' Countdown Timer Launcher (No Console Window)
' Use this to create a shortcut that can be pinned to taskbar

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "pythonw countdown_timer.py", 0, False
