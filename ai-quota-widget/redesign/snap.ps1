param([string]$action)
Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class DPI0 { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }'
[DPI0]::SetProcessDPIAware() | Out-Null
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Text;
using System.Drawing;
using System.Runtime.InteropServices;
public class S3 {
  public delegate bool P(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(P cb, IntPtr l);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int m);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out GR r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint f);
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
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
          g.FillRectangle(b, pad, pad + H - 2, W, 2); // 压掉 PrintWindow 对分层窗口的底边白带毛刺
        }
      }
      bmp.Save(path);
    }
    return W + "x" + H;
  }
}
'@
$root = 'E:\pi always\1a\redesign'
[S3]::Hwnd = [S3]::FindHwnd('AIQuotaWidget')
if ([S3]::Hwnd -eq [IntPtr]::Zero) { Write-Output 'no hwnd'; exit 1 }
switch ($action) {
  'bridge' { Write-Output ('bridge: ' + [S3]::Snap((Join-Path $root 'shot-bridge.png'), 20)) }
  'expanded' { [S3]::ClickCenter(); Start-Sleep -Milliseconds 900; Write-Output ('expanded: ' + [S3]::Snap((Join-Path $root 'shot-expanded.png'), 20)) }
  'collapse' { [S3]::ClickCenter(); Start-Sleep -Milliseconds 500; Write-Output ('collapsed: ' + [S3]::Snap((Join-Path $root 'shot-bridge.png'), 20)) }
  'line' { Write-Output ('line: ' + [S3]::Snap((Join-Path $root 'shot-line.png'), 20)) }
}
