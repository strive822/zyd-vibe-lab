Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class DPI1 { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }'
[DPI1]::SetProcessDPIAware() | Out-Null
Add-Type @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public class W {
  public delegate bool P(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(P cb, IntPtr l);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int m);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out GR r);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint x, uint y, uint d, UIntPtr e);
  public struct GR { public int L, T, Rt, B; }
  public static IntPtr Hwnd = IntPtr.Zero;
  public static IntPtr Find() {
    IntPtr f = IntPtr.Zero;
    EnumWindows(delegate(IntPtr h, IntPtr l) { var t = new StringBuilder(256); GetWindowText(h, t, 256); if (t.ToString() == 'AIQuotaWidget') { f = h; return false; } return true; }, IntPtr.Zero);
    return f;
  }
  public static GR Rect() { GR r; GetWindowRect(Hwnd, out r); return r; }
  public static void RealClick() {
    GR r = Rect();
    int cx = (r.L + r.Rt) / 2, cy = (r.T + r.B) / 2;
    SetCursorPos(cx, cy);
    mouse_event(2, 0, 0, 0, UIntPtr.Zero);
    System.Threading.Thread.Sleep(60);
    mouse_event(4, 0, 0, 0, UIntPtr.Zero);
  }
}
'@
[W]::Hwnd = [W]::Find()
if ([W]::Hwnd -eq [IntPtr]::Zero) { Write-Output 'no hwnd'; exit 1 }
$before = [W]::Rect()
[W]::RealClick()
Start-Sleep -Milliseconds 600
$after = [W]::Rect()
Write-Output ('before: ' + ($before.Rt - $before.L) + 'x' + ($before.B - $before.T) + '  after: ' + ($after.Rt - $after.L) + 'x' + ($after.B - $after.T))
