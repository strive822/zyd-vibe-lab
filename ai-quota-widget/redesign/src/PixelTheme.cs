using System;
using System.Drawing;
using System.Windows.Forms;

namespace QuotaWidget
{
    // Shared presentation tokens. No provider, configuration or scheduling policy lives here.
    internal static class PixelTheme
    {
        private static Color Pick(string hex, Color system) { return SystemInformation.HighContrast ? system : ColorTranslator.FromHtml(hex); }
        internal static Color Background { get { return Pick("#1E3A50", SystemColors.Window); } }
        internal static Color Surface { get { return Pick("#284D61", SystemColors.Window); } }
        internal static Color Footer { get { return Pick("#284B60", SystemColors.Window); } }
        internal static Color Text { get { return Pick("#F2F6FC", SystemColors.WindowText); } }
        internal static Color Secondary { get { return Pick("#D0E2EC", SystemColors.WindowText); } }
        internal static Color Accent { get { return Pick("#42E8E0", SystemColors.Highlight); } }
        internal static Color Focus { get { return Pick("#42E8E0", SystemColors.WindowText); } }
        internal static Color Warning { get { return Pick("#FFBF47", SystemColors.WindowText); } }
        internal static Color Error { get { return Pick("#FF9FAF", SystemColors.WindowText); } }
        internal static Color OnAccent { get { return Pick("#071116", SystemColors.HighlightText); } }
        internal static Color Track { get { return Pick("#95B7C7", SystemColors.WindowText); } }
        internal static Color Line { get { return Pick("#638498", SystemColors.WindowText); } }
        internal static Color Selected { get { return Pick("#35677D", SystemColors.Highlight); } }
        internal static Color Disabled { get { return Pick("#9CB2C2", SystemColors.GrayText); } }
        internal static Color ProviderSurface(string provider)
        {
            if (provider == "codex") return Pick("#174B5B", SystemColors.Window);
            if (provider == "zhipu") return Pick("#4B2A50", SystemColors.Window);
            if (provider == "deepseek") return Pick("#354B2B", SystemColors.Window);
            return Background;
        }
        internal static Color ProviderHeader(string provider)
        { return SystemInformation.HighContrast ? SystemColors.Highlight : Provider(provider); }
        internal static Color Provider(string provider)
        {
            if (provider == "zhipu") return Pick("#FF5EDB", SystemColors.WindowText);
            if (provider == "deepseek") return Pick("#BEF54A", SystemColors.WindowText);
            return Pick("#42E8E0", SystemColors.WindowText);
        }
        internal static Color QuotaColor(double remaining, string provider)
        {
            return remaining <= 10 ? Error : remaining <= 25 ? Warning : Provider(provider);
        }
    }

