using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;

namespace QuotaWidget
{
    public class AccountState
    {
        public string Key;
        public string Name;
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

    public class WidgetForm : Form
    {
        private AppConfig _cfg;
        private readonly List<AccountState> _accounts = new List<AccountState>();
        private NotifyIcon _tray;
        private ContextMenuStrip _menu;
        private System.Windows.Forms.Timer _tick;
        private DateTime _nextRefresh = DateTime.MinValue;
        private DateTime _lastRefresh = DateTime.MinValue;
        private bool _refreshing;
        private bool _exiting;
        private bool _collapsed;
        private bool _dragging;
        private Point _dragOffset;
        private int _expandedTick;
        private float _scale = 1f;
        private Font _font;
        private Font _fontSmall;
        private Font _fontBold;
        private Rectangle _rectCollapse;
        private Rectangle _rectClose;
        private readonly List<KeyValuePair<Rectangle, AccountState>> _cardRects =
            new List<KeyValuePair<Rectangle, AccountState>>();
        private Icon _trayIcon;
        private bool _balloonTemplateShown;
        private bool _balloonHideShown;

        // 配色
        private static readonly Color ColBg = Color.FromArgb(23, 24, 28);
        private static readonly Color ColCard = Color.FromArgb(32, 34, 40);
        private static readonly Color ColCardBorder = Color.FromArgb(46, 49, 56);
        private static readonly Color ColBarBg = Color.FromArgb(51, 54, 61);
        private static readonly Color ColText = Color.FromArgb(232, 232, 232);
        private static readonly Color ColSub = Color.FromArgb(154, 160, 166);
        private static readonly Color ColGreen = Color.FromArgb(76, 195, 138);
        private static readonly Color ColYellow = Color.FromArgb(242, 193, 78);
        private static readonly Color ColRed = Color.FromArgb(229, 83, 75);

        [DllImport("user32.dll")]
        private static extern bool DestroyIcon(IntPtr hIcon);

        public WidgetForm(AppConfig cfg)
        {
            _cfg = cfg;
            _collapsed = cfg.Ui.Collapsed;
            BuildAccountsFromConfig(null);
            InitForm();
            EnsureScaleFonts();
            InitTray();
            BuildMenu();
            _tick = new System.Windows.Forms.Timer();
            _tick.Interval = 1000;
            _tick.Tick += OnTick;
            _tick.Start();
            _nextRefresh = DateTime.Now.AddSeconds(2);
        }

        // ---------- 初始化 ----------

        private void InitForm()
        {
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
            if (_cfg.Ui.Left >= 0 && _cfg.Ui.Top >= 0)
            {
                Location = new Point(_cfg.Ui.Left, _cfg.Ui.Top); // -1/-1 是模板哨兵值，表示未设置
            }
            else
            {
                Rectangle wa = Screen.PrimaryScreen.WorkingArea;
                Location = new Point(wa.Right - 480, wa.Bottom - 340);
            }
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
            _font = new Font("Microsoft YaHei UI", 9f);
            _fontSmall = new Font("Microsoft YaHei UI", 8f);
            _fontBold = new Font("Microsoft YaHei UI", 9f, FontStyle.Bold);
            _toolTip = new ToolTip();
            _toolTip.SetToolTip(this, "拖动移动 · 双击刷新 · 右键菜单");
            RecalcSize();
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
        }

        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);
            Program.StartSignalWorker(this); // 句柄就绪后再启动，避免早期唤起信号被吞
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
            RecalcSize();
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

        // ---------- 尺寸布局 ----------

        private int S(int px) { return (int)Math.Round(px * _scale); }
        private int TitleH() { return S(30); }
        private int FooterH() { return S(22); }
        private int RowH() { return S(22); }

        private int CardHeight(AccountState acc)
        {
            int rows = acc.IsBalance ? 1 : MaxRows(acc);
            return S(24) + rows * RowH() + S(6); // 24 = 头部行高，含头部行自身空间
        }

        private List<QuotaWindow> SortedWindows(AccountState acc)
        {
            List<QuotaWindow> ws = new List<QuotaWindow>(acc.Windows);
            ws.Sort(delegate(QuotaWindow a, QuotaWindow b) { return ((int)a.Kind).CompareTo((int)b.Kind); });
            return ws;
        }

        private int MaxRows(AccountState acc)
        {
            List<QuotaWindow> ws = SortedWindows(acc);
            if (ws.Count == 0) return 1;
            return Math.Min(3, ws.Count);
        }

