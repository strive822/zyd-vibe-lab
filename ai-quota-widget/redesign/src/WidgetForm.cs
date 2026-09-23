using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Windows.Forms;

namespace QuotaWidget
{
    public class AccountState
    {
        public string Key;
        public string Name;
        public string Abbr;
        public string Provider; // codex | zhipu | deepseek
        public bool Visible = true;
        public bool IsBalance;
        public string ApiKey;
        public string AuthJsonPath;
        public List<QuotaWindow> Windows = new List<QuotaWindow>();
        public BalanceData Balance;
        public string Error;
        public string Warning;
        public bool Stale;
        public DateTime LastSuccess = DateTime.MinValue;
    }

    internal class JobPair
    {
        public AccountState Acc;
        public Func<FetchResult> Run;
    }

    // ============================================================
    // LED BRIDGE 视觉系统
    // 「一块钉在屏幕边缘的调音台电平桥——余光里的 LED 精密仪器」
    //
    // 三态（面积从无到有）：
    //   LINE     高 12px，只有底部一条状态色线，几乎不存在
    //   BRIDGE   高 22px（默认），每账号一个通道：色点+缩写+双 LED 电平条+数字
    //   EXPANDED 桥变表头，下挂排版面板：全称/5H/周/百分比/重置倒计时
    //
    // Motion 只表达两件事：层级变化（高度插值）与状态（告警呼吸）。
    // 数据更新零动画——LED 是即时量化的，渐变是撒谎。
    // ============================================================

    public class WidgetForm : Form
    {
        private AppConfig _cfg;
        private readonly List<AccountState> _accounts = new List<AccountState>();
        private NotifyIcon _tray;
        private ContextMenuStrip _menu;
        private System.Windows.Forms.Timer _tick;   // 1s：呼吸相位 / 自动收回 / 自动刷新 / 重申置顶
        private System.Windows.Forms.Timer _anim;   // 15ms：高度插值
        private string _mode;                       // bridge | line
        private bool _expanded;
        private int _animFromH;
        private int _animToH;
        private DateTime _animStart;
        private bool _hover;
        private readonly bool _mock;
        private bool _pressing;
        private bool _dragging;
        private Point _downScreen;
        private int _lastInteractTick = -1000000;
        private float _scale = 1f;
        private Font _font;
        private Font _fontBold;
        private Font _fontSmall;
        private Font _fontMicro;
        private Font _fontMono;
        private Font _fontMonoSmall;
        private Font _fontMonoNum;
        private Icon _trayIcon;
        private bool _balloonTemplateShown;
        private bool _balloonHideShown;
        private DateTime _nextRefresh = DateTime.MinValue;
        private DateTime _lastRefresh = DateTime.MinValue;
        private bool _refreshing;
        private bool _exiting;
        private static readonly Color ColKey = Color.FromArgb(1, 2, 3); // LINE 态镂空键色
        private bool _keyed;

        // ---- 色板：暗室 + LED 三色 + 两级灰 ----
        private static readonly Color ColBg = Color.FromArgb(16, 17, 20);
        private static readonly Color ColBgLine = Color.FromArgb(13, 14, 17);
        private static readonly Color ColBgHover = Color.FromArgb(22, 24, 28);
        private static readonly Color ColSep = Color.FromArgb(35, 37, 43);
        private static readonly Color ColLedOff = Color.FromArgb(27, 29, 34);
        private static readonly Color ColText = Color.FromArgb(200, 205, 212);
        private static readonly Color ColSub = Color.FromArgb(107, 114, 128);
        private static readonly Color ColHandle = Color.FromArgb(46, 49, 56);
        private static readonly Color ColGreen = Color.FromArgb(70, 192, 138);
        private static readonly Color ColOrange = Color.FromArgb(232, 134, 58);
        private static readonly Color ColRed = Color.FromArgb(229, 83, 75);
        private static readonly Color ColDimDot = Color.FromArgb(58, 62, 70);

        // ---- LED 几何（物理像素，小元件不随 DPI 缩放更锐） ----
        private const int LedSegIdle = 2;   // 桥上：段宽 2
        private const int LedGapIdle = 1;
        private const int LedSegFull = 7;   // 展开面板：段宽 7
        private const int LedGapFull = 2;
        private const int LedIdleW = 10 * LedSegIdle + 9 * LedGapIdle;   // 29
        private const int LedFullW = 10 * LedSegFull + 9 * LedGapFull;   // 88

        [DllImport("user32.dll")]
        private static extern bool DestroyIcon(IntPtr hIcon);

        [DllImport("dwmapi.dll")]
        private static extern void DwmSetWindowAttribute(IntPtr hwnd, int attr, ref int val, int size);

        [DllImport("user32.dll")]
        private static extern bool SetWindowPos(IntPtr hWnd, IntPtr after, int x, int y, int cx, int cy, uint flags);
        [DllImport("user32.dll")]
        private static extern bool ReleaseCapture();
        [DllImport("user32.dll")]
        private static extern IntPtr SendMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
        private static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
        private const uint WM_NCLBUTTONDOWN = 0xA1;
        private static readonly IntPtr HTCAPTION = (IntPtr)2;
        private const uint SWP_FLAGS = 0x1 | 0x2 | 0x10; // NOSIZE | NOMOVE | NOACTIVATE

        public WidgetForm(AppConfig cfg, bool mock)
        {
            _cfg = cfg;
            _mock = mock;
            _mode = cfg.Ui.Mode == "line" ? "line" : "bridge";
            BuildAccountsFromConfig(null);
            InitForm();
            EnsureScaleFonts();
            InitTray();
            BuildMenu();
            _tick = new System.Windows.Forms.Timer();
            _tick.Interval = 1000;
            _tick.Tick += OnTick;
            _tick.Start();
            _anim = new System.Windows.Forms.Timer();
            _anim.Interval = 15;
            _anim.Tick += OnAnimTick;
            _nextRefresh = DateTime.Now.AddSeconds(2);
            AppConfig.Save(_cfg); // 启动即重写，把旧单行配置迁移成缩进格式
            Log.W("ctor done, mode=" + _mode + " accounts=" + _accounts.Count);
        }

