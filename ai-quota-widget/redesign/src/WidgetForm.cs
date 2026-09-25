using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Text;
using System.Globalization;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;

namespace QuotaWidget
{
    // One always-visible dispatch board. Each provider owns its data, failure and next poll.
    public sealed class WidgetForm : Form
    {
        private AppConfig _cfg;
        private IList<AccountState> _accounts = new List<AccountState>();
        private RefreshCoordinator _coordinator;
        private string _uiMessage;
        private bool _resourcesDisposed;
        private NotifyIcon _tray;
        private Icon _trayIcon;
        private ContextMenuStrip _menu;
        private SettingsForm _activeSettings;
        private System.Windows.Forms.Timer _tick;
        private readonly bool _mock;
        private readonly string _mockScenario;
        private readonly Func<bool> _getAutostart;
        private readonly Func<bool, string, bool> _setAutostart;
        private const string AutostartError = "开机自启设置失败，请检查当前用户权限后重试。";
        private bool _exiting, _pressing, _dragging, _firstRunHint;
        private Point _downScreen;
        private DateTime _lastRefresh = DateTime.MinValue;
        private int _scroll, _bodyHeight, _viewportHeight, _ticks;
        private float _scale = 1f;
        private Font _text, _small, _heading, _number, _mono;
        private readonly ToolTip _footerTip = new ToolTip();
        private PixelButton _configure;
        private bool _overFooter;

        private static Color Bg { get { return PixelTheme.Background; } }
        private static Color Line { get { return PixelTheme.Line; } }
        private static Color TextColor { get { return PixelTheme.Text; } }
        private static Color Muted { get { return PixelTheme.Secondary; } }
        private static Color Accent { get { return PixelTheme.Accent; } }
        private static Color Caution { get { return PixelTheme.Warning; } }
        private static Color Danger { get { return PixelTheme.Error; } }

        [DllImport("user32.dll")]
        private static extern bool ReleaseCapture();
        [DllImport("user32.dll")]
        private static extern IntPtr SendMessage(IntPtr hwnd, uint msg, IntPtr w, IntPtr l);
        [DllImport("dwmapi.dll")]
        private static extern int DwmSetWindowAttribute(IntPtr hwnd, int attr, ref int value, int size);
        [DllImport("user32.dll")]
        private static extern bool DestroyIcon(IntPtr icon);

        private int S(int n) { return (int)Math.Round(n * _scale); }
        private int FooterH { get { return Math.Max(S(18), TextHeight("最近请求结束", _small, Width)); } }
        private int RowH { get { return QuotaNumberH + S(5); } }
        private static DateTime ReferenceTime { get { return new DateTime(2026, 9, 25, 17, 11, 30, DateTimeKind.Local); } }

        public WidgetForm(AppConfig cfg, bool mock, string mockScenario, float previewScale)
            : this(cfg, mock, mockScenario, previewScale, true)
        {
        }

        internal WidgetForm(AppConfig cfg, bool mock, string mockScenario, float previewScale, bool enableTray)
            : this(cfg, mock, mockScenario, previewScale, enableTray,
                AppConfig.GetAutostart, AppConfig.SetAutostart)
        {
        }

        internal WidgetForm(AppConfig cfg, bool mock, string mockScenario, float previewScale, bool enableTray,
            Func<bool> getAutostart, Func<bool, string, bool> setAutostart)
        {
            _cfg = cfg;
            _mock = mock;
            _mockScenario = mockScenario;
            _getAutostart = getAutostart;
            _setAutostart = setAutostart;
            Text = mock ? "AIQuotaWidgetPreview" : "AIQuotaWidget";
            FormBorderStyle = FormBorderStyle.None;
            StartPosition = FormStartPosition.Manual;
            ShowInTaskbar = false;
            DoubleBuffered = true;
            BackColor = Bg;
            TopMost = cfg.Ui.TopMost;
            try { using (Graphics g = CreateGraphics()) _scale = Math.Max(1f, g.DpiX / 96f); }
            catch { _scale = 1f; }
            if (mock && previewScale > 0) _scale = previewScale;
            _text = new Font("Microsoft YaHei UI", 12f * _scale, FontStyle.Regular, GraphicsUnit.Pixel);
            _small = new Font("Microsoft YaHei UI", Math.Max(12f, 10f * _scale), FontStyle.Regular, GraphicsUnit.Pixel);
            _heading = new Font("Microsoft YaHei UI", Math.Max(13f, 12f * _scale), FontStyle.Bold, GraphicsUnit.Pixel);
            _number = new Font("Consolas", Math.Max(20f, 16f * _scale), FontStyle.Bold, GraphicsUnit.Pixel);
            _mono = new Font("Consolas", Math.Max(12f, 9f * _scale), FontStyle.Regular, GraphicsUnit.Pixel);
            AccessibleName = "AI 额度悬浮窗 · 像素能源控制器";
            AccessibleDescription = "查看剩余额度和数据状态；菜单键或 Shift+F10 打开操作菜单。";
            _configure = new PixelButton(true) { Text = "打开设置", Font = _text, AccessibleName = "打开账号设置" };
            _configure.Click += delegate { ShowSettings(false); };
            Controls.Add(_configure);
            _footerTip.OwnerDraw = true;
            _footerTip.BackColor = PixelTheme.Surface;
            _footerTip.ForeColor = TextColor;
            _footerTip.Popup += delegate(object sender, PopupEventArgs e)
            {
                e.ToolTipSize = new Size(S(252), TextHeight(_footerTip.GetToolTip(this), _small, S(240)) + S(12));
            };
            _footerTip.Draw += delegate(object sender, DrawToolTipEventArgs e)
            {
                using (SolidBrush b = new SolidBrush(PixelTheme.Surface)) e.Graphics.FillRectangle(b, e.Bounds);
                using (Pen p = new Pen(Line)) e.Graphics.DrawRectangle(p, 0, 0, e.Bounds.Width - 1, e.Bounds.Height - 1);
                DrawText(e.Graphics, e.ToolTipText, _small, TextColor,
                    new Rectangle(S(6), S(6), e.Bounds.Width - S(12), e.Bounds.Height - S(12)), TextFormatFlags.WordBreak);
            };
            _coordinator = new RefreshCoordinator(FetchAccount, () => DateTime.UtcNow,
                DispatchResult, OnAccountsChanged);
            _coordinator.Reconcile(cfg);
            _accounts = _coordinator.Accounts;
            if (cfg.LoadError) _uiMessage = "配置损坏，已停止刷新与保存；修复后请重新启动。";
            if (_mock && (_mockScenario == "stale" || _mockScenario == "limited" || _mockScenario == "login" || _mockScenario == "refresh-error"))
                foreach (AccountState a in _accounts)
                    a.Apply(MockResult(a.Provider, "normal"), DateTime.Now.AddMinutes(-2), DateTime.UtcNow.AddMinutes(-2), 10);
            ResizeForContent(false);
            PlaceInitial();
            if (enableTray) InitTray();
            _tick = new System.Windows.Forms.Timer { Interval = 1000 };
            _tick.Tick += OnTick;
            _tick.Start();
        }