        private void RecalcSize()
        {
            if (_collapsed)
            {
                ClientSize = new Size(S(64), S(64));
            }
            else
            {
                int w = S(440);
                int h = S(4) + TitleH();
                foreach (AccountState acc in _accounts)
                {
                    if (!acc.Visible) continue;
                    h += CardHeight(acc) + S(6);
                }
                h += FooterH() + S(4);
                ClientSize = new Size(w, h);
            }
            Invalidate();
        }

        // ---------- 绘制 ----------

        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.ClearTypeGridFit;
            _rectCollapse = Rectangle.Empty;
            _rectClose = Rectangle.Empty;
            _cardRects.Clear();
            if (_collapsed) PaintCollapsed(g);
            else PaintExpanded(g);
        }

        private Color StatusColor(double pct)
        {
            if (pct >= _cfg.WarnThreshold) return ColRed;
            if (pct >= 60) return ColYellow;
            return ColGreen;
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

        private static Color Lerp(Color a, Color b, double t)
        {
            return Color.FromArgb(
                (int)(a.R + (b.R - a.R) * t),
                (int)(a.G + (b.G - a.G) * t),
                (int)(a.B + (b.B - a.B) * t));
        }

        private void PaintExpanded(Graphics g)
        {
            Rectangle client = ClientRectangle;
            using (SolidBrush bg = new SolidBrush(ColBg)) g.FillRectangle(bg, client);

            int y = S(4);
            Rectangle titleRect = new Rectangle(0, y, client.Width, TitleH());
            TextRenderer.DrawText(g, "⚡ AI 额度", _fontBold, new Point(S(10), y + S(4)), ColText);

            int btnW = S(24);
            int btnH = S(20);
            _rectClose = new Rectangle(client.Width - btnW - S(8), y + S(5), btnW, btnH);
            _rectCollapse = new Rectangle(client.Width - btnW * 2 - S(12), y + S(5), btnW, btnH);
            TextRenderer.DrawText(g, "—", _font, _rectCollapse, ColSub, TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter);
            TextRenderer.DrawText(g, "✕", _font, _rectClose, ColSub, TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter);
            y += TitleH();

            bool flashOn = (Environment.TickCount / 500) % 2 == 0;

            foreach (AccountState acc in _accounts)
            {
                if (!acc.Visible) continue;
                Rectangle card = new Rectangle(S(8), y, client.Width - S(16), CardHeight(acc));
                _cardRects.Add(new KeyValuePair<Rectangle, AccountState>(card, acc));

                bool warn = false;
                foreach (QuotaWindow w in acc.Windows)
                {
                    if (w.UsedPercent >= _cfg.WarnThreshold) warn = true;
                }
                Color cardBg = warn && flashOn ? Lerp(ColCard, ColRed, 0.28) : ColCard;
                using (GraphicsPath path = RoundRect(card, S(8)))
                {
                    using (SolidBrush b = new SolidBrush(cardBg)) g.FillPath(b, path);
                    using (Pen p = new Pen(ColCardBorder)) g.DrawPath(p, path);
                }

                // 头部：状态点 + 名称
                double accWorst = 0;
                foreach (QuotaWindow w in acc.Windows)
                {
                    if (w.UsedPercent > accWorst) accWorst = w.UsedPercent;
                }
                Color dot = acc.IsBalance
                    ? (acc.Balance != null && !acc.Balance.Available ? ColYellow : ColGreen)
                    : (acc.Windows.Count > 0 ? StatusColor(accWorst) : ColSub);
                using (SolidBrush b = new SolidBrush(dot))
                {
                    g.FillEllipse(b, card.X + S(10), card.Y + S(7), S(8), S(8));
                }
                string header = acc.Name + (acc.Stale ? "（过期）" : "");
                TextRenderer.DrawText(g, header, _fontBold,
                    new Point(card.X + S(24), card.Y + S(3)), ColText);
                if (!string.IsNullOrEmpty(acc.Warning))
                {
                    SizeF hs = g.MeasureString(header, _fontBold);
                    TextRenderer.DrawText(g, "⚠ " + acc.Warning, _fontSmall,
                        new Point(card.X + S(24) + (int)hs.Width + S(6), card.Y + S(5)), ColYellow);
                }

                int rowY = card.Y + S(24);
                if (acc.IsBalance)
                {
                    DrawBalanceRow(g, acc, card, rowY);
                }
                else if (acc.Windows.Count == 0)
                {
                    string msg = string.IsNullOrEmpty(acc.Error) ? "等待数据…" : "刷新失败";
                    TextRenderer.DrawText(g, msg, _fontSmall,
                        new Point(card.X + S(12), rowY), string.IsNullOrEmpty(acc.Error) ? ColSub : ColRed);
                    if (!string.IsNullOrEmpty(acc.Error))
                    {
                        SizeF ts = g.MeasureString(msg, _fontSmall);
                        TextRenderer.DrawText(g, "（" + Providers.Truncate(acc.Error, 42) + "）", _fontSmall,
                            new Point(card.X + S(12) + (int)ts.Width, rowY), ColSub);
                    }
                }
                else
                {
                    List<QuotaWindow> ws = SortedWindows(acc);
                    int rows = Math.Min(3, ws.Count);
                    for (int i = 0; i < rows; i++)
                    {
                        DrawWindowRow(g, acc, ws[i], card, rowY + i * RowH(), acc.Stale);
                    }
                }
                y += card.Height + S(6);
            }

            // 底栏
            Rectangle footer = new Rectangle(0, client.Bottom - FooterH() - S(2), client.Width, FooterH());
            string last = _lastRefresh == DateTime.MinValue ? "—" : _lastRefresh.ToString("HH:mm:ss");
            string footerText = "上次刷新 " + last + " · 每 " + _cfg.RefreshIntervalSeconds + "s";
            TextRenderer.DrawText(g, footerText, _fontSmall, new Point(S(10), footer.Y), ColSub);
            string hint = _refreshing ? "刷新中…" : "右键菜单 · 双击刷新";
            TextRenderer.DrawText(g, hint, _fontSmall, footer, ColSub,
                TextFormatFlags.Right | TextFormatFlags.VerticalCenter);
        }

        private void DrawWindowRow(Graphics g, AccountState acc, QuotaWindow w, Rectangle card, int y, bool stale)
        {
            int labelW = S(34);
            int barX = card.X + S(12) + labelW + S(4);
            int barW = S(150);
            int barH = S(9);
            int barY = y + (RowH() - barH) / 2;

            Color accent = StatusColor(w.UsedPercent);
            if (stale) accent = Color.FromArgb(140, accent);

            TextRenderer.DrawText(g, w.Label(), _fontSmall,
                new Rectangle(card.X + S(12), y, labelW, RowH()), ColSub,
                TextFormatFlags.Left | TextFormatFlags.VerticalCenter);

            Rectangle barBg = new Rectangle(barX, barY, barW, barH);
            using (GraphicsPath path = RoundRect(barBg, barH / 2))
            using (SolidBrush b = new SolidBrush(ColBarBg)) g.FillPath(b, path);

            int fillW = (int)(barW * w.UsedPercent / 100.0 + 0.5);
            if (fillW > 0)
            {
                if (fillW < barH) fillW = barH;
                if (fillW > barW) fillW = barW;
                Rectangle fill = new Rectangle(barX, barY, fillW, barH);
                using (GraphicsPath path = RoundRect(fill, barH / 2))
                using (SolidBrush b = new SolidBrush(accent)) g.FillPath(b, path);
            }

            string pctText = Math.Round(w.UsedPercent) + "%";
            SizeF ps = g.MeasureString(pctText, _fontSmall);
            TextRenderer.DrawText(g, pctText, _fontSmall,
                new Point(barX + barW + S(6), y), stale ? ColSub : ColText);

            string reset = Providers.FormatCountdown(w.ResetAt);
            string rightText = reset == null ? "--" : reset + " 后重置";
            Rectangle rightRect = new Rectangle((int)(barX + barW + S(6) + ps.Width) + S(4), y,
                card.Right - S(10) - (int)(barX + barW + S(6) + ps.Width) - S(4), RowH());
            TextRenderer.DrawText(g, rightText, _fontSmall, rightRect, ColSub,
                TextFormatFlags.Right | TextFormatFlags.VerticalCenter);
        }

        private void DrawBalanceRow(Graphics g, AccountState acc, Rectangle card, int y)
        {
            if (acc.Balance == null)
            {
                string msg = string.IsNullOrEmpty(acc.Error) ? "等待数据…" : "刷新失败（" + Providers.Truncate(acc.Error, 36) + "）";
                TextRenderer.DrawText(g, msg, _fontSmall, new Point(card.X + S(12), y),
                    string.IsNullOrEmpty(acc.Error) ? ColSub : ColRed);
                return;
            }
            BalanceData b = acc.Balance;
            string symbol = b.Currency == "CNY" ? "¥" : (b.Currency == "USD" ? "$" : b.Currency + " ");
            string text = "余额 " + symbol + b.Total.ToString("0.00", System.Globalization.CultureInfo.InvariantCulture);
            if (b.Granted != null && b.Granted.Value > 0)
                text += " · 赠送 " + symbol + b.Granted.Value.ToString("0.00", System.Globalization.CultureInfo.InvariantCulture);
            if (!b.Available) text += "（不可用）";
            TextRenderer.DrawText(g, text, _font, new Point(card.X + S(12), y), ColText);
        }

        private void PaintCollapsed(Graphics g)
        {
            Rectangle client = ClientRectangle;
            using (SolidBrush bg = new SolidBrush(ColBg)) g.FillRectangle(bg, client);
            int inset = S(4);
            Rectangle circle = new Rectangle(inset, inset, client.Width - inset * 2, client.Height - inset * 2);
            using (SolidBrush b = new SolidBrush(ColCard)) g.FillEllipse(b, circle);
            using (Pen p = new Pen(ColCardBorder, 1.4f)) g.DrawEllipse(p, circle);

            double pct = WorstPercent();
            using (Pen pen = new Pen(StatusColor(pct), S(5)))
            {
                g.DrawArc(pen, new Rectangle(circle.X + S(5), circle.Y + S(5), circle.Width - S(10), circle.Height - S(10)),
                    -90, (float)(Math.Max(0.5, pct) / 100.0 * 360.0));
            }
            string text = Math.Round(pct) + "%";
            TextRenderer.DrawText(g, text, _fontBold, client, ColText,
                TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter);
        }

        // ---------- 交互 ----------

        private ToolTip _toolTip;

        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.Button != MouseButtons.Left) return;
            if (!_collapsed && Environment.TickCount - _expandedTick < 350) return; // 展开瞬间的双击第二下，避免误点按钮
            if (!_collapsed && _rectClose.Contains(e.Location)) { HideToTray(); return; }
            if (!_collapsed && _rectCollapse.Contains(e.Location)) { ToggleCollapse(); return; }
            if (_collapsed) { ToggleCollapse(); return; }
            _dragging = true;
            _dragOffset = e.Location;
            Capture = true;
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            if (!_dragging) return;
            Point scr = PointToScreen(e.Location);
            Location = new Point(scr.X - _dragOffset.X, scr.Y - _dragOffset.Y);
        }

        protected override void OnMouseUp(MouseEventArgs e)
        {
            base.OnMouseUp(e);
            if (e.Button == MouseButtons.Left && _dragging)
            {
                _dragging = false;
                Capture = false;
                SaveUi();
            }
        }

        protected override void OnMouseDoubleClick(MouseEventArgs e)
        {
            base.OnMouseDoubleClick(e);
            if (e.Button == MouseButtons.Left) RefreshNow();
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

        private void ToggleCollapse()
        {
            bool wasCollapsed = _collapsed;
            _collapsed = !_collapsed;
            if (wasCollapsed)
            {
                _expandedTick = Environment.TickCount;
                _dragging = false;
                Capture = false;
            }
            _cfg.Ui.Collapsed = _collapsed;
            SaveUi();
            RecalcSize();
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
            if (_tick != null)
            {
                _tick.Stop();
                _tick.Dispose();
                _tick = null;
            }
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
                try { DestroyIcon(old.Handle); } catch { }
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

        // 菜单自身仍打开时不可立即 Dispose 重建，延迟到消息循环下一轮
        private void SafeRebuildMenu()
        {
            if (IsDisposed || !IsHandleCreated) return;
            try { BeginInvoke((Action)delegate { BuildMenu(); }); }
            catch { }
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
                    RecalcSize();
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
                SaveUi();
                SafeRebuildMenu();
            };
            parent.DropDownItems.Add(mi);
        }

        // ---------- 刷新 ----------

        private void OnTick(object sender, EventArgs e)
        {
            // 持续重申置顶，防止被其他置顶窗口抢占
            if (_cfg.Ui.TopMost && !TopMost) TopMost = true;
            if (!_refreshing && _nextRefresh != DateTime.MinValue && DateTime.Now >= _nextRefresh)
            {
                RefreshNow();
            }
            Invalidate();
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
                        _nextRefresh = DateTime.Now.AddSeconds(Math.Max(60, _cfg.RefreshIntervalSeconds));
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

        // ---------- 配置持久化 ----------

        private void SaveUi()
        {
            _cfg.Ui.Left = Location.X;
            _cfg.Ui.Top = Location.Y;
            _cfg.Ui.Collapsed = _collapsed;
            _cfg.Ui.Opacity = Opacity;
            _cfg.Ui.TopMost = TopMost;
            AppConfig.Save(_cfg);
        }
    }
}