        // ---------- 初始化 ----------

        private void InitForm()
        {
            Text = "AIQuotaWidget"; // 无边框不显示，但让 MainWindowHandle/窗口枚举可用
            FormBorderStyle = FormBorderStyle.None;
            StartPosition = FormStartPosition.Manual;
            ShowInTaskbar = false;
            AllowTransparency = true;
            DoubleBuffered = true;
            BackColor = ColBg;
            double op = _cfg.Ui.Opacity;
            if (op < 0.3 || op > 1.0) op = 0.95;
            Opacity = op;
            TopMost = _cfg.Ui.TopMost;
            int w, h;
            ComputeTargetSize(out w, out h);
            if (_cfg.Ui.Left >= 0 && _cfg.Ui.Top >= 0)
            {
                Location = new Point(_cfg.Ui.Left, _cfg.Ui.Top);
            }
            else
            {
                Rectangle wa = Screen.PrimaryScreen.WorkingArea;
                Location = new Point(wa.Right - w - S(24), wa.Bottom - h - S(56));
            }
            Size = new Size(w, h);
        }

        private void EnsureScaleFonts()
        {
            if (_font != null) return;
            try
            {
                using (Graphics g = CreateGraphics())
                {
                    _scale = Math.Max(1f, g.DpiX / 96f);
                }
            }
            catch { _scale = 1f; }
            Log.W("scale=" + _scale);
            _font = new Font("Microsoft YaHei UI", 9f);
            _fontBold = new Font("Microsoft YaHei UI", 9f, FontStyle.Bold);
            _fontSmall = new Font("Microsoft YaHei UI", 8f);
            _fontMicro = new Font("Microsoft YaHei UI", 7.5f);
            _fontMono = new Font("Consolas", 8.25f);
            _fontMonoSmall = new Font("Consolas", 7.5f);
            _fontMonoNum = new Font("Consolas", 10.5f, FontStyle.Bold);
            ApplySize(false); // scale 就绪后重算三态尺寸（InitForm 时 scale 尚未初始化）
            UpdateLineKeying();
        }

        protected override void OnHandleDestroyed(EventArgs e)
        {
            Log.W("handle destroyed, disposing=" + Disposing);
            base.OnHandleDestroyed(e);
        }