    // Native Button semantics, keyboard behavior and accessibility are retained.
    internal sealed class PixelButton : Button
    {
        private readonly bool _primary;
        private bool _hover, _pressed;
        private bool _destructive;
        internal bool Destructive { get { return _destructive; } set { _destructive = value; RefreshColors(); } }
        internal PixelButton(bool primary)
        {
            _primary = primary;
            FlatStyle = FlatStyle.Flat;
            Cursor = Cursors.Hand;
            UseCompatibleTextRendering = true;
            TabStop = true;
            Padding = new Padding(4, 0, 4, 0);
            RefreshColors();
        }
        private void RefreshColors()
        {
            BackColor = Enabled && _primary ? PixelTheme.Accent : PixelTheme.Surface;
            ForeColor = !Enabled ? PixelTheme.Disabled : _primary ? PixelTheme.OnAccent
                : Destructive ? PixelTheme.Error : PixelTheme.Text;
            FlatAppearance.BorderColor = !Enabled ? PixelTheme.Line : _primary ? PixelTheme.Accent
                : _pressed ? PixelTheme.Text : _hover ? (Destructive ? PixelTheme.Error : PixelTheme.Focus) : PixelTheme.Line;
            FlatAppearance.MouseOverBackColor = _primary ? PixelTheme.Provider("deepseek") : Destructive ? PixelTheme.Surface : PixelTheme.Selected;
            FlatAppearance.MouseDownBackColor = _primary ? PixelTheme.Secondary : Destructive ? PixelTheme.Surface : PixelTheme.Line;
        }
        protected override void OnEnabledChanged(EventArgs e) { base.OnEnabledChanged(e); RefreshColors(); }
        protected override void OnGotFocus(EventArgs e) { base.OnGotFocus(e); Invalidate(); }
        protected override void OnLostFocus(EventArgs e) { base.OnLostFocus(e); Invalidate(); }
        protected override void OnSystemColorsChanged(EventArgs e) { base.OnSystemColorsChanged(e); RefreshColors(); }
        protected override void OnMouseEnter(EventArgs e) { base.OnMouseEnter(e); _hover = true; RefreshColors(); }
        protected override void OnMouseLeave(EventArgs e) { base.OnMouseLeave(e); _hover = _pressed = false; RefreshColors(); }
        protected override void OnMouseDown(MouseEventArgs e) { base.OnMouseDown(e); _pressed = true; RefreshColors(); }
        protected override void OnMouseUp(MouseEventArgs e) { base.OnMouseUp(e); _pressed = false; RefreshColors(); }
        protected override void OnPaint(PaintEventArgs e)
        {
            if (!Enabled)
            {
                // The native disabled caption ignores ForeColor on a dark surface.
                e.Graphics.Clear(PixelTheme.Surface);
                ControlPaint.DrawBorder(e.Graphics, ClientRectangle, PixelTheme.Line, ButtonBorderStyle.Solid);
                TextRenderer.DrawText(e.Graphics, Text, Font, ClientRectangle, PixelTheme.Disabled,
                    TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.SingleLine);
                return;
            }
            base.OnPaint(e);
            if (Focused && ShowFocusCues)
            {
                int inset = Math.Max(3, (int)Math.Round(3 * e.Graphics.DpiX / 96));
                using (Pen pen = new Pen(_primary ? PixelTheme.OnAccent : PixelTheme.Focus,
                    Math.Max(2, (int)Math.Round(2 * e.Graphics.DpiX / 96))))
                    e.Graphics.DrawRectangle(pen, inset, inset, Math.Max(1, Width - inset * 2 - 1), Math.Max(1, Height - inset * 2 - 1));
            }
        }
    }

    internal sealed class PixelCheckBox : CheckBox
    {
        protected override void OnPaint(PaintEventArgs e)
        {
            if (Enabled) { base.OnPaint(e); return; }
            // Retain native checked/disabled semantics, but keep the dark disabled label readable.
            e.Graphics.Clear(BackColor);
            int size = Math.Min(Height - 4, SystemInformation.MenuCheckSize.Width);
            int top = (Height - size) / 2;
            using (Pen pen = new Pen(PixelTheme.Disabled))
                e.Graphics.DrawRectangle(pen, 0, top, size - 1, size - 1);
            if (Checked)
            {
                int unit = Math.Max(1, size / 8);
                using (SolidBrush brush = new SolidBrush(PixelTheme.Disabled))
                {
                    e.Graphics.FillRectangle(brush, unit, top + 3 * unit, 2 * unit, 3 * unit);
                    e.Graphics.FillRectangle(brush, 3 * unit, top + 4 * unit, 2 * unit, 2 * unit);
                    e.Graphics.FillRectangle(brush, 5 * unit, top + unit, 2 * unit, 4 * unit);
                }
            }
            TextRenderer.DrawText(e.Graphics, Text, Font, new Rectangle(size + 4, 0, Width - size - 4, Height),
                PixelTheme.Disabled, TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.WordBreak);
        }
    }

