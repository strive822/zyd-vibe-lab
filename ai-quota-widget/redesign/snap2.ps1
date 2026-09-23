param([string]$action)
Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class DPI0 { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }'
[DPI0]::SetProcessDPIAware() | Out-Null
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Text;
using System.Drawing;
using System.Runtime.InteropServices;
public class S4 {
  public delegate bool P(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(P cb, IntPtr l);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int m);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out GR r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint f);
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, UIntPtr e);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  public struct GR { public int L, T, Rt, B; }
  public static IntPtr Hwnd = IntPtr.Zero;
  public static IntPtr FindHwnd(string title) {
    IntPtr found = IntPtr.Zero;
    EnumWindows(delegate(IntPtr h, IntPtr l) {
      var t = new StringBuilder(256); GetWindowText(h, t, 256);
      if (t.ToString() == title) { found = h; return false; }
      return true;
    }, IntPtr.Zero);
    return found;
  }
  public static GR Rect() { GR r = new GR(); GetWindowRect(Hwnd, out r); return r; }
  public static void ClickCenter() {
    GR r = Rect();
    int cx = (int)((r.L + r.Rt) / 2), cy = (int)((r.T + r.B) / 2);
    IntPtr lp = (IntPtr)((cy - r.T) * 65536 + (cx - r.L));
    PostMessage(Hwnd, 0x201, (IntPtr)1, lp);
    System.Threading.Thread.Sleep(80);
    PostMessage(Hwnd, 0x202, (IntPtr)0, lp);
  }
  public static void RightClickAt(int cx, int cy) {
    IntPtr lp = (IntPtr)(cy * 65536 + cx);
    PostMessage(Hwnd, 0x204, (IntPtr)2, lp);
    System.Threading.Thread.Sleep(80);
    PostMessage(Hwnd, 0x205, (IntPtr)0, lp);
  }
  public static string Snap(string path, int pad) {
    GR r = Rect();
    int W = r.Rt - r.L, H = r.B - r.T;
    if (W <= 0) return "zero";
    using (var bmp = new Bitmap(W + 2 * pad, H + 2 * pad)) {
      using (var g = Graphics.FromImage(bmp)) {
        g.Clear(Color.FromArgb(40, 40, 46));
        IntPtr dc = g.GetHdc();
        PrintWindow(Hwnd, dc, 2);
        g.ReleaseHdc(dc);
        using (var b = new SolidBrush(Color.FromArgb(16, 17, 20))) {
          g.FillRectangle(b, pad, pad + H - 2, W, 2);
        }
      }
      bmp.Save(path);
    }
    return W + "x" + H;
  }
  public static void ShotScreen(int x, int y, int w, int h, string path) {
    using (var bmp = new Bitmap(w, h)) {
      using (var g = Graphics.FromImage(bmp)) {
        g.CopyFromScreen(x, y, 0, 0, (System.Drawing.Size)new System.Drawing.Size(w, h));
      }
      bmp.Save(path);
    }
  }
  public static string SnapMenuWindow(string path) {
    IntPtr menu = IntPtr.Zero;
    EnumWindows(delegate(IntPtr h, IntPtr l) {
      var cn = new StringBuilder(256); GetClassName(h, cn, 256);
      if (cn.ToString() == "#32768" && IsWindowVisible(h)) { menu = h; return false; }
      return true;
    }, IntPtr.Zero);
    if (menu == IntPtr.Zero) return "menu-window-not-found";
    GR r = new GR(); GetWindowRect(menu, out r);
    int W = r.Rt - r.L, H = r.B - r.T;
    using (var bmp = new Bitmap(W, H)) {
      using (var g = Graphics.FromImage(bmp)) {
        IntPtr dc = g.GetHdc();
        PrintWindow(menu, dc, 2);
        g.ReleaseHdc(dc);
      }
      bmp.Save(path);
    }
    return "menu " + W + "x" + H;
  }
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int m);
}
'@
$root = 'E:\pi always\1a\redesign'
[S4]::Hwnd = [S4]::FindHwnd('AIQuotaWidget')
if ([S4]::Hwnd -eq [IntPtr]::Zero) { Write-Output 'no hwnd'; exit 1 }
switch ($action) {
  'collapsed' { Write-Output ('collapsed: ' + [S4]::Snap((Join-Path $root 'shot-bridge.png'), 20)) }
  'expanded'  { [S4]::ClickCenter(); Start-Sleep -Milliseconds 900; Write-Output ('expanded: ' + [S4]::Snap((Join-Path $root 'shot-expanded.png'), 20)) }
  'menu' {
    $r = [S4]::Rect()
    $mx = $r.L + 40; $my = $r.T + 12
    [S4]::SetCursorPos($mx, $my) | Out-Null
    Start-Sleep -Milliseconds 200
    [S4]::mouse_event(0x8, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 90
    [S4]::mouse_event(0x10, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 700
    Write-Output ([S4]::SnapMenuWindow((Join-Path $root 'shot-menu.png')))
  }
}