        protected override void OnLoad(EventArgs e)
        {
            base.OnLoad(e);
            if (_cfg.CreatedTemplate && !_balloonTemplateShown && _tray != null)
            {
                _tray.ShowBalloonTip(6000, "AI 额度悬浮窗",
                    "已生成配置模板，请右键 → 打开配置 填入智谱 / DeepSeek 的 API Key", ToolTipIcon.Info);
                _balloonTemplateShown = true;
            }
            RefreshNow();
            Log.W("onload done");
        }

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            try
            {
                // Win11 DWM 默认给顶层窗画圆角+边缘高光（底部亮带来源）；直角仪器窗禁用
                int pref = 1; // DWMWCP_DONOTROUND
                DwmSetWindowAttribute(Handle, 33, ref pref, 4);
            }
            catch { }
        }

        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);
            Log.W("onshown");
            Program.StartSignalWorker(this); // 句柄就绪后再启动，避免早期唤起信号被吞
        }

        // ---------- 账号列表（同 v1 数据层） ----------

        private void BuildAccountsFromConfig(List<AccountState> previous)
        {
            List<AccountState> list = new List<AccountState>();
            if (_cfg.Codex.Enabled)
            {
                AccountState s = MakeAccount(previous, "codex",
                    string.IsNullOrEmpty(_cfg.Codex.Name) ? "OpenAI Codex" : _cfg.Codex.Name,
                    "codex", null, _cfg.Codex.Visible, false);
                s.AuthJsonPath = _cfg.Codex.AuthJsonPath;
                list.Add(s);
            }
            for (int i = 0; i < _cfg.Zhipu.Count; i++)
            {
                ZhipuCfg z = _cfg.Zhipu[i];
                string name = string.IsNullOrEmpty(z.Name) ? ("智谱" + (i + 1)) : z.Name;
                list.Add(MakeAccount(previous, "zhipu:" + i, name, "zhipu", z.ApiKey, z.Visible, false));
            }
            if (_cfg.DeepSeek.Enabled)
            {
                AccountState s = MakeAccount(previous, "deepseek",
                    string.IsNullOrEmpty(_cfg.DeepSeek.Name) ? "DeepSeek" : _cfg.DeepSeek.Name,
                    "deepseek", _cfg.DeepSeek.ApiKey, _cfg.DeepSeek.Visible, true);
                list.Add(s);
            }
            _accounts.Clear();
            _accounts.AddRange(list);

            // 单字母标签系统：O=OpenAI Codex、Z=智谱、D=DeepSeek；同提供商多账户才追加序号
            var groups = new Dictionary<string, List<AccountState>>();
            foreach (AccountState s in list)
            {
                s.Abbr = s.Provider == "codex" ? "O" : s.Provider == "zhipu" ? "Z" : "D";
                List<AccountState> gl;
                if (!groups.TryGetValue(s.Provider, out gl))
                {
                    gl = new List<AccountState>();
                    groups[s.Provider] = gl;
                }
                gl.Add(s);
            }
            foreach (KeyValuePair<string, List<AccountState>> kv in groups)
            {
                if (kv.Value.Count > 1)
                {
                    for (int i = 0; i < kv.Value.Count; i++)
                    {
                        kv.Value[i].Abbr = kv.Key == "O" ? "O" + (i + 1) : kv.Key + (i + 1);
                    }
                }
            }
        }

        private AccountState MakeAccount(List<AccountState> previous, string key, string name,
            string provider, string apiKey, bool visible, bool isBalance)
        {
            AccountState s = new AccountState();
            s.Key = key;
            s.Name = name;
            s.Provider = provider;
            s.ApiKey = apiKey;
            s.Visible = visible;
            s.IsBalance = isBalance;
            if (previous != null)
            {
                foreach (AccountState old in previous)
                {
                    if (old.Key == key)
                    {
                        s.Windows = old.Windows;
                        s.Balance = old.Balance;
                        s.Error = old.Error;
                        s.Warning = old.Warning;
                        s.Stale = old.Stale;
                        s.LastSuccess = old.LastSuccess;
                    }
                }
            }
            return s;
        }

        public void ReloadConfig()
        {
            AppConfig fresh = AppConfig.Load();
            fresh.Ui = _cfg.Ui; // 保留窗口位置等 UI 状态
            fresh.CreatedTemplate = false;
            _cfg = fresh;
            BuildAccountsFromConfig(_accounts);
            ApplySize(true);
            RefreshNow();
        }

        private void SetConfigVisible(AccountState acc, bool visible)
        {
            if (acc.Provider == "codex") _cfg.Codex.Visible = visible;
            else if (acc.Provider == "zhipu")
            {
                int idx = ParseZhipuIndex(acc.Key);
                if (idx >= 0 && idx < _cfg.Zhipu.Count) _cfg.Zhipu[idx].Visible = visible;
            }
            else if (acc.Provider == "deepseek") _cfg.DeepSeek.Visible = visible;
        }

        private static int ParseZhipuIndex(string key)
        {
            const string prefix = "zhipu:";
            if (key == null || !key.StartsWith(prefix)) return -1;
            int n;
            if (int.TryParse(key.Substring(prefix.Length), out n)) return n;
            return -1;
        }

        // ---------- 尺寸与三态 ----------

        private int S(int px) { return (int)Math.Round(px * _scale); }
        private int BridgeH() { return S(22); }
        private int LineH() { return S(12); }

        private List<AccountState> VisibleAccounts()
        {
            List<AccountState> list = new List<AccountState>();
            foreach (AccountState a in _accounts)
            {
                if (a.Visible) list.Add(a);
            }
            return list;
        }

        private int ChannelWidth(AccountState acc)
        {
            return IsUnconfigured(acc) ? S(150) : S(140);
        }

        private void ComputeTargetSize(out int w, out int h)
        {
            List<AccountState> vis = VisibleAccounts();
            int bridgeW = S(12) + S(6);
            for (int i = 0; i < vis.Count; i++)
            {
                bridgeW += ChannelWidth(vis[i]);
                if (i < vis.Count - 1) bridgeW += 1;
            }
            if (_expanded)
            {
                w = Math.Max(bridgeW, S(352));
                h = S(6) + PanelHeight(vis) + S(4);
            }
            else if (_mode == "line")
            {
                w = bridgeW;
                h = LineH();
            }
            else
            {
                w = bridgeW;
                h = BridgeH();
            }
        }

        private int PanelHeight(List<AccountState> vis)
        {
            int h = S(3);
            foreach (AccountState a in vis)
            {
                h += a.IsBalance ? S(24)
                    : IsUnconfigured(a) ? S(18) * 2 + S(8)
                    : S(18) * 3 + S(8);
            }
            return h;
        }

        private void ApplySize(bool animate)
        {
            int nw, nh;
            ComputeTargetSize(out nw, out nh);
            Log.W("applysize animate=" + animate + " -> " + nw + "x" + nh);
            int oldRight = Right;
            bool heightChanged = nh != Height;
            Width = nw;
            Left = oldRight - nw; // 右缘锚定
            // 底缘钳制：展开后若超出工作区，整体上移（收回时保持，用户拖动即重新记忆）
            try
            {
                Rectangle wa = Screen.FromControl(this).WorkingArea;
                if (Top + nh > wa.Bottom - S(4)) Top = wa.Bottom - nh - S(4);
            }
            catch { }
            if (!heightChanged) { Invalidate(); return; }
            if (!animate) { Height = nh; Invalidate(); return; }
            _animFromH = Height;
            _animToH = nh;
            _animStart = DateTime.UtcNow;
            if (!_anim.Enabled) _anim.Start();
        }

        // LINE 态且完全不透明时：窗体底色转为镂空键色，视觉上只剩一条纯色线
        private void UpdateLineKeying()
        {
            bool wantKeyed = _mode == "line" && !_expanded && Opacity >= 0.999;
            if (wantKeyed == _keyed) return;
            _keyed = wantKeyed;
            if (_keyed)
            {
                TransparencyKey = ColKey;
                BackColor = ColKey;
            }
            else
            {
                TransparencyKey = Color.Empty;
                BackColor = ColBg;
            }
            Invalidate();
        }

        private void OnAnimTick(object sender, EventArgs e)
        {
            double t = (DateTime.UtcNow - _animStart).TotalMilliseconds / 150.0;
            if (t >= 1)
            {
                Height = _animToH;
                _anim.Stop();
                Invalidate();
                return;
            }
            double ease = 1 - (1 - t) * (1 - t) * (1 - t);
            int h = _animFromH + (int)Math.Round((_animToH - _animFromH) * ease);
            if (h != Height) { Height = h; Invalidate(); }
        }

        private void SetMode(string mode)
        {
            if (_mode == mode) return;
            _mode = mode;
            if (mode == "line") _expanded = false;
            SaveUi();
            ApplySize(true);
            UpdateLineKeying();
            SafeRebuildMenu();
        }

        private void ExpandPanel()
        {
            if (_expanded) return;
            _expanded = true;
            _lastInteractTick = Environment.TickCount;
            ApplySize(true);
            UpdateLineKeying();
        }

        private void CollapsePanel()
        {
            if (!_expanded) return;
            _expanded = false;
            ApplySize(true);
            UpdateLineKeying();
        }

        // ---------- 颜色与量化 ----------

        private Color StatusColor(double pct)
        {
            if (pct > 90) return ColRed;
            if (pct >= 70) return ColOrange;
            return ColGreen;
        }

        // 圆点只表示连接/配置状态：绿=正常 灰=未配置/无数据 红=连接失败
        private Color ChannelDot(AccountState acc)
        {
            if (IsUnconfigured(acc)) return ColDimDot;
            if (!string.IsNullOrEmpty(acc.Error)) return ColRed;
            if (acc.IsBalance) return acc.Balance == null ? ColDimDot : ColGreen;
            return acc.Windows.Count == 0 ? ColDimDot : ColGreen;
        }

        private static bool IsUnconfigured(AccountState acc)
        {
            return !string.IsNullOrEmpty(acc.Error) && acc.Error.Contains("未配置");
        }

        private bool Breathing(AccountState acc)
        {
            if (acc.IsBalance) return false;
            foreach (QuotaWindow w in acc.Windows)
            {
                if (w.UsedPercent >= _cfg.WarnThreshold) return true;
            }
            return false;
        }

        private double WorstPercent()
        {
            double worst = 0;
            foreach (AccountState acc in _accounts)
            {
                if (!acc.Visible) continue;
                foreach (QuotaWindow w in acc.Windows)
                {
                    if (w.UsedPercent > worst) worst = w.UsedPercent;
                }
            }
            return worst;
        }

        private double WorstPercentOf(AccountState acc)
        {
            double worst = 0;
            foreach (QuotaWindow w in acc.Windows)
            {
                if (w.UsedPercent > worst) worst = w.UsedPercent;
            }
            return worst;
        }

        private bool FlashOn()
        {
            return (Environment.TickCount / 500) % 2 == 0;
        }

        private Color WithAlpha(Color c, int alpha)
        {
            return Color.FromArgb(alpha, c);
        }

        // LED 电平条：10 段，段的色由其上界百分比决定（与阈值语义一致）
        private void DrawLed(Graphics g, int x, int y, int h, int segW, int gap,
            double pct, bool stale, bool breathing)
        {
            int lit = (int)Math.Ceiling(pct / 10.0); // ceil：90% 即亮红段
            if (pct > 0 && lit < 1) lit = 1;
            if (lit > 10) lit = 10;
            bool dim = breathing && !FlashOn();
            using (SolidBrush off = new SolidBrush(ColLedOff))
            {
                for (int i = 0; i < 10; i++)
                {
                    Rectangle r = new Rectangle(x + i * (segW + gap), y, segW, h);
                    if (i < lit)
                    {
                        Color c = StatusColor(i * 10 + 1); // 段色取段下界：红只出现在 90-100 段，与阈值语义对齐
                        int alpha = 235;
                        if (stale) alpha = 150;
                        else if (dim) alpha = 110;
                        using (SolidBrush b = new SolidBrush(WithAlpha(c, alpha))) g.FillRectangle(b, r);
                    }
                    else
                    {
                        g.FillRectangle(off, r);
                    }
                }
            }
        }

        private void DrawDot(Graphics g, int x, int y, int d, Color c, bool stale, bool breathing)
        {
            int alpha = 235;
            if (stale) alpha = 150;
            else if (breathing && !FlashOn()) alpha = 110;
            using (SolidBrush b = new SolidBrush(WithAlpha(c, alpha)))
            {
                g.FillEllipse(b, x, y, d, d);
            }
        }

        private static GraphicsPath RoundRect(Rectangle r, int radius)
        {
            GraphicsPath p = new GraphicsPath();
            int d = radius * 2;
            if (d > r.Width) d = r.Width;
            if (d > r.Height) d = r.Height;
            if (d < 1) { p.AddRectangle(r); return p; }
            p.AddArc(r.X, r.Y, d, d, 180, 90);
            p.AddArc(r.Right - d, r.Y, d, d, 270, 90);
            p.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
            p.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
            p.CloseFigure();
            return p;
        }

        private static string AbbrOf(string name)
        {
            if (string.IsNullOrEmpty(name)) return "?";
            string t = name.Trim();
            if (t.Length == 0) return "?";
            if (t[0] > 127) return t.Substring(0, 1); // 中文等取首字
            StringBuilder sb = new StringBuilder();
            foreach (char c in t)
            {
                if (char.IsLetterOrDigit(c))
                {
                    sb.Append(char.ToUpperInvariant(c));
                    if (sb.Length == 2) break;
                }
            }
            return sb.Length > 0 ? sb.ToString() : "?";
        }

        private static string CurrencySymbol(string currency)
        {
            if (currency == "CNY") return "¥";
            if (currency == "USD") return "$";
            return currency + " ";
        }

        // ---------- 绘制 ----------

        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.ClearTypeGridFit;

            if (_mode == "line" && !_expanded)
            {
                PaintLine(g);
                return;
            }

            if (_expanded)
            {
                using (SolidBrush bg = new SolidBrush(ColBg)) g.FillRectangle(bg, ClientRectangle);
                PaintPanel(g);
                return;
            }

            PaintBridge(g);
        }

        private void PaintLine(Graphics g)
        {
            Rectangle client = ClientRectangle;
            if (!_keyed)
            {
                using (SolidBrush bg = new SolidBrush(ColBgLine)) g.FillRectangle(bg, client);
            }
            double worst = WorstPercent();
            bool anyStale = false;
            bool warn = false;
            foreach (AccountState a in _accounts)
            {
                if (!a.Visible) continue;
                if (a.Stale) anyStale = true;
                if (Breathing(a)) warn = true;
            }
            Color c = StatusColor(worst);
            if (anyStale && !warn) c = WithAlpha(c, 170);
            if (warn) c = WithAlpha(c, FlashOn() ? 255 : 110);
            using (SolidBrush b = new SolidBrush(c))
            {
                g.FillRectangle(b, 0, client.Bottom - S(3), client.Width, S(3));
            }
        }

        private void PaintBridge(Graphics g)
        {
            Rectangle client = ClientRectangle;
            using (SolidBrush bg = new SolidBrush(_hover ? ColBgHover : ColBg))
            {
                g.FillRectangle(bg, client); // 直角深底，无圆角卡片
            }

            // 拖动把手：三条竖纹
            using (SolidBrush hb = new SolidBrush(ColHandle))
            {
                g.FillRectangle(hb, S(2), S(7), 1, client.Height - S(14));
                g.FillRectangle(hb, S(4), S(7), 1, client.Height - S(14));
                g.FillRectangle(hb, S(6), S(7), 1, client.Height - S(14));
            }

            bool flashOn = FlashOn();
            int ux = S(12);
            int cy = client.Height / 2;
            List<AccountState> vis = VisibleAccounts();
            for (int ci = 0; ci < vis.Count; ci++)
            {
                AccountState acc = vis[ci];

                // 未配置：塌缩为「● 名称 — 未配置 Key」，不出条与数字
                if (IsUnconfigured(acc))
                {
                    DrawDot(g, ux, cy - S(2), S(4), ColDimDot, false, false);
                    TextRenderer.DrawText(g, acc.Name + "  —  未配置 Key", _fontSmall,
                        new Rectangle(ux + S(8), 0, S(140), client.Height),
                        ColSub,
                        TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);
                    ux += S(150);
                }
                else
                {
                    // 圆点只表示连接/配置状态，不复用用量色
                    DrawDot(g, ux, cy - S(2), S(4), ChannelDot(acc), false, false);

                    // 缩写
                    TextRenderer.DrawText(g, acc.Abbr, _fontMono,
                        new Rectangle(ux + S(7), 0, S(18), client.Height),
                        acc.Stale ? ColSub : ColText,
                        TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);

                    double worst = WorstPercentOf(acc);
                    bool noData = !acc.IsBalance && acc.Windows.Count == 0;

                    // 数字带 %，随阈值变色
                    string num = acc.IsBalance
                        ? (acc.Balance == null ? "--%" : CurrencySymbol(acc.Balance.Currency) + acc.Balance.Total.ToString("0", System.Globalization.CultureInfo.InvariantCulture))
                        : (noData ? "--%" : Math.Round(worst) + "%");
                    Color numColor = acc.Stale ? ColSub
                        : acc.IsBalance ? (acc.Balance == null ? ColSub : ColText)
                        : (noData ? ColSub : StatusColor(worst));
                    TextRenderer.DrawText(g, num, _fontMonoNum,
                        new Rectangle(ux + S(19), 0, S(34), client.Height),
                        numColor,
                        TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);

                    // 右块双行：5h / 7d 重置时刻（直接显示日期时间，不用倒计时）
                    QuotaWindow five = FindWindow(acc, WindowKind.FiveHour);
                    QuotaWindow week = FindWindow(acc, WindowKind.Week);
                    string l1 = "5h " + (five == null ? "--" : Providers.FormatTimeAnchor(five.ResetAt) ?? "--");
                    string l2 = "7d " + (week == null ? "--" : Providers.FormatResetAnchor(week.ResetAt) ?? "--");
                    TextRenderer.DrawText(g, l1, _fontMonoSmall, new Point(ux + S(56), cy - S(10)), ColSub);
                    TextRenderer.DrawText(g, l2, _fontMonoSmall, new Point(ux + S(56), cy), ColSub);

                    ux += S(140);
                }

                // 通道分隔
                if (ci < vis.Count - 1)
                {
                    using (SolidBrush sb = new SolidBrush(ColSep))
                    {
                        g.FillRectangle(sb, ux, S(4), 1, client.Height - S(8));
                    }
                    ux += 1;
                }
            }
        }

        private static QuotaWindow FindWindow(AccountState acc, WindowKind kind)
        {
            foreach (QuotaWindow w in acc.Windows)
            {
                if (w.Kind == kind) return w;
            }
            return null;
        }

        private void PaintPanel(Graphics g)
        {
            Rectangle client = ClientRectangle;
            int top = S(6);

            List<AccountState> vis = VisibleAccounts();
            foreach (AccountState acc in vis)
            {
                DrawDot(g, S(10), top + S(6), S(4), ChannelDot(acc), false, false);
                string suffix = acc.Stale ? "  ·数据过期" : (acc.Warning != null ? "  ·⚠" : "");
                TextRenderer.DrawText(g, acc.Name + suffix, _fontBold,
                    new Point(S(19), top + S(1)), ColText);
                top += S(18);

                if (acc.IsBalance)
                {
                    string text = "等待数据…";
                    Color tc = ColSub;
                    if (acc.Balance != null)
                    {
                        string sym = CurrencySymbol(acc.Balance.Currency);
                        text = "余额 " + sym + acc.Balance.Total.ToString("0.00", System.Globalization.CultureInfo.InvariantCulture) +
                               (acc.Balance.Available ? "" : "（不可用）");
                        tc = ColText;
                    }
                    else if (!string.IsNullOrEmpty(acc.Error))
                    {
                        if (acc.Error.Contains("未配置"))
                        {
                            text = "未配置 Key"; // 没配置谈不上失败，不占用告警红
                            tc = ColSub;
                        }
                        else
                        {
                            text = "刷新失败（" + Providers.Truncate(acc.Error, 30) + "）";
                            tc = ColRed;
                        }
                    }
                    TextRenderer.DrawText(g, text, _fontSmall, new Point(S(26), top), tc);
                    top += S(18);
                }
                else if (IsUnconfigured(acc))
                {
                    // 空态塌缩：标题行下直接一行「未配置 Key」，不出空轨道与 --
                    TextRenderer.DrawText(g, "未配置 Key", _fontSmall, new Point(S(26), top), ColSub);
                    top += S(18);
                }
                else
                {
                    QuotaWindow five = FindWindow(acc, WindowKind.FiveHour);
                    QuotaWindow week = FindWindow(acc, WindowKind.Week);
                    DrawPanelRow(g, "5h", five, S(26), ref top, acc, false);
                    DrawPanelRow(g, "7d", week, S(26), ref top, acc, true);
                }

                if (!string.IsNullOrEmpty(acc.Error) && !acc.IsBalance && !IsUnconfigured(acc) && acc.Windows.Count == 0)
                {
                    TextRenderer.DrawText(g, "刷新失败（" + Providers.Truncate(acc.Error, 34) + "）",
                        _fontMicro, new Point(S(44), top), ColRed);
                    top += S(14);
                }

                top += S(8);
                using (SolidBrush sb = new SolidBrush(ColSep))
                {
                    g.FillRectangle(sb, S(10), top, client.Width - S(20), 1);
                }
                top += 1;
            }
        }

        private void DrawPanelRow(Graphics g, string label, QuotaWindow w, int x, ref int top, AccountState acc, bool weekly)
        {
            TextRenderer.DrawText(g, label, _fontMono,
                new Rectangle(x, top, S(16), S(16)),
                ColSub, TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);
            int ledX = x + S(18);
            DrawLed(g, ledX, top + S(4), S(8), LedSegFull, LedGapFull,
                w == null ? 0 : w.UsedPercent, acc.Stale, Breathing(acc));
            if (w == null)
            {
                TextRenderer.DrawText(g, "--", _fontMonoNum,
                    new Point(ledX + LedFullW + S(6), top - S(1)), ColSub);
                top += S(18);
                return;
            }
            string num = Math.Round(w.UsedPercent) + "%";
            TextRenderer.DrawText(g, num, _fontMonoNum,
                new Point(ledX + LedFullW + S(6), top - S(1)),
                acc.Stale ? ColSub : StatusColor(w.UsedPercent));
            string cd = weekly ? Providers.FormatResetAnchor(w.ResetAt) : Providers.FormatTimeAnchor(w.ResetAt);
            if (cd != null)
            {
                TextRenderer.DrawText(g, "重置 " + cd, _fontMicro,
                    new Rectangle(ledX + LedFullW + S(44), top, ClientRectangle.Width - (ledX + LedFullW + S(44)) - S(10), S(16)),
                    ColSub, TextFormatFlags.Right | TextFormatFlags.VerticalCenter);
            }
            top += S(18);
        }

        // ---------- 交互 ----------

        protected override void OnMouseEnter(EventArgs e)
        {
            base.OnMouseEnter(e);
            _hover = true;
            _lastInteractTick = Environment.TickCount;
            Invalidate();
        }

        protected override void OnMouseLeave(EventArgs e)
        {
            base.OnMouseLeave(e);
            _hover = false;
            Invalidate();
        }

        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.Button != MouseButtons.Left) return;
            _pressing = true;
            _dragging = false;
            _downScreen = Cursor.Position;
            _lastInteractTick = Environment.TickCount;
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            _lastInteractTick = Environment.TickCount;
            if (!_pressing || _dragging) return;
            Size drag = SystemInformation.DragSize;
            if (Math.Abs(Cursor.Position.X - _downScreen.X) > drag.Width ||
                Math.Abs(Cursor.Position.Y - _downScreen.Y) > drag.Height)
            {
                // 系统级拖动：手感与原生窗口一致，无跳变
                _dragging = true;
                ReleaseCapture();
                SendMessage(Handle, WM_NCLBUTTONDOWN, HTCAPTION, IntPtr.Zero);
                SaveUi();
            }
        }

        protected override void OnMouseUp(MouseEventArgs e)
        {
            base.OnMouseUp(e);
            if (e.Button != MouseButtons.Left || !_pressing) return;
            bool wasDragging = _dragging;
            _pressing = false;
            _dragging = false;
            if (wasDragging) return; // 系统拖动结束不触发点击
            HandleClick();
        }

        private void HandleClick()
        {
            _lastInteractTick = Environment.TickCount;
            if (_expanded) { CollapsePanel(); return; }
            if (_mode == "line") { SetMode("bridge"); return; }
            ExpandPanel();
        }

        protected override void OnMouseClick(MouseEventArgs e)
        {
            base.OnMouseClick(e);
            if (e.Button == MouseButtons.Right)
            {
                _lastInteractTick = Environment.TickCount;
                BuildMenu();
                _menu.Show(Cursor.Position);
            }
        }

        // 菜单自身仍打开时不可立即 Dispose 重建，延迟到消息循环下一轮
        // 供截图工具使用：程序启动时主动弹出右键菜单（--menu-demo）
        internal void OpenMenuForDemo()
        {
            BuildMenu();
            Rectangle r = ClientRectangle;
            _menu.Show(new Point(Location.X + S(30), Location.Y + S(8)));
        }

        private void SafeRebuildMenu()
        {
            if (IsDisposed || !IsHandleCreated) return;
            try { BeginInvoke((Action)delegate { BuildMenu(); }); }
            catch { }
        }

        public void ShowFromTray()
        {
            Show();
            WindowState = FormWindowState.Normal;
            if (_cfg.Ui.TopMost) TopMost = true;
            Activate();
        }

        private void HideToTray()
        {
            Hide();
            if (!_balloonHideShown && _tray != null)
            {
                _tray.ShowBalloonTip(4000, "AI 额度悬浮窗", "已隐藏到托盘，点击图标可恢复", ToolTipIcon.Info);
                _balloonHideShown = true;
            }
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            if (!_exiting && e.CloseReason == CloseReason.UserClosing)
            {
                e.Cancel = true;
                HideToTray();
                return;
            }
            base.OnFormClosing(e);
        }

        private void ExitApp()
        {
            _exiting = true;
            SaveUi();
            if (_tray != null)
            {
                _tray.Visible = false;
                _tray.Dispose();
                _tray = null;
            }
            if (_trayIcon != null)
            {
                try { DestroyIcon(_trayIcon.Handle); }
                catch { }
                _trayIcon.Dispose();
                _trayIcon = null;
            }
            if (_tick != null) { _tick.Stop(); _tick.Dispose(); _tick = null; }
            if (_anim != null) { _anim.Stop(); _anim.Dispose(); _anim = null; }
            Application.Exit();
        }

        // ---------- 托盘与菜单 ----------

        private void InitTray()
        {
            _tray = new NotifyIcon();
            _tray.Text = "AI 额度悬浮窗";
            _trayIcon = MakeTrayIcon(ColGreen); // 记录句柄以便退出时销毁，避免 HICON 泄漏
            _tray.Icon = _trayIcon;
            _tray.Visible = true;
            _tray.MouseClick += delegate(object s, MouseEventArgs e)
            {
                if (e.Button == MouseButtons.Left)
                {
                    if (Visible) HideToTray();
                    else ShowFromTray();
                }
            };
            BuildMenu();
            _tray.ContextMenuStrip = _menu;
        }

        private void UpdateTrayIcon()
        {
            if (_tray == null) return;
            Color c = StatusColor(WorstPercent());
            Icon old = _trayIcon;
            _trayIcon = MakeTrayIcon(c);
            _tray.Icon = _trayIcon;
            if (old != null)
            {
                try { DestroyIcon(old.Handle); }
                catch { }
                old.Dispose();
            }
        }

        private Icon MakeTrayIcon(Color c)
        {
            using (Bitmap bmp = new Bitmap(16, 16))
            {
                using (Graphics g = Graphics.FromImage(bmp))
                {
                    g.SmoothingMode = SmoothingMode.AntiAlias;
                    using (SolidBrush b = new SolidBrush(Color.FromArgb(30, 31, 36))) g.FillEllipse(b, 0, 0, 15, 15);
                    using (Pen p = new Pen(c, 2.4f)) g.DrawEllipse(p, 2.5f, 2.5f, 11, 11);
                }
                IntPtr h = bmp.GetHicon();
                return Icon.FromHandle(h);
            }
        }

        private void BuildMenu()
        {
            if (_menu != null)
            {
                _menu.Dispose();
                _menu = null;
            }
            _menu = new ContextMenuStrip();
            _menu.Renderer = new ToolStripProfessionalRenderer(new DarkMenuColors());
            _menu.BackColor = ColBg;
            _menu.ForeColor = ColText;
            _menu.ShowImageMargin = true;
            _menu.Font = _font;

            _menu.Items.Add(PlainItem("立即刷新", delegate { RefreshNow(); }));
            _menu.Items.Add(new ToolStripSeparator());

            // 显示类
            _menu.Items.Add(CheckItem("置顶显示", _cfg.Ui.TopMost, delegate
            {
                _cfg.Ui.TopMost = !_cfg.Ui.TopMost;
                TopMost = _cfg.Ui.TopMost;
                SaveUi();
            }));

            ToolStripMenuItem miOpacity = new ToolStripMenuItem("透明度");
            AddOpacityItem(miOpacity, "100%", 1.0);
            AddOpacityItem(miOpacity, "90%", 0.9);
            AddOpacityItem(miOpacity, "80%", 0.8);
            AddOpacityItem(miOpacity, "65%", 0.65);
            AddOpacityItem(miOpacity, "50%", 0.5);
            _menu.Items.Add(miOpacity);

            ToolStripMenuItem miAccounts = new ToolStripMenuItem("显示账号");
            foreach (AccountState acc in _accounts)
            {
                AccountState a = acc;
                ToolStripMenuItem mi = CheckItem(a.Name, a.Visible, delegate
                {
                    a.Visible = !a.Visible;
                    SetConfigVisible(a, a.Visible);
                    ApplySize(true);
                    SaveUi();
                    RefreshNow();
                });
                miAccounts.DropDownItems.Add(mi);
            }
            _menu.Items.Add(miAccounts);

            _menu.Items.Add(CheckItem("收成一线", _mode == "line", delegate
            {
                SetMode(_mode == "line" ? "bridge" : "line");
            }));

            _menu.Items.Add(new ToolStripSeparator());

            // 配置类
            _menu.Items.Add(PlainItem("打开配置", delegate
            {
                try { Process.Start("notepad.exe", "\"" + AppConfig.ConfigPath + "\""); }
                catch { }
            }));
            _menu.Items.Add(PlainItem("重载配置", delegate { ReloadConfig(); }));
            _menu.Items.Add(CheckItem("开机自启", AppConfig.GetAutostart(), delegate
            {
                AppConfig.SetAutostart(!AppConfig.GetAutostart(), Application.ExecutablePath);
            }));

            _menu.Items.Add(new ToolStripSeparator());
            _menu.Items.Add(PlainItem("退出", delegate { ExitApp(); }));

            // 深色子菜单同步
            StyleDropDown(_menu);

            if (_tray != null) _tray.ContextMenuStrip = _menu;
        }

        private ToolStripMenuItem PlainItem(string text, EventHandler onClick)
        {
            ToolStripMenuItem mi = new ToolStripMenuItem(text);
            mi.ForeColor = ColText;
            if (onClick != null) mi.Click += onClick;
            return mi;
        }

        // 勾选项用 accent 绿自定义勾选标记（自绘 image），不用系统默认
        private ToolStripMenuItem CheckItem(string text, bool on, EventHandler onClick)
        {
            ToolStripMenuItem mi = new ToolStripMenuItem(text);
            mi.Image = MakeCheckIcon(on);
            mi.ForeColor = on ? ColText : ColSub;
            mi.Click += delegate { onClick(this, EventArgs.Empty); };
            return mi;
        }

        private Bitmap MakeCheckIcon(bool on)
        {
            Bitmap bmp = new Bitmap(14, 14);
            if (on)
            {
                using (Graphics g = Graphics.FromImage(bmp))
                {
                    g.SmoothingMode = SmoothingMode.AntiAlias;
                    using (Pen p = new Pen(ColGreen, 2f))
                    {
                        g.DrawLines(p, new[] { new Point(3, 8), new Point(6, 11), new Point(11, 3) });
                    }
                }
            }
            return bmp;
        }

        private void StyleDropDown(ToolStrip drop)
        {
            drop.BackColor = ColBg;
            drop.ForeColor = ColText;
            drop.Font = _font;
            foreach (ToolStripItem item in drop.Items)
            {
                item.ForeColor = ColText;
                ToolStripMenuItem mi = item as ToolStripMenuItem;
                if (mi != null && mi.HasDropDownItems) StyleDropDown(mi.DropDown);
            }
        }

        private void AddOpacityItem(ToolStripMenuItem parent, string label, double value)
        {
            ToolStripMenuItem mi = CheckItem(label, Math.Abs(_cfg.Ui.Opacity - value) < 0.01, delegate
            {
                _cfg.Ui.Opacity = value;
                Opacity = value;
                UpdateLineKeying();
                SaveUi();
            });
            parent.DropDownItems.Add(mi);
        }

        private void ApplyMock()
        {
            foreach (AccountState acc in _accounts)
            {
                if (acc.IsBalance || acc.Provider != "codex") continue;
                long now = Providers.NowUnixSeconds();
                acc.Windows = new List<QuotaWindow>
                {
                    new QuotaWindow { Kind = WindowKind.FiveHour, DurationSeconds = 18000, UsedPercent = 93, ResetAt = now + 2400 },
                    new QuotaWindow { Kind = WindowKind.Week, DurationSeconds = 604800, UsedPercent = 75, ResetAt = now + 432000 }
                };
                acc.Error = null;
                acc.Warning = null;
                acc.Stale = false;
            }
            Invalidate();
        }

        private void OnTick(object sender, EventArgs e)
        {
            // 置顶双保险：属性重申 + 每秒 SetWindowPos 强制回最上层
            if (_cfg.Ui.TopMost)
            {
                if (!TopMost) TopMost = true;
                SetWindowPos(Handle, HWND_TOPMOST, 0, 0, 0, 0, SWP_FLAGS);
            }
            if (_expanded && _cfg.Ui.AutoCollapseSeconds > 0 &&
                Environment.TickCount - _lastInteractTick > _cfg.Ui.AutoCollapseSeconds * 1000)
            {
                CollapsePanel(); // 鼠标离开后自动收回，恢复“环境物”属性
            }
            if (!_refreshing && _nextRefresh != DateTime.MinValue && DateTime.Now >= _nextRefresh)
            {
                RefreshNow();
            }
            Invalidate(); // 呼吸相位 / 倒计时秒变
        }

        public void RefreshNow()
        {
            if (_refreshing) return;
            _refreshing = true;
            Invalidate();

            List<JobPair> jobs = new List<JobPair>();
            foreach (AccountState acc in _accounts)
            {
                if (!acc.Visible) continue;
                JobPair job = new JobPair();
                job.Acc = acc;
                if (acc.Provider == "codex")
                {
                    string path = acc.AuthJsonPath;
                    job.Run = delegate { return Providers.FetchCodex(path); };
                }
                else if (acc.Provider == "zhipu")
                {
                    string key = acc.ApiKey;
                    string scheme = _cfg.ZaiAuthorization;
                    job.Run = delegate { return Providers.FetchZhipu(key, scheme); };
                }
                else
                {
                    string key = acc.ApiKey;
                    job.Run = delegate { return Providers.FetchDeepSeek(key); };
                }
                jobs.Add(job);
            }

            ThreadPool.QueueUserWorkItem(delegate
            {
                bool first = true;
                foreach (JobPair job in jobs)
                {
                    JobPair j = job; // 防御性拷贝：不依赖编译器的 foreach 捕获语义
                    if (!first && j.Acc.Provider == "zhipu") Thread.Sleep(200);
                    first = false;
                    FetchResult r;
                    try { r = j.Run(); }
                    catch (Exception ex)
                    {
                        r = new FetchResult();
                        r.Error = ex.Message;
                    }
                    try
                    {
                        BeginInvoke((Action)delegate { ApplyResult(j.Acc, r); });
                    }
                    catch { }
                }
                try
                {
                    BeginInvoke((Action)delegate
                    {
                        _refreshing = false;
                        _lastRefresh = DateTime.Now;
                        _nextRefresh = DateTime.Now.AddSeconds(Math.Max(5, _cfg.RefreshIntervalSeconds));
                        if (_mock) ApplyMock();
                        UpdateTrayIcon();
                        if (_tray != null)
                        {
                            _tray.Text = "AI 额度悬浮窗 · " + _lastRefresh.ToString("HH:mm") + " 已刷新";
                        }
                        Invalidate();
                    });
                }
                catch { }
            });
        }

        private void ApplyResult(AccountState acc, FetchResult r)
        {
            if (IsDisposed) return;
            acc.LastSuccess = r != null && r.Ok ? DateTime.Now : acc.LastSuccess;
            if (r != null && r.Ok)
            {
                acc.Windows = r.Windows != null ? r.Windows : new List<QuotaWindow>();
                acc.Balance = r.Balance;
                acc.Error = null;
                acc.Warning = r.Warning;
                acc.Stale = r.Stale;
            }
            else
            {
                acc.Stale = acc.Windows.Count > 0 || acc.Balance != null;
                acc.Error = r == null ? "未知错误" : (string.IsNullOrEmpty(r.Error) ? "HTTP 错误" : r.Error);
            }
            Invalidate();
        }

        // ---------- 配置持久化 ----------

        private void SaveUi()
        {
            _cfg.Ui.Left = Location.X;
            _cfg.Ui.Top = Location.Y;
            _cfg.Ui.Collapsed = _mode == "line";
            _cfg.Ui.Mode = _mode;
            _cfg.Ui.Opacity = Opacity;
            _cfg.Ui.TopMost = TopMost;
            AppConfig.Save(_cfg);
        }
    }

    // 深色菜单色表：与挂件同一套背景/边框/hover 语言
    internal class DarkMenuColors : ProfessionalColorTable
    {
        private static Color Bg() { return Color.FromArgb(16, 17, 20); }
        private static Color Hover() { return Color.FromArgb(38, 40, 46); }
        private static Color Sep() { return Color.FromArgb(35, 37, 43); }

        public override Color ToolStripDropDownBackground { get { return Bg(); } }
        public override Color ImageMarginGradientBegin { get { return Bg(); } }
        public override Color ImageMarginGradientMiddle { get { return Bg(); } }
        public override Color ImageMarginGradientEnd { get { return Bg(); } }
        public override Color MenuBorder { get { return Sep(); } }
        public override Color MenuItemBorder { get { return Sep(); } }
        public override Color MenuItemSelected { get { return Hover(); } }
        public override Color MenuItemSelectedGradientBegin { get { return Hover(); } }
        public override Color MenuItemSelectedGradientEnd { get { return Hover(); } }
        public override Color MenuItemPressedGradientBegin { get { return Color.FromArgb(22, 24, 28); } }
        public override Color MenuItemPressedGradientEnd { get { return Color.FromArgb(22, 24, 28); } }
        public override Color SeparatorDark { get { return Sep(); } }
        public override Color SeparatorLight { get { return Sep(); } }
        public override Color CheckBackground { get { return Color.Transparent; } }
        public override Color CheckSelectedBackground { get { return Color.Transparent; } }
        public override Color CheckPressedBackground { get { return Color.Transparent; } }
    }
}
