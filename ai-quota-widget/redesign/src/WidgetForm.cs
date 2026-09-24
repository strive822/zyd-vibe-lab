using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Runtime.InteropServices;
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
    // LED 油量表视觉系统 v3（形态重定义）
    //
    // 面板态（默认常驻，~290×220）：2×2 竖刻度管网格
    //   行 = 提供商（O / Z），列 = 窗口（5h / 7d）
    //   每管：剩余 = 液面高度，10 格刻度，警戒红线刻在管壁，
    //         管旁大号等宽数字「剩 N%」（随阈值变色），格底绝对重置时刻
    // mini 态：一条细线，只显示最危险的一个数字（剩余最少、色阶最高）
    //
    // 剩余语义贯穿：液面/数字/色阶全部按「剩余」表达（满格=充足）。
    // 危险判定 = 剩余少。
    //
    // 动效纪律：零渐变、零发光、零玻璃；数据更新零动画。
    // ============================================================

    public class WidgetForm : Form
    {
        private AppConfig _cfg;
        private readonly List<AccountState> _accounts = new List<AccountState>();
        private NotifyIcon _tray;
        private ContextMenuStrip _menu;
        private System.Windows.Forms.Timer _tick;   // 1s：心跳/自动收回/自动刷新/置顶重申
        private System.Windows.Forms.Timer _anim;   // 15ms：高度插值
        private int _animFromH;
        private int _animToH;
        private DateTime _animStart;
        private int _tickCount;
        private bool _hover;
        private bool _pressing;
        private bool _dragging;
        private Point _downScreen;
        private float _scale = 1f;
        private Font _font;
        private Font _fontBold;
        private Font _fontSmall;
        private Font _fontMicro;
        private Font _fontMono;
        private Font _fontMonoSmall;
        private Font _fontMonoNum;
        private Font _fontMonoBig;
        private ToolTip _toolTip;
        private Icon _trayIcon;
        private bool _balloonTemplateShown;
        private bool _balloonHideShown;
        private readonly bool _mock;
        private DateTime _nextRefresh = DateTime.MinValue;
        private DateTime _lastRefresh = DateTime.MinValue;
        private bool _refreshing;
        private bool _exiting;

        // ---- 色板 ----
        private static readonly Color ColBg = Color.FromArgb(16, 17, 20);
        private static readonly Color ColBgHover = Color.FromArgb(24, 26, 30);
        private static readonly Color ColText = Color.FromArgb(210, 215, 222);
        private static readonly Color ColSub = Color.FromArgb(140, 147, 156);
        private static readonly Color ColSubDim = Color.FromArgb(92, 98, 106);
        private static readonly Color ColGreen = Color.FromArgb(70, 192, 138);
        private static readonly Color ColOrange = Color.FromArgb(232, 134, 58);
        private static readonly Color ColRed = Color.FromArgb(229, 83, 75);
        private static readonly Color ColDimDot = Color.FromArgb(70, 76, 84);
        private static readonly Color ColTubeWall = Color.FromArgb(58, 64, 72);
        private static readonly Color ColTick = Color.FromArgb(52, 58, 66);
        private static readonly Color ColHandle = Color.FromArgb(46, 49, 56);

        [DllImport("user32.dll")]
        private static extern bool DestroyIcon(IntPtr hIcon);

        [DllImport("user32.dll")]
        private static extern bool SetWindowPos(IntPtr hWnd, IntPtr after, int x, int y, int cx, int cy, uint flags);
        [DllImport("user32.dll")]
        private static extern bool ReleaseCapture();
        [DllImport("user32.dll")]
        private static extern IntPtr SendMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
        [DllImport("dwmapi.dll")]
        private static extern void DwmSetWindowAttribute(IntPtr hwnd, int attr, ref int val, int size);
        private static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
        private const uint WM_NCLBUTTONDOWN = 0xA1;
        private static readonly IntPtr HTCAPTION = (IntPtr)2;
        private const uint SWP_FLAGS = 0x1 | 0x2 | 0x10; // NOSIZE | NOMOVE | NOACTIVATE

        public WidgetForm(AppConfig cfg, bool mock)
        {
            _cfg = cfg;
            _mock = mock;
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
            AppConfig.Save(_cfg); // 启动即重写，把旧配置迁移成缩进格式
            Log.W("ctor done, accounts=" + _accounts.Count + " mock=" + _mock);
        }

        // ---------- 初始化 ----------

        private void InitForm()
        {
            Text = "AIQuotaWidget"; // 无边框不显示，但让窗口枚举可用
            FormBorderStyle = FormBorderStyle.None;
            StartPosition = FormStartPosition.Manual;
            ShowInTaskbar = false;
            AllowTransparency = true;
            DoubleBuffered = true;
            BackColor = ColBg;
            double op = _cfg.Ui.Opacity;
            if (op < 0.3 || op > 1.0) op = 1.0;
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
            _fontMonoNum = new Font("Consolas", 11f, FontStyle.Bold);
            _fontMonoBig = new Font("Consolas", 13f, FontStyle.Bold);
            _toolTip = new ToolTip();
            _toolTip.SetToolTip(this, "点击切换 面板/mini · 按住拖动 · 右键菜单");
            ApplySize(false);
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
                // Win11 DWM 默认给顶层窗画圆角+边缘高光；直角仪器窗禁用（底部白带根修）
                int pref = 1; // DWMWCP_DONOTROUND
                DwmSetWindowAttribute(Handle, 33, ref pref, 4);
            }
            catch { }
        }

        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);
            Program.StartSignalWorker(this);
            Log.W("onshown");
        }

        // ---------- 账号列表 ----------

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
                string name = string.IsNullOrEmpty(z.Name)
                    ? (_cfg.Zhipu.Count > 1 ? "智谱" + (i + 1) : "智谱")
                    : z.Name;
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

            // 单字母标签：O=OpenAI Codex、Z=智谱、D=DeepSeek；同提供商多账户才编号
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
            fresh.Ui = _cfg.Ui;
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

        private List<AccountState> VisibleAccounts()
        {
            List<AccountState> list = new List<AccountState>();
            foreach (AccountState a in _accounts)
            {
                if (a.Visible) list.Add(a);
            }
            return list;
        }

        // ---------- 尺寸与两态 ----------

        private int S(int px) { return (int)Math.Round(px * _scale); }

        private void ComputeTargetSize(out int w, out int h)
        {
            w = S(290);
            List<AccountState> vis = VisibleAccounts();
            int hh = S(6);
            foreach (AccountState a in vis)
            {
                // 块高实测：头18 + 标签10 + 管64 + 重置14 + 间10 = 116；
                // 余额/未配置块 = 头18 + 行20 + 间10 = 48
                hh += a.IsBalance ? S(48) : (IsUnconfigured(a) ? S(48) : S(116));
            }
            hh += S(6);
            if (hh < S(198)) hh = S(198);
            if (hh > S(242)) hh = S(242);
            h = hh;
        }

        private void ApplySize(bool animate)
        {
            int nw, nh;
            ComputeTargetSize(out nw, out nh);
            int oldRight = Right;
            Width = nw;
            Left = Math.Max(0, oldRight - nw); // 右缘锚定
            if (Height != nh)
            {
                if (!animate) Height = nh;
                else
                {
                    _animFromH = Height;
                    _animToH = nh;
                    _animStart = DateTime.UtcNow;
                    if (!_anim.Enabled) _anim.Start();
                }
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
            int hh = _animFromH + (int)Math.Round((_animToH - _animFromH) * ease);
            if (hh != Height) { Height = hh; Invalidate(); }
        }

        // ---------- 颜色与剩余语义 ----------

        // 剩余视角色阶：剩余充足绿 → 接近阈值橙 → 将耗尽红
        private Color RemainingColor(double remaining)
        {
            double redLine = 100.0 - _cfg.WarnThreshold; // 默认剩 10 以内红
            if (remaining <= redLine) return ColRed;
            if (remaining <= redLine + 20) return ColOrange;
            return ColGreen;
        }

        private static Color WithAlpha(Color c, int alpha)
        {
            return Color.FromArgb(alpha, c);
        }

        private bool Breathing(AccountState acc)
        {
            foreach (QuotaWindow w in acc.Windows)
            {
                double rem = 100.0 - w.UsedPercent;
                if (rem <= 100.0 - _cfg.WarnThreshold) return true;
            }
            return false;
        }

        private bool FlashOn()
        {
            return (Environment.TickCount / 500) % 2 == 0;
        }

        private static bool IsUnconfigured(AccountState acc)
        {
            return !string.IsNullOrEmpty(acc.Error) && acc.Error.Contains("未配置");
        }

        private Color ChannelDot(AccountState acc)
        {
            if (IsUnconfigured(acc)) return ColDimDot;
            if (!string.IsNullOrEmpty(acc.Error)) return ColRed;
            if (acc.IsBalance) return acc.Balance == null ? ColDimDot : ColGreen;
            return acc.Windows.Count == 0 ? ColDimDot : ColGreen;
        }

        private static QuotaWindow FindWindow(AccountState acc, WindowKind kind)
        {
            foreach (QuotaWindow w in acc.Windows)
            {
                if (w.Kind == kind) return w;
            }
            return null;
        }

        private static string CurrencySymbol(string currency)
        {
            if (currency == "CNY") return "¥";
            if (currency == "USD") return "$";
            return currency + " ";
        }

        private double WorstRemOf(AccountState acc)
        {
            double worstRem = double.MaxValue;
            foreach (QuotaWindow w in acc.Windows)
            {
                double rem = 100.0 - w.UsedPercent;
                if (rem < worstRem) worstRem = rem;
            }
            return worstRem;
        }

        // ---------- 竖刻度管（油量表芯） ----------

        // 剩余 = 液面高度（满格=充足）；10 格刻度；警戒红线刻在管壁剩余红阈处
        private void DrawTube(Graphics g, int x, int y, int w, int h, double remaining, bool stale, bool breathing)
        {
            using (Pen wall = new Pen(ColTubeWall, 1f))
            {
                g.DrawRectangle(wall, x, y, w, h);
            }
            int innerX = x + 2, innerY = y + 2;
            int innerW = w - 4, innerH = h - 4;
            if (innerH < 4) innerH = 4;

            using (SolidBrush off = new SolidBrush(Color.FromArgb(24, 26, 30)))
            {
                g.FillRectangle(off, innerX, innerY, innerW, innerH);
            }

            double clamped = Math.Max(0, Math.Min(100, remaining));
            int lit = (int)Math.Round(clamped / 10.0);
            if (clamped > 0 && lit < 1) lit = 1;
            if (lit > 10) lit = 10;
            int segH = Math.Max(2, innerH / 10);
            int alpha = stale ? 140 : (breathing && !FlashOn() ? 120 : 240);
            for (int i = 0; i < lit; i++)
            {
                // 从底部数第 i 段
                int segBottom = innerY + innerH - i * segH;
                int segTop = segBottom - segH + 1;
                if (segTop < innerY) segTop = innerY;
                // 段色按「剩余区间」语义：底段（剩余低）红，向上过渡绿
                double segRemMid = (i + 0.5) * 10.0;
                Color c = RemainingColor(segRemMid);
                using (SolidBrush b = new SolidBrush(WithAlpha(c, alpha)))
                {
                    g.FillRectangle(b, innerX, segTop, innerW, segBottom - segTop);
                }
            }

            // 警戒红线：刻在管壁剩余红阈处（默认剩 10%）
            double redRem = 100.0 - _cfg.WarnThreshold;
            if (redRem < 0) redRem = 0;
            int redY = innerY + innerH - (int)Math.Round(innerH * redRem / 100.0);
            using (Pen rp = new Pen(WithAlpha(ColRed, stale ? 120 : 200), 1f))
            {
                g.DrawLine(rp, innerX - 2, redY, innerX + innerW + 2, redY);
            }

            // 刻度：右侧每 10% 短横线
            using (Pen tp = new Pen(ColTick, 1f))
            {
                for (int i = 1; i < 10; i++)
                {
                    int ty = innerY + innerH - (int)Math.Round(innerH * i / 10.0);
                    g.DrawLine(tp, x + w + 1, ty, x + w + 4, ty);
                }
            }
        }

        private void DrawDot(Graphics g, int x, int y, int d, Color c)
        {
            using (SolidBrush b = new SolidBrush(c))
            {
                g.FillEllipse(b, x, y, d, d);
            }
        }

        // ---------- 绘制 ----------

        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.ClearTypeGridFit;

            using (SolidBrush bg = new SolidBrush(_hover ? ColBgHover : ColBg))
            {
                g.FillRectangle(bg, ClientRectangle);
            }

            PaintPanel(g);
        }

        private void PaintPanel(Graphics g)
        {
            Rectangle client = ClientRectangle;
            int pad = S(10);
            int halfW = (client.Width - pad * 2 - S(12)) / 2; // 列宽（5h / 7d）
            int tubeW = S(26);
            int tubeH = S(64);
            int y = S(4);

            // 顶部铭牌：AI QUOTA（仪器铭牌）
            TextRenderer.DrawText(g, "AI QUOTA", _fontMono,
                new Point(pad + S(2), y), ColSubDim,
                TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);
            y += S(16);

            List<AccountState> vis = VisibleAccounts();
            foreach (AccountState acc in vis)
            {
                int bx = pad;

                // 行头：dot + Abbr + Name
                DrawDot(g, bx, y + S(4), S(4), ChannelDot(acc));
                TextRenderer.DrawText(g, acc.Abbr, _fontMono,
                    new Rectangle(bx + S(8), y, S(18), S(14)),
                    acc.Stale ? ColSub : ColText,
                    TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);
                string suffix = acc.Stale ? "  ·数据过期" : (acc.Warning != null ? "  ·⚠" : "");
                TextRenderer.DrawText(g, acc.Name + suffix, _fontBold,
                    new Point(bx + S(28), y), ColText);
                y += S(16);

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
                    else if (IsUnconfigured(acc))
                    {
                        text = "未配置 Key";
                        tc = ColSub;
                    }
                    else if (!string.IsNullOrEmpty(acc.Error))
                    {
                        text = "刷新失败（" + Providers.Truncate(acc.Error, 30) + "）";
                        tc = ColRed;
                    }
                    TextRenderer.DrawText(g, text, _fontSmall, new Point(bx + S(8), y), tc);
                    y += S(20);
                }
                else if (IsUnconfigured(acc))
                {
                    // 空态单行：未配置 Key
                    TextRenderer.DrawText(g, "未配置 Key", _fontSmall, new Point(bx + S(8), y), ColSub);
                    y += S(20);
                }
                else
                {
                    // 2×2：行 = 提供商，列 = 5h / 7d
                    QuotaWindow five = FindWindow(acc, WindowKind.FiveHour);
                    QuotaWindow week = FindWindow(acc, WindowKind.Week);
                    int colX = bx + S(8);
                    int col2X = colX + halfW;

                    // 列标签（降一档灰度）
                    TextRenderer.DrawText(g, "5h", _fontMonoSmall,
                        new Point(colX, y), ColSubDim,
                        TextFormatFlags.Left | TextFormatFlags.Top | TextFormatFlags.NoPadding);
                    TextRenderer.DrawText(g, "7d", _fontMonoSmall,
                        new Point(col2X, y), ColSubDim,
                        TextFormatFlags.Left | TextFormatFlags.Top | TextFormatFlags.NoPadding);
                    y += S(10);

                    // 竖管（无数据时 rem=-1 → 空管）
                    DrawTube(g, colX, y, tubeW, tubeH,
                        five == null ? -1 : Math.Max(0, Math.Min(100, 100.0 - five.UsedPercent)),
                        acc.Stale, Breathing(acc));
                    DrawTube(g, col2X, y, tubeW, tubeH,
                        week == null ? -1 : Math.Max(0, Math.Min(100, 100.0 - week.UsedPercent)),
                        acc.Stale, Breathing(acc));

                    // 管旁大号剩余数字（等宽；剩余语义 + 阈值色；无数据 → 灰「无数据」）
                    int numY = y + tubeH / 2 - S(12);
                    DrawRemainNum(g, five, colX + tubeW + S(5), numY, acc);
                    DrawRemainNum(g, week, col2X + tubeW + S(5), numY, acc);
                    y += tubeH + S(2);

                    // 底部绝对重置时刻（列内右对齐；无数据画灰「—」）
                    DrawResetFoot(g, five, colX, halfW - S(8), y);
                    DrawResetFoot(g, week, col2X, halfW - S(8), y);
                    y += S(14);
                }

                y += S(10); // 块间距
            }

            // 底部状态行：上次刷新（压灰）
            string last = _lastRefresh == DateTime.MinValue ? "—" : _lastRefresh.ToString("HH:mm:ss");
            TextRenderer.DrawText(g, "刷新 " + last, _fontMicro,
                new Point(pad + S(2), client.Bottom - S(12)), ColSubDim,
                TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);
        }

        // 「剩 N%」：剩余语义 + 阈值色，等宽大号；无数据 → 灰「无数据」（不占红）
        private void DrawRemainNum(Graphics g, QuotaWindow w, int x, int y, AccountState acc)
        {
            if (w == null)
            {
                TextRenderer.DrawText(g, "无数据", _fontMonoSmall, new Point(x + S(4), y + S(6)), ColSub);
                return;
            }
            double rem = Math.Max(0, Math.Min(100, 100.0 - w.UsedPercent));
            TextRenderer.DrawText(g, "剩 " + Math.Round(rem) + "%", _fontMonoBig,
                new Point(x, y), acc.Stale ? ColSub : RemainingColor(rem));
        }

        // 底部绝对重置时刻（列内右对齐；无数据画灰「—」）
        private void DrawResetFoot(Graphics g, QuotaWindow w, int x, int w2, int y)
        {
            string reset = w == null || w.ResetAt == null ? "--" : Providers.FormatResetAnchor(w.ResetAt);
            TextRenderer.DrawText(g, "重置 " + reset, _fontMicro,
                new Rectangle(x, y, w2, S(12)),
                ColSub, TextFormatFlags.Right | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);
        }

        // ---------- 交互 ----------

        protected override void OnMouseEnter(EventArgs e)
        {
            base.OnMouseEnter(e);
            _hover = true;
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
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
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
            if (wasDragging) return;
        }

        protected override void OnMouseClick(MouseEventArgs e)
        {
            base.OnMouseClick(e);
            if (e.Button == MouseButtons.Right)
            {
                    BuildMenu();
                _menu.Show(Cursor.Position);
            }
        }

        // 菜单自身仍打开时不可立即 Dispose 重建，延迟到消息循环下一轮
        // 供截图工具使用：程序启动时主动弹出右键菜单（--menu-demo / --submenu-demo）
        internal void OpenMenuForDemo(bool expandOpacity)
        {
            BuildMenu();
            Rectangle r = ClientRectangle;
            _menu.Show(new Point(Location.X + S(30), Location.Y + S(8)));
            if (expandOpacity)
            {
                System.Threading.Thread.Sleep(400); // 等主菜单完成显示
                foreach (ToolStripItem item in _menu.Items)
                {
                    ToolStripMenuItem mi = item as ToolStripMenuItem;
                    if (mi != null && mi.Text == "透明度" && mi.HasDropDownItems)
                    {
                        mi.ShowDropDown();
                        break;
                    }
                }
            }
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
            _trayIcon = MakeTrayIcon(ColGreen);
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
            double worstUsed = 0;
            foreach (AccountState acc in _accounts)
            {
                if (!acc.Visible) continue;
                foreach (QuotaWindow w in acc.Windows)
                {
                    double used = w.UsedPercent;
                    if (used > worstUsed) worstUsed = used;
                }
            }
            Color c = RemainingColor(100.0 - worstUsed);
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

            // 显示类（开关项同组）
            _menu.Items.Add(CheckItem("置顶显示", _cfg.Ui.TopMost, delegate
            {
                _cfg.Ui.TopMost = !_cfg.Ui.TopMost;
                TopMost = _cfg.Ui.TopMost;
                SaveUi();
            }));

            _menu.Items.Add(CheckItem("开机自启", AppConfig.GetAutostart(), delegate
            {
                AppConfig.SetAutostart(!AppConfig.GetAutostart(), Application.ExecutablePath);
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

            _menu.Items.Add(new ToolStripSeparator());

            // 配置类
            _menu.Items.Add(PlainItem("打开配置", delegate
            {
                try { Process.Start("notepad.exe", "\"" + AppConfig.ConfigPath + "\""); }
                catch { }
            }));
            _menu.Items.Add(PlainItem("重载配置", delegate { ReloadConfig(); }));

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
                SaveUi();
            });
            parent.DropDownItems.Add(mi);
        }

        // ---------- 刷新 ----------

        private void OnTick(object sender, EventArgs e)
        {
            _tickCount++;
            // 置顶低频重申：每 30s SetWindowPos 一次（高频会与 DWM 合成竞争）
            if (_cfg.Ui.TopMost)
            {
                if (!TopMost) TopMost = true;
                if (_tickCount % 30 == 0)
                {
                    SetWindowPos(Handle, HWND_TOPMOST, 0, 0, 0, 0, SWP_FLAGS);
                }
            }
            if (!_refreshing && _nextRefresh != DateTime.MinValue && DateTime.Now >= _nextRefresh)
            {
                RefreshNow();
            }
            Invalidate(); // 呼吸相位 / 秒级时刻刷新
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

        // ---------- 配置持久化 ----------

        private void SaveUi()
        {
            _cfg.Ui.Left = Location.X;
            _cfg.Ui.Top = Location.Y;
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
    }
}
