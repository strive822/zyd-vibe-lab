param(
  [Parameter(Mandatory=$true)][string]$Browser,
  [Parameter(Mandatory=$true)][string]$Url,
  [Parameter(Mandatory=$true)][string]$StateFile
)
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
public class LibreTVWindow {
  public long Handle;
  public int ProcessId;
  public string Title;
  public bool Maximized;
}
public static class LibreTVNative {
  private delegate bool EnumProc(IntPtr hwnd, IntPtr parameter);
  [DllImport("user32.dll")] private static extern bool EnumWindows(EnumProc callback, IntPtr parameter);
  [DllImport("user32.dll")] private static extern bool IsWindowVisible(IntPtr hwnd);
  [DllImport("user32.dll",CharSet=CharSet.Unicode)] private static extern int GetWindowText(IntPtr hwnd,StringBuilder text,int count);
  [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr hwnd,out uint pid);
  [DllImport("user32.dll")] public static extern bool IsZoomed(IntPtr hwnd);
  [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hwnd,int command);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hwnd);
  public static LibreTVWindow[] Windows(string executable) {
    var result = new List<LibreTVWindow>();
    EnumWindows(delegate(IntPtr handle,IntPtr unused) {
      if(!IsWindowVisible(handle)) return true;
      uint pid; GetWindowThreadProcessId(handle,out pid);
      try {
        var process=Process.GetProcessById((int)pid);
        if(!String.Equals(Path.GetFullPath(process.MainModule.FileName),Path.GetFullPath(executable),StringComparison.OrdinalIgnoreCase))return true;
        var title=new StringBuilder(2048); GetWindowText(handle,title,title.Capacity);
        result.Add(new LibreTVWindow { Handle=handle.ToInt64(),ProcessId=(int)pid,Title=title.ToString(),Maximized=IsZoomed(handle) });
      } catch { }
      return true;
    },IntPtr.Zero);
    return result.ToArray();
  }
}
'@
$before = @([LibreTVNative]::Windows($Browser) | ForEach-Object { $_.Handle })
Start-Process -FilePath $Browser -ArgumentList @('--new-window','--start-maximized',$Url) -WindowStyle Maximized | Out-Null
$deadline = [DateTime]::UtcNow.AddSeconds(25)
$target = $null
while ([DateTime]::UtcNow -lt $deadline) {
  $all = @([LibreTVNative]::Windows($Browser) | Where-Object { $_.Title -like '*LibreTV*' })
  $fresh = @($all | Where-Object { $before -notcontains $_.Handle })
  if ($fresh.Count -eq 1) { $target=$fresh[0]; break }
  Start-Sleep -Milliseconds 150
}
if (!$target) { throw 'A unique new LibreTV browser window was not detected. No unrelated window was changed.' }
$handle = [IntPtr]$target.Handle
# Chromium may delegate to an existing browser process and ignore startup flags.
# Maximize the actual new LibreTV HWND after it exists, then verify its state.
[LibreTVNative]::ShowWindowAsync($handle,3) | Out-Null
[LibreTVNative]::SetForegroundWindow($handle) | Out-Null
$deadline = [DateTime]::UtcNow.AddSeconds(5)
while (![LibreTVNative]::IsZoomed($handle) -and [DateTime]::UtcNow -lt $deadline) {
  Start-Sleep -Milliseconds 100
  [LibreTVNative]::ShowWindowAsync($handle,3) | Out-Null
}
if (![LibreTVNative]::IsZoomed($handle)) { throw 'The LibreTV window did not enter the maximized state.' }
$record = [ordered]@{handle=$target.Handle; processId=$target.ProcessId; title=$target.Title; maximized=$true; verifiedAt=[DateTime]::UtcNow.ToString('o')}
$record | ConvertTo-Json -Compress | Set-Content -LiteralPath $StateFile -Encoding UTF8
Write-Output ('Verified maximized LibreTV window: ' + $target.Handle)
