Option Explicit
Dim sh, fso, root
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = root
sh.Run Chr(34) & root & "\runtime\node.exe" & Chr(34) & " " & Chr(34) & root & "\launcher.mjs" & Chr(34), 0, False
