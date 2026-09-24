param([string]$action)
# 只读截图工具：绝不启动/重启/停止挂件进程。
# menu/submenu 动作要求挂件已以 --menu-demo / --submenu-demo 模式运行（由调用方显式启动）。
Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class DPI0 { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }'
try { [DPI0]::SetProcessDPIAware() | Out-Null } catch { }
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Text;
using System.Drawing;
using System.Runtime.InteropServices;
public class S4 {
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  public static void EnsureDpi() { try { SetProcessDPIAware(); } catch { } }
  public delegate bool P(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(P cb, IntPtr l);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint p);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int m);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int m);
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
  public static string Snap(string path) {
    GR r = Rect();
    int W = r.Rt - r.L, H = r.B - r.T;
    if (W <= 0) return "zero";
    using (var bmp = new Bitmap(W, H)) {
      using (var g = Graphics.FromImage(bmp)) {
        g.Clear(Color.FromArgb(16, 17, 20));
        IntPtr dc = g.GetHdc();
        PrintWindow(Hwnd, dc, 2);
        g.ReleaseHdc(dc);
        using (var b = new SolidBrush(Color.FromArgb(16, 17, 20))) {
          g.FillRectangle(b, 0, H - 2, W, 2);
        }
      }
      bmp.Save(path);
    }
    return W + "x" + H;
  }
  public static string SnapAllMenus(string pathBase) {
    GR mr = Rect();
    uint pid = 0; GetWindowThreadProcessId(Hwnd, out pid);
    int n = 0;
    string first = null;
    EnumWindows(delegate(IntPtr h, IntPtr l) {
      uint p2; GetWindowThreadProcessId(h, out p2);
      if (p2 == pid && h != Hwnd && IsWindowVisible(h)) {
        var cn = new StringBuilder(256); GetClassName(h, cn, 256);
        if (cn.ToString().StartsWith("WindowsForms10")) {
          GR r = new GR(); GetWindowRect(h, out r);
          int w = r.Rt - r.L, ht = r.B - r.T;
          if (w > 30 && w < 700 && ht > 25 && ht < 900) {
            n++;
            string p = (n == 1) ? pathBase : pathBase.Replace(".png", "-" + n + ".png");
            using (var bmp = new Bitmap(w, ht)) {
              using (var g = Graphics.FromImage(bmp)) {
                IntPtr dc = g.GetHdc();
                PrintWindow(h, dc, 2);
                g.ReleaseHdc(dc);
              }
              bmp.Save(p);
            }
            if (first == null) first = p;
          }
        }
      }
      return true;
    }, IntPtr.Zero);
    if (n == 0) return "0 menu window(s)";
    return n + " menu window(s); first=" + first;
  }
  public static string EnumPopups() {
    GR mr = Rect();
    uint pid = 0; GetWindowThreadProcessId(Hwnd, out pid);
    var sb = new StringBuilder();
    EnumWindows(delegate(IntPtr h, IntPtr l) {
      uint p2; GetWindowThreadProcessId(h, out p2);
      if (p2 == pid && h != Hwnd && IsWindowVisible(h)) {
        var cn = new StringBuilder(256); GetClassName(h, cn, 256);
        GR r = new GR(); GetWindowRect(h, out r);
        sb.Append("popup class=[").Append(cn).Append("] rect=").Append(r.L).Append(",").Append(r.T)
          .Append(" ").Append(r.Rt - r.L).Append("x").Append(r.B - r.T).Append("\r\n");
      }
      return true;
    }, IntPtr.Zero);
    return sb.ToString();
  }
}
'@
[S4]::EnsureDpi()
$root = 'E:\pi always\1a\redesign'

function Assert-File([string]$p) {
  if (-not (Test-Path -LiteralPath $p)) {
    Write-Output ("FAIL(missing): " + $p)
    exit 1
  }
  $len = (Get-Item -LiteralPath $p).Length
  if ($len -le 0) {
    Write-Output ("FAIL(empty): " + $p)
    exit 1
  }
  Write-Output ("file-ok: " + $p + " (" + $len + " bytes)")
}

[S4]::Hwnd = [S4]::FindHwnd('AIQuotaWidget')
if ([S4]::Hwnd -eq [IntPtr]::Zero) {
  Write-Output 'FAIL: widget window not found (is it running?)'
  exit 1
}

switch ($action) {
  'collapsed' {
    Write-Output ('collapsed: ' + [S4]::Snap((Join-Path $root 'shot-bridge.png')))
    Assert-File (Join-Path $root 'shot-bridge.png')
  }
  'expanded' {
    [S4]::ClickCenter()  # 注入一次点击展开（3s 后挂件自动收回）
    Start-Sleep -Milliseconds 900
    Write-Output ('expanded: ' + [S4]::Snap((Join-Path $root 'shot-expanded.png')))
    Assert-File (Join-Path $root 'shot-expanded.png')
  }
  'menu' {
    # 要求挂件已以 --menu-demo 模式运行（菜单保持打开）
    Remove-Item (Join-Path $root 'shot-menu*.png') -ErrorAction SilentlyContinue
    $res = [S4]::SnapAllMenus((Join-Path $root 'shot-menu.png'))
    Write-Output $res
    if ($res -like '0 *') { Write-Output 'FAIL: no menu window captured'; exit 1 }
    Assert-File (Join-Path $root 'shot-menu.png')
  }
  'submenu' {
    # 要求挂件已以 --submenu-demo 模式运行（主菜单+透明度子菜单保持打开）
    Remove-Item (Join-Path $root 'shot-submenu*.png') -ErrorAction SilentlyContinue
    $res = [S4]::SnapAllMenus((Join-Path $root 'shot-submenu.png'))
    Write-Output $res
    if ($res -like '0 *') { Write-Output 'FAIL: no menu window captured'; exit 1 }
    Assert-File (Join-Path $root 'shot-submenu.png')
    Assert-File (Join-Path $root 'shot-submenu-2.png')
  }
  'enum' {
    Write-Output ([S4]::EnumPopups())
  }
  default { Write-Output ("unknown action: " + $action); exit 1 }
}
