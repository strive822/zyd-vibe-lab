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
        private bool _pressing;
        private bool _dragging;
        private Point _downScreen;
        private Point _downFormLoc;
        private int _lastInteractTick = -1000000;
        private float _scale = 1f;
        private Font _font;
        private Font _fontBold;
        private Font _fontSmall;
        private Font _fontMicro;
        private Font _fontMono;
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
        private static readonly Color ColYellow = Color.FromArgb(224, 184, 78);
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

        public WidgetForm(AppConfig cfg)
        {
            _cfg = cfg;
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

            // 缩写：同各出现重名时追加序号，避免桥上歧义（智谱多 Key → 智1/智2）
            var groups = new Dictionary<string, List<AccountState>>();
            foreach (AccountState s in list)
            {
                s.Abbr = AbbrOf(s.Name);
                List<AccountState> gl;
                if (!groups.TryGetValue(s.Abbr, out gl))
                {
                    gl = new List<AccountState>();
                    groups[s.Abbr] = gl;
                }
                gl.Add(s);
            }
            foreach (KeyValuePair<string, List<AccountState>> kv in groups)
            {
                if (kv.Value.Count > 1)
                {
                    for (int i = 0; i < kv.Value.Count; i++)
                    {
                        kv.Value[i].Abbr = kv.Key + (i + 1);
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

        private void ComputeTargetSize(out int w, out int h)
        {
            List<AccountState> vis = VisibleAccounts();
            int bridgeW = S(11) + vis.Count * S(83) + Math.Max(0, vis.Count - 1) + S(6);
            if (_expanded)
            {
                w = Math.Max(bridgeW, S(352));
                h = BridgeH() + PanelHeight(vis);
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
                h += a.IsBalance ? S(24) : S(18) * 3 + S(8);
            }
            h += S(18); // footer
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
            if (pct >= _cfg.WarnThreshold) return ColRed;
            if (pct >= 60) return ColYellow;
            return ColGreen;
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

            PaintBridge(g, _expanded);
            if (_expanded) PaintPanel(g);
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

        private void PaintBridge(Graphics g, bool asHeader)
        {
            Rectangle client = ClientRectangle;
            using (SolidBrush bg = new SolidBrush(_hover && !_expanded ? ColBgHover : ColBg))
            {
                using (GraphicsPath path = RoundRect(client, S(4))) g.FillPath(bg, path);
            }

            // 展开态：桥脊内容钳制在顶部 BridgeH() 条带内，不随窗口变高而下坠
            int stripH = asHeader ? BridgeH() : client.Height;

            // 拖柄：两条竖纹
            using (SolidBrush hb = new SolidBrush(ColHandle))
            {
                g.FillRectangle(hb, S(2), S(6), 1, stripH - S(12));
                g.FillRectangle(hb, S(4), S(6), 1, stripH - S(12));
            }

            bool flashOn = FlashOn();
            int ux = S(11);
            int cy = stripH / 2;
            List<AccountState> vis = VisibleAccounts();
            for (int ci = 0; ci < vis.Count; ci++)
            {
                AccountState acc = vis[ci];
                Rectangle unit = new Rectangle(ux, 0, S(83), stripH);

                bool warn = Breathing(acc);
                double worst = WorstPercentOf(acc);

                // 状态点
                Color dotColor = ColDimDot;
                if (acc.IsBalance)
                {
                    dotColor = acc.Balance != null && !acc.Balance.Available ? ColYellow : ColGreen;
                }
                else if (acc.Windows.Count > 0)
                {
                    dotColor = StatusColor(worst);
                }
                DrawDot(g, ux, cy - S(2), S(4), dotColor, acc.Stale, warn);

                // 缩写
                TextRenderer.DrawText(g, AbbrOf(acc.Name), _fontMono,
                    new Rectangle(ux + S(7), 0, S(17), stripH),
                    acc.Stale ? ColSub : ColText,
                    TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);

                // 展开态桥脊只留点+缩写作锚轨，数字让位给面板（展开=增值）
                if (!asHeader)
                {
                    if (acc.IsBalance)
                    {
                    string bal = "--";
                    if (acc.Balance != null)
                    {
                        bal = CurrencySymbol(acc.Balance.Currency) +
                              acc.Balance.Total.ToString("0", System.Globalization.CultureInfo.InvariantCulture);
                    }
                    TextRenderer.DrawText(g, bal, _fontMonoNum,
                        new Rectangle(ux + S(27), 0, S(50), stripH),
                        acc.Stale ? ColSub : ColText,
                        TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);
                }
                else
                {
                    QuotaWindow five = FindWindow(acc, WindowKind.FiveHour);
                    QuotaWindow week = FindWindow(acc, WindowKind.Week);
                    int ledX = ux + S(27);
                    int ledY1 = cy - S(7);
                    int ledY2 = cy + S(2);
                    DrawLed(g, ledX, ledY1, S(5), LedSegIdle, LedGapIdle,
                        five == null ? 0 : five.UsedPercent, acc.Stale, warn);
                    DrawLed(g, ledX, ledY2, S(5), LedSegIdle, LedGapIdle,
                        week == null ? 0 : week.UsedPercent, acc.Stale, warn);

                    // 最紧百分比
                    string num = acc.Windows.Count == 0 ? "--" : Math.Round(worst) + "";
                    TextRenderer.DrawText(g, num, _fontMonoNum,
                        new Rectangle(ledX + LedIdleW + S(3), 0, S(24), stripH),
                        acc.Stale ? ColSub : (acc.Windows.Count == 0 ? ColSub : ColText),
                        TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);
                }
                }

                ux += S(83);

                // 通道分隔
                if (ci < vis.Count - 1)
                {
                    using (SolidBrush sb = new SolidBrush(ColSep))
                    {
                        g.FillRectangle(sb, ux, S(4), 1, stripH - S(8));
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
            int top = BridgeH();

            // 桥与面板的分隔
            using (SolidBrush sb = new SolidBrush(ColSep))
            {
                g.FillRectangle(sb, S(6), top, client.Width - S(12), 1);
            }
            top += S(3);

            List<AccountState> vis = VisibleAccounts();
            foreach (AccountState acc in vis)
            {
                Color dotColor = ColDimDot;
                if (acc.IsBalance)
                {
                    dotColor = acc.Balance != null && !acc.Balance.Available ? ColYellow : ColGreen;
                }
                else if (acc.Windows.Count > 0)
                {
                    dotColor = StatusColor(WorstPercentOf(acc));
                }
                bool warn = Breathing(acc);
                DrawDot(g, S(10), top + S(6), S(4), dotColor, acc.Stale, warn);
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
                else
                {
                    QuotaWindow five = FindWindow(acc, WindowKind.FiveHour);
                    QuotaWindow week = FindWindow(acc, WindowKind.Week);
                    DrawPanelRow(g, "5h", five, S(26), ref top, acc, true);
                    DrawPanelRow(g, "周", week, S(26), ref top, acc, false);
                }

                if (!string.IsNullOrEmpty(acc.Error) && !acc.IsBalance && acc.Windows.Count == 0)
                {
                    bool unconf = acc.Error.Contains("未配置");
                    TextRenderer.DrawText(g,
                        unconf ? "未配置 Key" : "刷新失败（" + Providers.Truncate(acc.Error, 34) + "）",
                        _fontMicro, new Point(S(44), top), unconf ? ColSub : ColRed);
                    top += S(14);
                }

                top += S(8);
                using (SolidBrush sb = new SolidBrush(ColSep))
                {
                    g.FillRectangle(sb, S(10), top, client.Width - S(20), 1);
                }
                top += 1;
            }

            // footer：只留收起提示（时间与频率在托盘 tooltip 里）
            TextRenderer.DrawText(g, "点击收起", _fontMicro,
                new Rectangle(S(10), client.Bottom - S(16), client.Width - S(20), S(14)),
                ColSub, TextFormatFlags.Left | TextFormatFlags.VerticalCenter);
        }

        private void DrawPanelRow(Graphics g, string label, QuotaWindow w, int x, ref int top, AccountState acc, bool relativeCountdown)
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
                acc.Stale ? ColSub : ColText);
            string cd = relativeCountdown ? Providers.FormatCountdown(w.ResetAt) : Providers.FormatResetAnchor(w.ResetAt);
            string suffix = relativeCountdown ? "后重置" : " 重置";
            if (cd != null)
            {
                TextRenderer.DrawText(g, cd + suffix, _fontMicro,
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
            _downFormLoc = Location;
            _lastInteractTick = Environment.TickCount;
            Capture = true;
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            _lastInteractTick = Environment.TickCount;
            if (!_pressing || _dragging) return;
            Point cur = Cursor.Position;
            int dx = cur.X - _downScreen.X;
            int dy = cur.Y - _downScreen.Y;
            if (Math.Abs(dx) + Math.Abs(dy) > S(5))
            {
                _dragging = true;
            }
            if (_dragging)
            {
                Location = new Point(_downFormLoc.X + dx, _downFormLoc.Y + dy);
            }
        }

        protected override void OnMouseUp(MouseEventArgs e)
        {
            base.OnMouseUp(e);
            if (e.Button != MouseButtons.Left || !_pressing) return;
            bool wasDragging = _dragging;
            _pressing = false;
            _dragging = false;
            Capture = false;
            if (wasDragging) { SaveUi(); return; }
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
            _menu.Items.Add("立即刷新", null, delegate { RefreshNow(); });
            _menu.Items.Add(new ToolStripSeparator());

            ToolStripMenuItem miLine = new ToolStripMenuItem("收成一线");
            miLine.Checked = _mode == "line";
            miLine.Click += delegate
            {
                SetMode(_mode == "line" ? "bridge" : "line");
                SafeRebuildMenu();
            };
            _menu.Items.Add(miLine);

            ToolStripMenuItem miTop = new ToolStripMenuItem("置顶显示");
            miTop.Checked = _cfg.Ui.TopMost;
            miTop.Click += delegate
            {
                _cfg.Ui.TopMost = !_cfg.Ui.TopMost;
                TopMost = _cfg.Ui.TopMost;
                SaveUi();
                SafeRebuildMenu();
            };
            _menu.Items.Add(miTop);

            ToolStripMenuItem miAccounts = new ToolStripMenuItem("显示账号");
            foreach (AccountState acc in _accounts)
            {
                AccountState a = acc;
                ToolStripMenuItem mi = new ToolStripMenuItem(a.Name);
                mi.Checked = a.Visible;
                mi.Click += delegate
                {
                    a.Visible = !a.Visible;
                    SetConfigVisible(a, a.Visible);
                    ApplySize(true);
                    SaveUi();
                    RefreshNow();
                    SafeRebuildMenu();
                };
                miAccounts.DropDownItems.Add(mi);
            }
            _menu.Items.Add(miAccounts);

            ToolStripMenuItem miOpacity = new ToolStripMenuItem("透明度");
            AddOpacityItem(miOpacity, "100%", 1.0);
            AddOpacityItem(miOpacity, "90%", 0.9);
            AddOpacityItem(miOpacity, "80%", 0.8);
            AddOpacityItem(miOpacity, "65%", 0.65);
            AddOpacityItem(miOpacity, "50%", 0.5);
            _menu.Items.Add(miOpacity);

            ToolStripMenuItem miAuto = new ToolStripMenuItem("开机自启");
            miAuto.Checked = AppConfig.GetAutostart();
            miAuto.Click += delegate
            {
                bool cur = AppConfig.GetAutostart();
                AppConfig.SetAutostart(!cur, Application.ExecutablePath);
                SafeRebuildMenu();
            };
            _menu.Items.Add(miAuto);

            _menu.Items.Add(new ToolStripSeparator());
            _menu.Items.Add("打开配置", null, delegate
            {
                try { Process.Start("notepad.exe", "\"" + AppConfig.ConfigPath + "\""); }
                catch { }
            });
            _menu.Items.Add("重载配置", null, delegate { ReloadConfig(); });
            _menu.Items.Add(new ToolStripSeparator());
            _menu.Items.Add("退出", null, delegate { ExitApp(); });

            if (_tray != null) _tray.ContextMenuStrip = _menu;
        }

        private void AddOpacityItem(ToolStripMenuItem parent, string label, double value)
        {
            ToolStripMenuItem mi = new ToolStripMenuItem(label);
            mi.Checked = Math.Abs(_cfg.Ui.Opacity - value) < 0.01;
            mi.Click += delegate
            {
                _cfg.Ui.Opacity = value;
                Opacity = value;
                UpdateLineKeying();
                SaveUi();
                SafeRebuildMenu();
            };
            parent.DropDownItems.Add(mi);
        }

        // ---------- 刷新 ----------

        private void OnTick(object sender, EventArgs e)
        {
            if (_cfg.Ui.TopMost && !TopMost) TopMost = true; // 持续重申置顶
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
}