        protected override bool ShowWithoutActivation { get { return true; } }

        internal Bitmap RenderFrame()
        {
            Bitmap frame = new Bitmap(Width, Height);
            using (Graphics graphics = Graphics.FromImage(frame)) PaintWidget(graphics);
            if (_configure.Visible) _configure.DrawToBitmap(frame, _configure.Bounds);
            return frame;
        }

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            try { int noRound = 1; DwmSetWindowAttribute(Handle, 33, ref noRound, 4); } catch { }
        }

        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);
            Program.StartSignalWorker(this);
            RefreshNow();
            if (!_mock && !_cfg.LoadError && !_firstRunHint && !System.IO.File.Exists(AppConfig.ConfigPath))
            {
                _firstRunHint = true;
                BeginInvoke((Action)delegate { ShowSettings(false); });
            }
        }

        private void PlaceInitial()
        {
            if (_cfg.Ui.Left != -1 || _cfg.Ui.Top != -1)
                Location = new Point(_cfg.Ui.Left, _cfg.Ui.Top);
            else
            {
                Rectangle wa = Screen.PrimaryScreen.WorkingArea;
                Location = new Point(wa.Right - Width - S(24), wa.Bottom - Height - S(35));
            }
            ClampToScreen();
        }

        private void ClampToScreen()
        {
            Rectangle wa = Screen.FromRectangle(Bounds).WorkingArea;
            int x = Math.Max(wa.Left, Math.Min(Left, wa.Right - Width));
            int y = Math.Max(wa.Top, Math.Min(Top, wa.Bottom - Height));
            Location = new Point(x, y);
        }

        private FetchResult FetchAccount(AccountRequest request, CancellationToken cancellation)
        {
            if (_mock)
            {
                if ((_mockScenario == "loading" || _mockScenario == "refresh-error") && cancellation.WaitHandle.WaitOne(4500))
                    return new FetchResult { Canceled = true };
                return MockResult(request.Provider, _mockScenario);
            }
            return RefreshCoordinator.FetchProvider(request, cancellation);
        }

        private void DispatchResult(Action action)
        {
            if (_exiting || IsDisposed || !IsHandleCreated) return;
            try { BeginInvoke((Action)delegate { if (!_exiting && !IsDisposed) action(); }); }
            catch (InvalidOperationException) { }
        }

        private void OnAccountsChanged()
        {
            if (_exiting || IsDisposed) return;
            foreach (AccountState account in _accounts)
                if (account.LastCompletedUtc != DateTime.MinValue && account.LastCompletedUtc.ToLocalTime() > _lastRefresh)
                    _lastRefresh = account.LastCompletedUtc.ToLocalTime();
            if (_mock && _mockScenario == "reference" && _lastRefresh != DateTime.MinValue) _lastRefresh = ReferenceTime;
            ResizeForContent(false);
            UpdateTrayIcon();
            if (IsHandleCreated) AccessibilityNotifyClients(AccessibleEvents.ValueChange, -1);
        }

        private List<AccountState> VisibleAccounts()
        {
            List<AccountState> list = new List<AccountState>();
            foreach (AccountState a in _accounts) if (a.Visible) list.Add(a);
            return list;
        }

        private int TextWidth(string value, Font font)
        {
            using (Graphics g = CreateGraphics())
            using (StringFormat f = new StringFormat(StringFormat.GenericTypographic))
            {
                f.FormatFlags |= StringFormatFlags.NoWrap;
                return (int)Math.Ceiling(g.MeasureString(value ?? "", font, int.MaxValue, f).Width) + S(2);
            }
        }

        private int TextHeight(string value, Font font, int width)
        {
            using (Graphics g = CreateGraphics())
            using (StringFormat f = new StringFormat(StringFormat.GenericTypographic))
                return (int)Math.Ceiling(g.MeasureString(string.IsNullOrEmpty(value) ? " " : value,
                    font, Math.Max(1, width), f).Height) + S(2);
        }

        private string QuotaDetail(QuotaWindow quota)
        {
            if (quota == null) return "重置时间未知";
            DateTime now = _mock && _mockScenario == "reference" ? ReferenceTime : DateTime.Now;
            return quota.Kind == WindowKind.FiveHour
                ? Providers.FormatFiveHourReset(quota.ResetAt, now)
                : Providers.FormatWeekReset(quota.ResetAt, now);
        }

        internal static double? Remaining(QuotaWindow quota)
        {
            if (quota == null || double.IsNaN(quota.UsedPercent) || double.IsInfinity(quota.UsedPercent)) return null;
            return Math.Max(0, Math.Min(100, 100 - quota.UsedPercent));
        }

        internal static string QuotaValue(QuotaWindow quota)
        {
            double? value = Remaining(quota);
            return value.HasValue ? Math.Round(value.Value).ToString("0", CultureInfo.InvariantCulture) + "%" : "—";
        }

        internal static string AccountStatus(AccountState a)
        {
            double lowest = 100;
            foreach (QuotaWindow q in a.Windows)
            {
                double? value = Remaining(q);
                if (value.HasValue) lowest = Math.Min(lowest, value.Value);
            }
            return a.Fetching ? "刷新中" : a.RequiresLogin ? "需要登录" :
                a.CooldownUntil > DateTime.UtcNow ? "限流冷却" : a.Stale ? "数据过期" :
                !string.IsNullOrEmpty(a.Error) ? "请求失败" : a.LastSuccess == DateTime.MinValue ? "等待数据" :
                lowest <= 10 ? "余量紧张" : lowest <= 25 ? "余量低" : "";
        }

        private int AccountHeaderH(AccountState a, int width)
        {
            int reserve = StatusWidth(a);
            return Math.Max(S(16), TextHeight(a.Name, _heading, width - S(24) - reserve));
        }

        private int StatusWidth(AccountState a)
        {
            string status = AccountStatus(a);
            return status.Length == 0 ? 0 : TextWidth(status, _small) + S(6);
        }

        private int QuotaLabelWidth { get { return TextWidth("周额度", _small); } }
        private int QuotaValueWidth { get { return Math.Max(S(50), TextWidth("100%", _number) + S(4)); } }
        private int QuotaDetailX { get { return S(8) + QuotaLabelWidth + S(6) + QuotaValueWidth + S(6); } }
        private int QuotaNumberH { get { return TextHeight("100%", _number, QuotaValueWidth) - S(2); } }

        internal static string AccountNotice(AccountState a)
        {
            List<string> messages = new List<string>();
            string status = AccountStatus(a);
            if (a.CooldownUntil > DateTime.UtcNow)
                messages.Add(Math.Ceiling((a.CooldownUntil - DateTime.UtcNow).TotalSeconds) + " 秒后可刷新");
            if (a.Stale && status != "数据过期") messages.Add("数据过期");
            if (!string.IsNullOrEmpty(a.Error) && a.Error != status) messages.Add(a.Error);
            if (!string.IsNullOrEmpty(a.Warning) && a.Warning != status && !messages.Contains(a.Warning)) messages.Add(a.Warning);
            return string.Join(" · ", messages.ToArray());
        }

        private int AccountErrorH(AccountState a, int width)
        {
            string notice = AccountNotice(a);
            return string.IsNullOrEmpty(notice) ? 0 : TextHeight(notice, _small, width - S(24)) + S(6);
        }

        private int MessageH(int width)
        {
            return string.IsNullOrEmpty(_uiMessage) ? 0 : TextHeight(_uiMessage, _small, width - S(24)) + S(12);
        }

        private int QuotaRowH(QuotaWindow q, int width)
        {
            return Math.Max(RowH, TextHeight(QuotaDetail(q), _small, width - S(8) - QuotaDetailX) + S(4));
        }

        private static string Amount(BalanceData b)
        {
            return b == null ? "—" : b.Total.ToString("N2", CultureInfo.InvariantCulture);
        }

        private bool StackedBalance(BalanceData b, int width)
        {
            return TextWidth(Amount(b), _number) + TextWidth(b == null ? "余额" : b.Currency, _text) + S(12) > width - S(24);
        }

        internal string BalanceDisplay(BalanceData balance, int width)
        {
            string value = Amount(balance);
            int available = Math.Max(1, width - S(24));
            List<string> lines = new List<string>();
            string line = "";
            string[] groups = value.Split(',');
            for (int i = 0; i < groups.Length; i++)
            {
                string group = groups[i] + (i < groups.Length - 1 ? "," : "");
                // Break only between integer groups, never within the final decimal group.
                if (line.Length > 0 && TextWidth(line + group, _number) > available)
                { lines.Add(line); line = ""; }
                line += group;
            }
            lines.Add(line);
            return string.Join("\n", lines.ToArray());
        }

        internal string CheckStatusLabel
        {
            get
            {
                return _cfg.LoadError ? "检查已停止" : VisibleAccounts().Count == 0 ? "暂无可检查账号"
                    : _lastRefresh == DateTime.MinValue ? "等待首次检查" : "最近请求结束";
            }
        }

        internal string CheckStatusText
        {
            get { return CheckStatusLabel + (CheckStatusLabel == "最近请求结束" ? " " + _lastRefresh.ToString("HH:mm:ss") : ""); }
        }

        private int BalanceRowH(BalanceData b, int width)
        {
            return StackedBalance(b, width)
                ? S(20) + TextHeight(BalanceDisplay(b, width), _number, width - S(24)) + S(24) : S(48);
        }

        private int AccountH(AccountState a, int width)
        {
            int rows = 0;
            if (a.IsBalance)
            {
                if (a.Balances.Count == 0) rows = BalanceRowH(null, width);
                else foreach (BalanceData b in a.Balances) rows += BalanceRowH(b, width);
            }
            else rows = QuotaRowH(FindWindow(a, WindowKind.FiveHour), width) + QuotaRowH(FindWindow(a, WindowKind.Week), width);
            return AccountHeaderH(a, width) + AccountErrorH(a, width) + rows + S(2);
        }

        private int DesiredWidth(List<AccountState> visible, Rectangle workArea)
        {
            int width = S(234);
            // Fixed type size, content-measured columns: long reset text grows width before wrapping.
            foreach (AccountState a in visible)
                if (!a.IsBalance)
                    foreach (WindowKind kind in new[] { WindowKind.FiveHour, WindowKind.Week })
                        width = Math.Max(width, Math.Min(S(360), QuotaDetailX + TextWidth(QuotaDetail(FindWindow(a, kind)), _small) + S(8)));
            foreach (AccountState a in visible)
                if (a.IsBalance)
                    foreach (BalanceData b in a.Balances)
                        width = Math.Max(width, Math.Min(S(360), S(24) + TextWidth(Amount(b), _number)));
            return Math.Min(width, Math.Max(1, workArea.Width - S(20)));
        }

        private void ResizeForContent(bool preserveRight)
        {
            int right = Right;
            List<AccountState> visible = VisibleAccounts();
            Rectangle wa = Screen.FromRectangle(Bounds).WorkingArea;
            int width = DesiredWidth(visible, wa);
            int body = MessageH(width);
            if (visible.Count == 0) body += S(96);
            else foreach (AccountState a in visible) body += AccountH(a, width);
            _bodyHeight = body;
            int maxHeight = Math.Max(FooterH + 1, (int)(wa.Height * .75));
            int height = Math.Min(body + FooterH, maxHeight);
            Size = new Size(width, height);
            if (preserveRight) Left = right - Width;
            _viewportHeight = Height - FooterH;
            _scroll = Math.Max(0, Math.Min(_scroll, Math.Max(0, _bodyHeight - _viewportHeight)));
            _configure.SetBounds(S(12), S(56) + MessageH(width) - _scroll, Math.Max(1, Width - S(24)), S(32));
            _configure.Visible = visible.Count == 0;
            ClampToScreen();
            if (_activeSettings != null && !_activeSettings.IsDisposed && _activeSettings.Visible)
                PlaceSettingsAbove(_activeSettings);
            Invalidate();
        }

        private Color RemainingColor(double remaining) { return PixelTheme.QuotaColor(remaining, "codex"); }
        private static Color ProviderColor(string provider) { return PixelTheme.Provider(provider); }

        private static QuotaWindow FindWindow(AccountState a, WindowKind kind)
        {
            foreach (QuotaWindow w in a.Windows) if (w.Kind == kind) return w;
            return null;
        }

        private void DrawText(Graphics g, string value, Font font, Color color, Rectangle box, TextFormatFlags flags)
        {
            g.TextRenderingHint = TextRenderingHint.AntiAliasGridFit;
            using (SolidBrush brush = new SolidBrush(color))
            using (StringFormat format = new StringFormat(StringFormat.GenericTypographic))
            {
                format.Alignment = (flags & TextFormatFlags.Right) != 0 ? StringAlignment.Far
                    : (flags & TextFormatFlags.HorizontalCenter) != 0 ? StringAlignment.Center : StringAlignment.Near;
                format.LineAlignment = (flags & TextFormatFlags.VerticalCenter) != 0 ? StringAlignment.Center : StringAlignment.Near;
                if ((flags & TextFormatFlags.WordBreak) == 0) format.FormatFlags |= StringFormatFlags.NoWrap;
                g.DrawString(value ?? "", font, brush, box, format);
            }
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            PaintWidget(e.Graphics);
        }

        private void PaintWidget(Graphics g)
        {
            g.SmoothingMode = SmoothingMode.None;
            g.Clear(Bg);
            List<AccountState> visible = VisibleAccounts();
            using (Bitmap body = new Bitmap(Width, Math.Max(1, _viewportHeight)))
            using (Graphics b = Graphics.FromImage(body))
            {
                b.Clear(Bg);
                int y = -_scroll;
                if (!string.IsNullOrEmpty(_uiMessage))
                {
                    DrawText(b, _uiMessage, _small, Danger,
                        new Rectangle(S(12), y, Width - S(24), MessageH(Width)), TextFormatFlags.WordBreak);
                    y += MessageH(Width);
                }
                if (visible.Count == 0)
                    DrawText(b, "暂无可见账号", _heading, TextColor,
                        new Rectangle(S(12), y + S(8), Width - S(24), S(24)), TextFormatFlags.Left);
                foreach (AccountState a in visible)
                {
                    if (y + AccountH(a, Width) >= 0 && y <= _viewportHeight) PaintAccount(b, a, y);
                    y += AccountH(a, Width);
                }
                g.DrawImageUnscaled(body, 0, 0);
            }
            if (_bodyHeight > _viewportHeight) PaintScrollBar(g);
            using (SolidBrush footer = new SolidBrush(PixelTheme.Footer))
                g.FillRectangle(footer, 0, Height - FooterH, Width, FooterH);
            using (Pen p = new Pen(Line)) g.DrawLine(p, S(12), Height - FooterH, Width - S(12), Height - FooterH);
            string checkLabel = CheckStatusLabel;
            DrawText(g, checkLabel, _small, Muted, new Rectangle(S(12), Height - FooterH, Width - S(24), FooterH),
                TextFormatFlags.Left | TextFormatFlags.VerticalCenter);
            if (checkLabel == "最近请求结束")
                DrawText(g, _lastRefresh.ToString("HH:mm:ss"), _mono, Muted,
                    new Rectangle(Width - S(84), Height - FooterH, S(72), FooterH), TextFormatFlags.Right | TextFormatFlags.VerticalCenter);
        }

        private void PaintAccount(Graphics g, AccountState a, int y)
        {
            int x = 0, w = Width;
            string status = AccountStatus(a);
            int header = AccountHeaderH(a, Width);
            using (SolidBrush surface = new SolidBrush(PixelTheme.ProviderSurface(a.Provider)))
                g.FillRectangle(surface, x, y, w, AccountH(a, Width));
            using (SolidBrush band = new SolidBrush(PixelTheme.ProviderHeader(a.Provider)))
                g.FillRectangle(band, x, y, w, header);
            DrawText(g, a.Name, _heading, PixelTheme.OnAccent,
                new Rectangle(x + S(8), y, w - S(8) - StatusWidth(a), header), TextFormatFlags.WordBreak);
            DrawText(g, status, _small, PixelTheme.OnAccent, new Rectangle(Width - S(8) - StatusWidth(a), y, StatusWidth(a), header),
                TextFormatFlags.Right | TextFormatFlags.VerticalCenter);
            int rowY = y + header;
            string notice = AccountNotice(a);
            if (notice.Length > 0)
            {
                DrawText(g, notice, _small, a.Stale || !string.IsNullOrEmpty(a.Warning) ? Caution : Muted,
                    new Rectangle(x, rowY, w, AccountErrorH(a, Width)), TextFormatFlags.WordBreak);
                rowY += AccountErrorH(a, Width);
            }
            if (a.IsBalance)
            {
                if (a.Balances.Count == 0) PaintBalanceRow(g, null, rowY, a.Stale);
                else foreach (BalanceData b in a.Balances)
                {
                    PaintBalanceRow(g, b, rowY, a.Stale);
                    rowY += BalanceRowH(b, Width);
                }
            }
            else
            {
                QuotaWindow five = FindWindow(a, WindowKind.FiveHour), week = FindWindow(a, WindowKind.Week);
                PaintQuotaRow(g, "5小时", five, rowY, a.Stale, a.Provider);
                PaintQuotaRow(g, "周额度", week, rowY + QuotaRowH(five, Width), a.Stale, a.Provider);
            }
        }

        // Each segment represents 5%. The last segment is clipped; never round it up.
        internal static int SegmentFillWidth(int segmentWidth, double remaining, int index)
        {
            if (double.IsNaN(remaining) || double.IsInfinity(remaining)) return 0;
            double fraction = Math.Max(0, Math.Min(1, remaining / 5.0 - index));
            return (int)Math.Floor(segmentWidth * fraction + 0.00000001);
        }

        private void PaintQuotaRow(Graphics g, string label, QuotaWindow quota, int y, bool stale, string provider)
        {
            int rowHeight = QuotaRowH(quota, Width);
            int valueX = S(8) + QuotaLabelWidth + S(6);
            DrawText(g, label, _small, Muted, new Rectangle(S(8), y, QuotaLabelWidth, QuotaNumberH), TextFormatFlags.VerticalCenter);
            double? remaining = Remaining(quota);
            Color color = stale || !remaining.HasValue ? Muted : PixelTheme.QuotaColor(remaining.Value, provider);
            Rectangle bar = new Rectangle(S(8), y + QuotaNumberH, valueX + QuotaValueWidth - S(8), Math.Max(3, S(5)));
            using (Pen outline = new Pen(PixelTheme.Track))
            using (SolidBrush fill = new SolidBrush(color))
                for (int i = 0; i < 20; i++)
                {
                    int left = bar.X + (int)Math.Round(i * bar.Width / 20.0);
                    int right = bar.X + (int)Math.Round((i + 1) * bar.Width / 20.0) - 1;
                    int width = Math.Max(1, right - left);
                    g.DrawRectangle(outline, left, bar.Y, width - 1, bar.Height - 1);
                    int filled = remaining.HasValue ? SegmentFillWidth(width, remaining.Value, i) : 0;
                    if (filled > 0) g.FillRectangle(fill, left, bar.Y, filled, bar.Height);
                }
            DrawText(g, QuotaValue(quota), _number, remaining.HasValue && !stale ? color : Muted,
                new Rectangle(valueX, y, QuotaValueWidth, QuotaNumberH), TextFormatFlags.Right | TextFormatFlags.VerticalCenter);
            DrawText(g, QuotaDetail(quota), _small, Muted,
                new Rectangle(QuotaDetailX, y, Width - S(8) - QuotaDetailX, rowHeight), TextFormatFlags.WordBreak | TextFormatFlags.VerticalCenter);
        }

        private void PaintBalanceRow(Graphics g, BalanceData b, int y, bool stale)
        {
            string currency = b == null ? "余额" : b.Currency;
            Color color = stale || b == null ? Muted : b.Available ? ProviderColor("deepseek") : Danger;
            bool stacked = StackedBalance(b, Width);
            string value = stacked ? BalanceDisplay(b, Width) : Amount(b);
            int valueY = stacked ? y + S(20) : y;
            int valueH = stacked ? TextHeight(value, _number, Width - S(24)) : S(26);
            DrawText(g, currency, _text, Muted, new Rectangle(S(12), y, Width - S(24), S(22)), TextFormatFlags.VerticalCenter);
            DrawText(g, value, _number, color,
                new Rectangle(stacked ? S(12) : S(64), valueY, Width - (stacked ? S(24) : S(76)), valueH),
                TextFormatFlags.Right | (stacked ? TextFormatFlags.WordBreak : TextFormatFlags.VerticalCenter));
            DrawText(g, b == null ? "等待数据" : b.Available ? "可用余额" : "余额不可用", _small,
                b != null && !b.Available ? Danger : Muted,
                new Rectangle(S(12), valueY + valueH, Width - S(24), S(20)), TextFormatFlags.Left);
        }

        private void PaintScrollBar(Graphics g)
        {
            int track = _viewportHeight - S(12);
            int thumb = Math.Max(S(24), track * _viewportHeight / _bodyHeight);
            int travel = track - thumb;
            int offset = (_bodyHeight - _viewportHeight) == 0 ? 0 :
                travel * _scroll / (_bodyHeight - _viewportHeight);
            using (SolidBrush b = new SolidBrush(PixelTheme.Track))
                g.FillRectangle(b, Width - S(5), S(6) + offset, S(2), thumb);
        }

        protected override void OnMouseWheel(MouseEventArgs e)
        {
            base.OnMouseWheel(e);
            if (_bodyHeight <= _viewportHeight) return;
            _scroll = Math.Max(0, Math.Min(_bodyHeight - _viewportHeight, _scroll - Math.Sign(e.Delta) * S(45)));
            Invalidate();
        }

        internal bool HandleNavigationKey(Keys key)
        {
            if (key == Keys.Apps || key == (Keys.Shift | Keys.F10))
            {
                BuildMenu();
                _menu.Show(this, new Point(S(12), S(12)));
                return true;
            }
            if (key == Keys.Escape) { Hide(); return true; }
            int next = _scroll;
            if (key == Keys.Down) next += RowH;
            else if (key == Keys.Up) next -= RowH;
            else if (key == Keys.PageDown) next += Math.Max(RowH, _viewportHeight - RowH);
            else if (key == Keys.PageUp) next -= Math.Max(RowH, _viewportHeight - RowH);
            else if (key == Keys.Home) next = 0;
            else if (key == Keys.End) next = _bodyHeight;
            else return false;
            _scroll = Math.Max(0, Math.Min(next, Math.Max(0, _bodyHeight - _viewportHeight)));
            ResizeForContent(false);
            return true;
        }

        protected override bool ProcessCmdKey(ref Message msg, Keys keyData)
        {
            return HandleNavigationKey(keyData) || base.ProcessCmdKey(ref msg, keyData);
        }

        internal string AccountAccessibleText(AccountState a)
        {
            List<string> values = new List<string>();
            values.Add(AccountStatus(a));
            values.Add(AccountNotice(a));
            if (a.IsBalance)
            {
                if (a.Balances.Count == 0) values.Add("余额未知，等待数据");
                foreach (BalanceData b in a.Balances)
                    values.Add(b.Currency + " " + Amount(b) + (b.Available ? " 可用余额" : " 余额不可用"));
            }
            else foreach (WindowKind kind in new[] { WindowKind.FiveHour, WindowKind.Week })
            {
                QuotaWindow q = FindWindow(a, kind);
                values.Add((kind == WindowKind.FiveHour ? "5小时剩余 " : "周额度剩余 ") + QuotaValue(q) + "，" + QuotaDetail(q));
            }
            if (a.Stale && a.LastSuccess != DateTime.MinValue)
                values.Add("最近成功 " + a.LastSuccess.ToString("MM-dd HH:mm:ss"));
            values.RemoveAll(string.IsNullOrEmpty);
            return string.Join("；", values.ToArray());
        }

        protected override AccessibleObject CreateAccessibilityInstance() { return new WidgetAccessible(this); }

        private sealed class WidgetAccessible : ControlAccessibleObject
        {
            private readonly WidgetForm _owner;
            internal WidgetAccessible(WidgetForm owner) : base(owner) { _owner = owner; }
            public override int GetChildCount() { return _owner.VisibleAccounts().Count + 1 + base.GetChildCount(); }
            public override AccessibleObject GetChild(int index)
            {
                List<AccountState> visible = _owner.VisibleAccounts();
                if (index < 0) return null;
                if (index < visible.Count) return new DataAccessible(_owner, visible[index]);
                if (index == visible.Count) return new DataAccessible(_owner, null);
                return base.GetChild(index - visible.Count - 1);
            }
        }

        private sealed class DataAccessible : AccessibleObject
        {
            private readonly WidgetForm _owner;
            private readonly AccountState _account;
            internal DataAccessible(WidgetForm owner, AccountState account) { _owner = owner; _account = account; }
            public override AccessibleObject Parent { get { return _owner.AccessibilityObject; } }
            public override string Name { get { return _account == null ? "最近一次请求完成时间" : _account.Name; } set { } }
            public override string Value
            {
                get
                {
                    return _account == null ? _owner.CheckStatusText
                        : _owner.AccountAccessibleText(_account);
                }
                set { }
            }
            public override string Description { get { return _account == null ? "不代表所有账号均成功更新。" : "剩余额度、重置时间及数据有效性。"; } }
            public override AccessibleRole Role { get { return AccessibleRole.StaticText; } }
            public override Rectangle Bounds
            {
                get
                {
                    if (!_owner.IsHandleCreated || !_owner.Visible) return Rectangle.Empty;
                    if (_account == null) return _owner.RectangleToScreen(new Rectangle(0, _owner.Height - _owner.FooterH, _owner.Width, _owner.FooterH));
                    int y = _owner.S(8) + _owner.MessageH(_owner.Width) - _owner._scroll;
                    foreach (AccountState a in _owner.VisibleAccounts())
                    {
                        int h = _owner.AccountH(a, _owner.Width);
                        if (a == _account)
                        {
                            Rectangle r = Rectangle.Intersect(new Rectangle(0, y, _owner.Width, h), new Rectangle(0, 0, _owner.Width, _owner._viewportHeight));
                            return r.IsEmpty ? Rectangle.Empty : _owner.RectangleToScreen(r);
                        }
                        y += h;
                    }
                    return Rectangle.Empty;
                }
            }
            public override AccessibleStates State { get { return AccessibleStates.ReadOnly | (Bounds.IsEmpty ? AccessibleStates.Offscreen : AccessibleStates.None); } }
        }

        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.Button != MouseButtons.Left) return;
            if (e.Y >= Height - FooterH) return;
            _pressing = true; _dragging = false; _downScreen = Cursor.Position;
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            bool footer = e.Y >= Height - FooterH;
            if (footer != _overFooter)
            {
                _overFooter = footer;
                _footerTip.SetToolTip(this, footer ? "最近一次请求完成时间；不代表所有账号均成功更新。" : null);
            }
            if (!_pressing || _dragging) return;
            Size d = SystemInformation.DragSize;
            if (Math.Abs(Cursor.Position.X - _downScreen.X) < d.Width &&
                Math.Abs(Cursor.Position.Y - _downScreen.Y) < d.Height) return;
            _dragging = true;
            ReleaseCapture();
            SendMessage(Handle, 0xA1, (IntPtr)2, IntPtr.Zero);
            ClampToScreen();
            SaveUi();
        }

        protected override void OnMouseUp(MouseEventArgs e)
        {
            base.OnMouseUp(e);
            _pressing = false; _dragging = false;
        }

        protected override void OnMouseClick(MouseEventArgs e)
        {
            base.OnMouseClick(e);
            if (e.Button == MouseButtons.Right) { BuildMenu(); _menu.Show(Cursor.Position); }
        }

        private void InitTray()
        {
            _tray = new NotifyIcon { Text = "AI 额度", Visible = true };
            UpdateTrayIcon();
            _tray.MouseClick += delegate(object sender, MouseEventArgs e)
            {
                if (e.Button != MouseButtons.Left) return;
                if (Visible) Hide(); else ShowFromTray();
            };
            BuildMenu();
        }

        private Icon MakeTrayIcon(Color c)
        {
            using (Bitmap bitmap = new Bitmap(16, 16))
            {
                using (Graphics g = Graphics.FromImage(bitmap))
                {
                    g.Clear(Bg);
                    using (SolidBrush b = new SolidBrush(c)) g.FillRectangle(b, 3, 3, 10, 10);
                }
                IntPtr handle = bitmap.GetHicon();
                Icon copy = (Icon)Icon.FromHandle(handle).Clone();
                DestroyIcon(handle);
                return copy;
            }
        }

        private void UpdateTrayIcon()
        {
            if (_tray == null) return;
            double worst = 100;
            foreach (AccountState a in _accounts)
                if (a.Visible)
                    foreach (QuotaWindow q in a.Windows) worst = Math.Min(worst, 100 - q.UsedPercent);
            Icon old = _trayIcon;
            _trayIcon = MakeTrayIcon(RemainingColor(worst));
            _tray.Icon = _trayIcon;
            if (old != null) old.Dispose();
        }

        private void BuildMenu()
        {
            if (_menu != null) { _menu.Dispose(); _menu = null; }
            _menu = new ContextMenuStrip { BackColor = Bg, ForeColor = TextColor,
                ShowImageMargin = false, ShowCheckMargin = true, Font = _text, Renderer = new DispatchMenuRenderer() };
            _menu.Items.Add(MenuItem("立即刷新", delegate { RefreshNow(); }));
            _menu.Items.Add(MenuItem("设置…", delegate { ShowSettings(false); }));
            ToolStripMenuItem accounts = new ToolStripMenuItem("显示账号") { ForeColor = TextColor };
            foreach (AccountState acc in _accounts)
            {
                AccountState a = acc;
                ToolStripMenuItem item = MenuItem(a.Name, delegate
                {
                    a.Visible = !a.Visible;
                    if (a.Provider == "codex") _cfg.Codex.Visible = a.Visible;
                    else if (a.Provider == "deepseek") _cfg.DeepSeek.Visible = a.Visible;
                    else
                    {
                        foreach (ZhipuCfg z in _cfg.Zhipu)
                            if ("zhipu:" + z.Id == a.Key) { z.Visible = a.Visible; break; }
                    }
                    SaveUi(); ResizeForContent(true);
                    _coordinator.Reconcile(_cfg);
                    if (!_cfg.LoadError) _coordinator.RefreshDue();
                    SafeRebuildMenu();
                });
                item.Checked = a.Visible;
                accounts.DropDownItems.Add(item);
            }
            _menu.Items.Add(accounts);
            _menu.Items.Add(new ToolStripSeparator());
            ToolStripMenuItem top = MenuItem("置顶显示", delegate
            {
                _cfg.Ui.TopMost = !_cfg.Ui.TopMost; TopMost = _cfg.Ui.TopMost; SaveUi(); SafeRebuildMenu();
            });
            top.Checked = _cfg.Ui.TopMost;
            _menu.Items.Add(top);
            ToolStripMenuItem auto = MenuItem("开机自启", delegate
            {
                if (_mock) return;
                bool enable = !_getAutostart();
                if (!_setAutostart(enable, Application.ExecutablePath) || _getAutostart() != enable)
                {
                    _uiMessage = AutostartError;
                    ResizeForContent(false);
                }
                else if (_uiMessage == AutostartError)
                {
                    _uiMessage = null;
                    ResizeForContent(false);
                }
                SafeRebuildMenu();
            });
            auto.Checked = !_mock && _getAutostart();
            auto.Enabled = !_mock;
            _menu.Items.Add(auto);
            _menu.Items.Add(new ToolStripSeparator());
            _menu.Items.Add(MenuItem("退出", delegate { ExitApp(); }));
            if (_tray != null) _tray.ContextMenuStrip = _menu;
        }

        internal void OpenMenuForDemo(bool openSubmenu)
        {
            Shown += delegate
            {
                BeginInvoke((Action)delegate
                {
                    BuildMenu();
                    _menu.Show(new Point(Left + S(35), Top + S(30)));
                    if (openSubmenu)
                        foreach (ToolStripItem item in _menu.Items)
                        {
                            ToolStripMenuItem menuItem = item as ToolStripMenuItem;
                            if (menuItem != null && menuItem.Text == "显示账号")
                            { menuItem.ShowDropDown(); break; }
                        }
                });
            };
        }

        internal void OpenSettingsForDemo()
        {
            Shown += delegate { BeginInvoke((Action)delegate { ShowSettings(false); }); };
        }

        private ToolStripMenuItem MenuItem(string title, Action action)
        {
            ToolStripMenuItem item = new ToolStripMenuItem(title) { ForeColor = TextColor,
                Padding = new Padding(8, 5, 8, 5) };
            item.Click += delegate { action(); };
            return item;
        }

        private void SafeRebuildMenu()
        {
            if (!IsDisposed && IsHandleCreated) BeginInvoke((Action)BuildMenu);
        }

        private void ShowSettings(bool opacity)
        {
            _cfg.Ui.Left = Left; _cfg.Ui.Top = Top;
            Point originalLocation = Location;
            using (SettingsForm settings = new SettingsForm(_cfg, opacity, !_mock, _mock ? _scale : 0, AppConfig.Save))
            {
                // The settings HWND already exists after DPI measurement; assigning a
                // modal owner alone does not move it into the owner's topmost band.
                settings.TopMost = TopMost;
                PlaceSettingsAbove(settings);
                if (_mock) settings.Shown += delegate { settings.PreviewState(_mockScenario); };
                settings.Shown += delegate { settings.BringToFront(); settings.Activate(); };
                DialogResult result;
                _activeSettings = settings;
                try { result = settings.ShowDialog(this); }
                finally
                {
                    _activeSettings = null;
                    if (!IsDisposed)
                    {
                        ResizeForContent(false);
                        Location = originalLocation;
                        ClampToScreen();
                    }
                }
                if (result != DialogResult.OK) return;
                _cfg = settings.UpdatedConfig;
                TopMost = _cfg.Ui.TopMost;
                _coordinator.Reconcile(_cfg);
                _accounts = _coordinator.Accounts;
                _uiMessage = null;
                ResizeForContent(false);
                BuildMenu();
                _coordinator.RefreshDue();
            }
        }

        private void PlaceSettingsAbove(SettingsForm settings)
        {
            PlaceSettingsAbove(settings, Screen.FromRectangle(Bounds).WorkingArea);
        }

        internal void PlaceSettingsAbove(SettingsForm settings, Rectangle work)
        {
            int gap = S(8);
            settings.StartPosition = FormStartPosition.Manual;
            // Reserve enough room for the dialog's fixed footer and a scrollable body.
            int minSettingsHeight = Math.Min(settings.Height, S(160));
            int maxWidgetHeight = Math.Max(FooterH + 1, work.Height - minSettingsHeight - gap);
            if (Height > maxWidgetHeight)
            {
                Height = maxWidgetHeight;
                _viewportHeight = Math.Max(1, Height - FooterH);
                _scroll = Math.Max(0, Math.Min(_scroll, Math.Max(0, _bodyHeight - _viewportHeight)));
            }
            settings.Height = Math.Min(settings.Height, Math.Max(1, work.Height - Height - gap));
            Top = Math.Min(Math.Max(Top, work.Top + settings.Height + gap), work.Bottom - Height);
            int x = Math.Max(work.Left, Math.Min(Right - settings.Width, work.Right - settings.Width));
            settings.Location = new Point(x, Top - gap - settings.Height);
            Invalidate();
        }

        public void ShowFromTray()
        {
            if (_activeSettings != null && !_activeSettings.IsDisposed && _activeSettings.Visible)
            {
                _activeSettings.BringToFront();
                _activeSettings.Activate();
                return;
            }
            Show(); WindowState = FormWindowState.Normal; TopMost = _cfg.Ui.TopMost; Activate();
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            if (!_exiting && e.CloseReason == CloseReason.UserClosing)
            {
                e.Cancel = true; Hide(); return;
            }
            base.OnFormClosing(e);
        }

        private void ExitApp()
        {
            _exiting = true;
            if (_coordinator != null) _coordinator.Dispose();
            Program.StopSignalWorker();
            Application.Exit();
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing && !_resourcesDisposed)
            {
                _resourcesDisposed = true;
                _exiting = true;
                if (_coordinator != null) _coordinator.Dispose();
                if (_tick != null) { _tick.Stop(); _tick.Dispose(); }
                if (_tray != null) { _tray.Visible = false; _tray.Dispose(); }
                if (_trayIcon != null) _trayIcon.Dispose();
                _footerTip.Dispose();
                if (_menu != null) _menu.Dispose();
                foreach (Font font in new[] { _text, _small, _heading, _number, _mono })
                    if (font != null) font.Dispose();
            }
            base.Dispose(disposing);
        }

        private void SaveUi()
        {
            if (_mock || _cfg == null) return;
            _cfg.Ui.Left = Left; _cfg.Ui.Top = Top;
            _cfg.Ui.TopMost = TopMost;
            _uiMessage = AppConfig.Save(_cfg) ? null :
                "配置保存失败；本次设置仅在当前运行生效。请检查配置和写入权限。";
            ResizeForContent(false);
        }

        private void OnTick(object sender, EventArgs e)
        {
            _ticks++;
            if (_cfg.Ui.TopMost && _ticks % 30 == 0 && !TopMost) TopMost = true;
            if (!_cfg.LoadError) _coordinator.RefreshDue();
            ResizeForContent(false);
        }

        public void RefreshNow()
        {
            if (!_cfg.LoadError) _coordinator.RefreshNow();
            Invalidate();
        }

        private static FetchResult MockResult(string provider, string scenario)
        {
            if (scenario == "login" && provider == "codex") return new FetchResult { Error = "请在 Codex 客户端重新登录", RequiresLogin = true, StatusCode = 401 };
            if (scenario == "limited") return new FetchResult { Error = "请求过于频繁", StatusCode = 429 };
            if (scenario == "empty") return new FetchResult { Error = "未配置 API Key" };
            if (scenario == "error" || scenario == "stale" || scenario == "refresh-error")
                return new FetchResult { Error = "网络连接失败", StatusCode = 0 };
            if (scenario == "unknown" && provider != "deepseek") return new FetchResult { Ok = true, Windows = new List<QuotaWindow>() };
            if (scenario == "extreme" && provider == "deepseek") return new FetchResult { Ok = true,
                Balances = new List<BalanceData> { new BalanceData { Currency = "CNY", Total = decimal.MaxValue, Available = true },
                    new BalanceData { Currency = "USD", Total = .01m, Available = true } } };
            if (provider == "deepseek") return new FetchResult { Ok = true,
                Warning = scenario == "partial" ? "部分余额数据无法识别，已保留有效币种" : null,
                Balances = new List<BalanceData> { new BalanceData { Currency = "CNY", Total = 42.50m },
                    new BalanceData { Currency = "USD", Total = 7.25m } } };
            long now = scenario == "reference" ? (long)(ReferenceTime.ToUniversalTime() - new DateTime(1970, 1, 1)).TotalSeconds : Providers.NowUnixSeconds();
            return new FetchResult { Ok = true, Windows = new List<QuotaWindow> {
                new QuotaWindow { Kind = WindowKind.FiveHour, UsedPercent = provider == "codex" ? 26 : 78, ResetAt = now + 8100 },
                new QuotaWindow { Kind = WindowKind.Week, UsedPercent = provider == "codex" ? 64 : 91, ResetAt = now + 315000 }
            } };
        }


    }

    internal sealed class DispatchMenuRenderer : ToolStripProfessionalRenderer
    {
        private static Color Bg { get { return PixelTheme.Surface; } }
        private static Color Hover { get { return PixelTheme.Selected; } }
        private static Color Accent { get { return PixelTheme.Focus; } }
        public DispatchMenuRenderer() : base(new Colors()) { }
        protected override void OnRenderItemCheck(ToolStripItemImageRenderEventArgs e)
        {
            Rectangle r = e.ImageRectangle;
            int unit = Math.Max(1, r.Width / 8);
            using (SolidBrush brush = new SolidBrush(Accent))
            {
                e.Graphics.FillRectangle(brush, r.X + unit, r.Y + 3 * unit, 2 * unit, 3 * unit);
                e.Graphics.FillRectangle(brush, r.X + 3 * unit, r.Y + 4 * unit, 2 * unit, 2 * unit);
                e.Graphics.FillRectangle(brush, r.X + 5 * unit, r.Y + unit, 2 * unit, 4 * unit);
            }
        }
        protected override void OnRenderItemText(ToolStripItemTextRenderEventArgs e)
        {
            e.TextColor = !e.Item.Enabled ? PixelTheme.Disabled : SystemInformation.HighContrast && e.Item.Selected
                ? SystemColors.HighlightText : PixelTheme.Text;
            base.OnRenderItemText(e);
        }
        protected override void OnRenderArrow(ToolStripArrowRenderEventArgs e)
        {
            e.ArrowColor = e.Item.Enabled ? PixelTheme.Text : PixelTheme.Disabled;
            base.OnRenderArrow(e);
        }
        private sealed class Colors : ProfessionalColorTable
        {
            public override Color ToolStripDropDownBackground { get { return Bg; } }
            public override Color ImageMarginGradientBegin { get { return Bg; } }
            public override Color ImageMarginGradientMiddle { get { return Bg; } }
            public override Color ImageMarginGradientEnd { get { return Bg; } }
            public override Color MenuBorder { get { return Hover; } }
            public override Color MenuItemSelected { get { return Hover; } }
            public override Color MenuItemSelectedGradientBegin { get { return Hover; } }
            public override Color MenuItemSelectedGradientEnd { get { return Hover; } }
            public override Color SeparatorDark { get { return Hover; } }
            public override Color SeparatorLight { get { return Hover; } }
        }
    }
}
