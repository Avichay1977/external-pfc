Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pythonw """ & Replace(WScript.ScriptFullName, "launch_pfc.vbs", "pfc_windows.py") & """", 0, False
