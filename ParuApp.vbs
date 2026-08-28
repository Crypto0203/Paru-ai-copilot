Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\Suresh\.gemini\antigravity-ide\scratch\nova-pro-assistant"
WshShell.Run "py -3.11 start_paru_gui.py", 0, False
Set WshShell = Nothing