    // Keep native disabled input/spinner behavior; paint only its read-only value legibly.
    internal sealed class PixelNumber : NumericUpDown
    {
        private readonly ReadOnlyCaption _caption;
        internal PixelNumber()
        {
            _caption = new ReadOnlyCaption(this) { TabStop = false, AccessibleRole = AccessibleRole.None, Visible = false };
            Controls.Add(_caption);
        }
        protected override void OnLayout(LayoutEventArgs e) { base.OnLayout(e); LayoutCaption(); }
        protected override void OnEnabledChanged(EventArgs e) { base.OnEnabledChanged(e); LayoutCaption(); }
        protected override void OnValueChanged(EventArgs e) { base.OnValueChanged(e); if (_caption != null) _caption.Invalidate(); }
        private void LayoutCaption()
        {
            if (_caption == null) return;
            foreach (Control child in Controls)
                if (child is TextBoxBase) { _caption.Bounds = child.Bounds; break; }
            _caption.Visible = !Enabled;
            if (!Enabled) { _caption.BringToFront(); _caption.Invalidate(); }
        }
        private sealed class ReadOnlyCaption : Control
        {
            private readonly PixelNumber _owner;
            internal ReadOnlyCaption(PixelNumber owner)
            {
                _owner = owner;
                SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer, true);
            }
            protected override void OnPaint(PaintEventArgs e)
            {
                e.Graphics.Clear(_owner.BackColor);
                TextRenderer.DrawText(e.Graphics, _owner.Text, _owner.Font, ClientRectangle, PixelTheme.Secondary,
                    TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.SingleLine | TextFormatFlags.NoPadding);
            }
        }
    }

    // Overlay only the native scrollbar's visual area. The native scrolling engine,
    // focus-into-view behavior and scrollbar accessibility remain on the Panel.
    internal sealed class PixelScrollRail : Control
    {
        private readonly ScrollableControl _target;
        private int _grab;
        private bool _refreshQueued;
        internal PixelScrollRail(ScrollableControl target)
        {
            _target = target;
            TabStop = false;
            BackColor = PixelTheme.Background;
            SetStyle(ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.AllPaintingInWmPaint, true);
            target.Scroll += delegate { QueueRefresh(); };
            target.Invalidated += delegate { QueueRefresh(); };
            target.MouseWheel += delegate { QueueRefresh(); };
        }
        private void QueueRefresh()
        {
            if (!IsHandleCreated || IsDisposed || _refreshQueued) return;
            _refreshQueued = true;
            // Repaint after native scrolling has settled, including wheel events sent to child controls.
            BeginInvoke((Action)delegate
            {
                _refreshQueued = false;
                if (!IsDisposed) Refresh();
            });
        }
        private int Maximum { get { return Math.Max(0, _target.VerticalScroll.Maximum - _target.VerticalScroll.LargeChange + 1); } }
        private Rectangle Thumb
        {
            get
            {
                int inset = Math.Max(4, Width / 4), track = Math.Max(1, Height - inset * 2);
                int length = Math.Min(track, Math.Max(24, track * _target.ClientSize.Height / Math.Max(1, _target.AutoScrollMinSize.Height)));
                int position = Math.Max(0, Math.Min(Maximum, -_target.AutoScrollPosition.Y));
                int top = inset + (Maximum == 0 ? 0 : (track - length) * position / Maximum);
                return new Rectangle(Width / 2 - 2, top, 4, length);
            }
        }
        protected override void OnPaint(PaintEventArgs e)
        {
            e.Graphics.Clear(PixelTheme.Background);
            if (Maximum > 0)
                using (SolidBrush brush = new SolidBrush(Capture ? PixelTheme.Accent : PixelTheme.Track))
                    e.Graphics.FillRectangle(brush, Thumb);
        }
        private void ScrollTo(int y)
        {
            int inset = Math.Max(4, Width / 4), travel = Height - inset * 2 - Thumb.Height;
            int next = travel <= 0 ? 0 : (int)Math.Round((y - inset - _grab) * Maximum / (double)travel);
            _target.AutoScrollPosition = new Point(0, Math.Max(0, Math.Min(Maximum, next)));
            Invalidate();
        }
        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.Button != MouseButtons.Left) return;
            Rectangle thumb = Thumb;
            _grab = e.Y >= thumb.Top && e.Y <= thumb.Bottom ? e.Y - thumb.Top : thumb.Height / 2;
            Capture = true; ScrollTo(e.Y);
        }
        protected override void OnMouseMove(MouseEventArgs e) { base.OnMouseMove(e); if (Capture) ScrollTo(e.Y); }
        protected override void OnMouseUp(MouseEventArgs e) { base.OnMouseUp(e); Capture = false; Invalidate(); }
        protected override void OnMouseWheel(MouseEventArgs e)
        {
            _target.AutoScrollPosition = new Point(0, Math.Max(0, Math.Min(Maximum, -_target.AutoScrollPosition.Y - Math.Sign(e.Delta) * 48)));
            Invalidate();
        }
    }
}
