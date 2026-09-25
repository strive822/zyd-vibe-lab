using System;
using System.Collections.Generic;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace QuotaWidget
{
    public sealed class SettingsForm : Form
    {
        private readonly AppConfig _source;
        private readonly bool _persist;
        private readonly Func<AppConfig, bool> _save;
        private readonly Panel _scroll;
        private readonly Panel _footer;
        private readonly PixelScrollRail _rail;
        private readonly TextBox _saveError;
        private readonly PixelButton _cancelButton, _saveButton;
        private readonly Font _bodyFont, _sectionFont;
        private readonly float _scale;
        private bool _building;
        private int _lastWidth, _tab;
        private List<ZhipuCfg> _zhipuDraft = new List<ZhipuCfg>();
        private List<ZhipuEditor> _zhipuEditors = new List<ZhipuEditor>();
        private string _codexNameDraft, _codexPathDraft, _deepseekNameDraft, _deepseekKeyDraft;
        private bool _codexEnabledDraft, _deepseekEnabledDraft, _topMostDraft;
        private decimal _intervalDraft;
        private TextBox _codexName, _codexPath, _deepseekName, _deepseekKey;
        private CheckBox _codexEnabled, _deepseekEnabled;
        private NumericUpDown _interval;
        private CheckBox _topMost;
        private readonly List<SectionBand> _sectionBands = new List<SectionBand>();
        private string _sectionProvider;
        private sealed class SectionBand { internal int Top, Bottom; internal string Provider; }
        public AppConfig UpdatedConfig { get; private set; }

        [DllImport("dwmapi.dll")]
        private static extern int DwmSetWindowAttribute(IntPtr hwnd, int attr, ref int value, int size);
        private int S(int value) { return (int)Math.Round(value * _scale); }
        private int ContentWidth { get { return Math.Max(S(120), ClientSize.Width - S(40) - SystemInformation.VerticalScrollBarWidth); } }

        private sealed class ZhipuEditor
        {
            public TextBox Name, Key;
            public CheckBox Visible;
            public ZhipuCfg Draft;
        }

        public SettingsForm(AppConfig source, bool focusOpacity, bool persist)
            : this(source, focusOpacity, persist, 0, AppConfig.Save) { }

        internal SettingsForm(AppConfig source, bool focusOpacity, bool persist, float previewScale, Func<AppConfig, bool> save)
        {
            _source = source;
            _persist = persist;
            _save = save;
            float dpi = 1;
            using (Graphics g = CreateGraphics()) dpi = Math.Max(1, g.DpiX / 96);
            _scale = previewScale > 0 ? previewScale : dpi;
            _bodyFont = new Font("Microsoft YaHei UI", 14 * _scale, FontStyle.Regular, GraphicsUnit.Pixel);
            _sectionFont = new Font("Microsoft YaHei UI", 16 * _scale, FontStyle.Bold, GraphicsUnit.Pixel);
            _codexNameDraft = source.Codex.Name;
            _codexPathDraft = source.Codex.AuthJsonPath;
            _deepseekNameDraft = source.DeepSeek.Name;
            _deepseekKeyDraft = source.DeepSeek.ApiKey;
            _codexEnabledDraft = source.Codex.Enabled;
            _deepseekEnabledDraft = source.DeepSeek.Enabled;
            _topMostDraft = source.Ui.TopMost;
            _intervalDraft = Math.Max(10, Math.Min(3600, source.RefreshIntervalSeconds));
            foreach (ZhipuCfg z in source.Zhipu) _zhipuDraft.Add(z.Clone());
            Text = persist ? "额度设置" : "额度设置 · 模拟预览";
            if (source.LoadError) Text += "（只读）";
            AccessibleName = Text;
            StartPosition = FormStartPosition.CenterParent;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            MinimizeBox = false;
            ShowInTaskbar = false;
            AutoScaleMode = AutoScaleMode.None; // Single explicit DPI transform, including dynamically added accounts.
            Rectangle work = Screen.FromPoint(Cursor.Position).WorkingArea;
            ClientSize = new Size(Math.Min(S(320), work.Width - S(24)), Math.Min(S(340), work.Height - S(64)));
            BackColor = PixelTheme.Background;
            ForeColor = PixelTheme.Text;
            Font = _bodyFont;

            _footer = new Panel { Dock = DockStyle.Bottom, Height = S(64), BackColor = PixelTheme.Footer, TabIndex = 1 };
            _footer.Paint += delegate(object sender, PaintEventArgs e)
            { using (Pen p = new Pen(PixelTheme.Line)) e.Graphics.DrawLine(p, S(20), 0, _footer.Width - S(20), 0); };
            _cancelButton = MakeButton(source.LoadError ? "关闭" : "取消", false);
            _cancelButton.TabIndex = 1;
            _cancelButton.Anchor = AnchorStyles.Right | AnchorStyles.Bottom;
            _cancelButton.Click += delegate { DialogResult = DialogResult.Cancel; Close(); };
            _saveButton = MakeButton("保存设置", true);
            _saveButton.TabIndex = 2;
            _saveButton.Anchor = AnchorStyles.Right | AnchorStyles.Bottom;
            _saveButton.Enabled = !source.LoadError;
            _saveButton.Click += SaveClicked;
            _saveError = new TextBox { Multiline = true, ReadOnly = true, BorderStyle = BorderStyle.None,
                BackColor = PixelTheme.Footer, ForeColor = PixelTheme.Error, Visible = false,
                AccessibleName = "设置保存错误", TabIndex = 0, Font = _bodyFont };
            _footer.Controls.Add(_saveError);
            _footer.Controls.Add(_cancelButton);
            _footer.Controls.Add(_saveButton);
            Controls.Add(_footer);
            AcceptButton = _saveButton;
            CancelButton = _cancelButton;
            _scroll = new Panel { Dock = DockStyle.Fill, AutoScroll = true, BackColor = PixelTheme.Background, TabIndex = 0 };
            _scroll.Paint += delegate(object sender, PaintEventArgs e)
            {
                foreach (SectionBand band in _sectionBands)
                    using (SolidBrush brush = new SolidBrush(PixelTheme.ProviderSurface(band.Provider)))
                        e.Graphics.FillRectangle(brush, 0, band.Top + _scroll.AutoScrollPosition.Y, _scroll.ClientSize.Width, Math.Max(0, band.Bottom - band.Top));
            };
            _scroll.Scroll += delegate { _scroll.Invalidate(); };
            Controls.Add(_scroll);
            _scroll.BringToFront();
            _rail = new PixelScrollRail(_scroll);
            Controls.Add(_rail);
            _scroll.Layout += delegate { LayoutRail(); };
            LayoutFooter();
            BuildBody();
            ClientSizeChanged += delegate
            {
                LayoutFooter();
                if (!_building && _codexName != null && _lastWidth != ClientSize.Width)
                { ReadOtherDraft(); ReadZhipuDraft(); BuildBody(); }
            };
            if (source.LoadError) Shown += delegate { _cancelButton.Focus(); };
        }

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            try { int dark = 1; DwmSetWindowAttribute(Handle, 20, ref dark, 4); } catch { }
        }

        protected override bool ProcessCmdKey(ref Message msg, Keys keyData)
        {
            if (_source != null && _source.LoadError && _scroll != null)
            {
                int position = -_scroll.AutoScrollPosition.Y;
                if (keyData == Keys.PageDown) position += _scroll.ClientSize.Height;
                else if (keyData == Keys.PageUp) position -= _scroll.ClientSize.Height;
                else if (keyData == Keys.End) position = _scroll.VerticalScroll.Maximum;
                else if (keyData == Keys.Home) position = 0;
                else return base.ProcessCmdKey(ref msg, keyData);
                _scroll.AutoScrollPosition = new Point(0, Math.Max(0, position));
                _rail.Refresh();
                return true;
            }
            return base.ProcessCmdKey(ref msg, keyData);
        }

        private int LabelHeight(string text, Font font, int width)
        {
            return TextRenderer.MeasureText(text, font, new Size(Math.Max(1, width), int.MaxValue),
                TextFormatFlags.WordBreak | TextFormatFlags.NoPrefix).Height + S(4);
        }

        private PixelButton MakeButton(string text, bool primary)
        {
            return new PixelButton(primary) { Text = text, Font = _bodyFont,
                Size = new Size(S(primary ? 112 : 80), S(36)), AccessibleName = text };
        }

        private void LayoutFooter()
        {
            if (_footer == null || _saveError == null) return;
            int errorH = _saveError.Text.Length > 0 ? LabelHeight(_saveError.Text, _bodyFont, ClientSize.Width - S(40)) + S(8) : 0;
            _footer.Height = S(64) + errorH;
            _saveError.SetBounds(S(20), S(8), Math.Max(1, _footer.Width - S(40)), Math.Max(1, errorH));
            _saveButton.SetBounds(_footer.Width - S(20) - _saveButton.Width, _footer.Height - S(50), _saveButton.Width, S(36));
            _cancelButton.SetBounds(_saveButton.Left - S(8) - _cancelButton.Width, _saveButton.Top, _cancelButton.Width, S(36));
            LayoutRail();
        }

        private void LayoutRail()
        {
            if (_rail == null || _scroll == null) return;
            int width = Math.Max(SystemInformation.VerticalScrollBarWidth, S(16));
            _rail.SetBounds(_scroll.Right - width, _scroll.Top, width, _scroll.Height);
            _rail.Visible = _scroll.VerticalScroll.Visible;
            _rail.BringToFront();
            _rail.Invalidate();
        }

        private T Add<T>(T control) where T : Control
        {
            if (control is Label || control is CheckBox) control.BackColor = PixelTheme.ProviderSurface(_sectionProvider);
            control.TabIndex = _tab++;
            _scroll.Controls.Add(control);
            return control;
        }

        private Label Label(string text, int x, int y, int width, bool heading)
        {
            Label label = new Label { Text = text, Font = heading ? _sectionFont : _bodyFont,
                Location = new Point(x, y), Size = new Size(width, LabelHeight(text, heading ? _sectionFont : _bodyFont, width)),
                ForeColor = PixelTheme.Secondary, BackColor = PixelTheme.Background, AutoEllipsis = false,
                UseCompatibleTextRendering = false, TabStop = false, AccessibleName = text };
            return Add(label);
        }

        private void Heading(string title, string provider, ref int y)
        {
            if (_sectionBands.Count > 0) _sectionBands[_sectionBands.Count - 1].Bottom = y;
            _sectionProvider = provider;
            _sectionBands.Add(new SectionBand { Top = y, Provider = provider });
            y += S(16);
            Label label = Label(title, S(20), y, ContentWidth, true);
            label.BackColor = provider == null ? PixelTheme.Footer : PixelTheme.ProviderHeader(provider);
            label.ForeColor = provider == null ? PixelTheme.Text : PixelTheme.OnAccent;
            label.Padding = new Padding(S(8), 0, 0, 0);
            label.TextAlign = ContentAlignment.MiddleLeft;
            label.Height += S(6);
            y += label.Height + S(12);
        }

        private TextBox Field(string label, string value, ref int y, bool secret)
        {
            Label caption = Label(label, S(20), y, ContentWidth, false);
            y += caption.Height + S(4);
            PixelField field = new PixelField(_bodyFont, _scale) { Location = new Point(S(20), y), Width = ContentWidth };
            field.Editor.Text = value ?? "";
            field.Editor.UseSystemPasswordChar = secret;
            field.Editor.MaxLength = secret || label.StartsWith("auth.json") ? 2048 : 120;
            field.Editor.AccessibleName = label;
            Add(field);
            y += field.Height + S(16);
            return field.Editor;
        }

        private CheckBox Check(string text, bool value, ref int y)
        {
            CheckBox checkbox = new PixelCheckBox { Text = text, Checked = value, Location = new Point(S(20), y),
                Size = new Size(ContentWidth, Math.Max(S(28), LabelHeight(text, _bodyFont, ContentWidth - S(24)))),
                Font = _bodyFont, ForeColor = PixelTheme.Text, BackColor = PixelTheme.Background, FlatStyle = FlatStyle.Flat,
                AccessibleName = text, UseVisualStyleBackColor = false };
            checkbox.FlatAppearance.CheckedBackColor = PixelTheme.Surface;
            checkbox.FlatAppearance.BorderColor = PixelTheme.Secondary;
            Add(checkbox); y += checkbox.Height + S(12);
            return checkbox;
        }

        private NumericUpDown Number(string label, decimal min, decimal max, decimal value, ref int y)
        {
            bool compact = ContentWidth < S(340);
            Label caption = Label(label, S(20), y, compact ? ContentWidth : ContentWidth - S(120), false);
            NumericUpDown input = new PixelNumber { Minimum = min, Maximum = max, Value = value,
                Font = _bodyFont, Width = S(100), BackColor = PixelTheme.Surface, ForeColor = PixelTheme.Text,
                BorderStyle = BorderStyle.FixedSingle, AccessibleName = label };
            input.Location = new Point(compact ? S(20) : S(20) + ContentWidth - input.Width, compact ? y + caption.Height + S(4) : y);
            Add(input);
            y = Math.Max(caption.Bottom, input.Bottom) + S(16);
            return input;
        }

        private void ReadZhipuDraft()
        {
            if (_zhipuEditors.Count == 0) return;
            _zhipuDraft = new List<ZhipuCfg>();
            foreach (ZhipuEditor e in _zhipuEditors)
            {
                ZhipuCfg draft = e.Draft.Clone();
                draft.Name = e.Name.Text.Trim();
                draft.ApiKey = e.Key.Text.Trim();
                draft.Visible = e.Visible.Checked;
                _zhipuDraft.Add(draft);
            }
        }

        private void ReadOtherDraft()
        {
            _codexNameDraft = _codexName.Text;
            _codexPathDraft = _codexPath.Text;
            _deepseekNameDraft = _deepseekName.Text;
            _deepseekKeyDraft = _deepseekKey.Text;
            _codexEnabledDraft = _codexEnabled.Checked;
            _deepseekEnabledDraft = _deepseekEnabled.Checked;
            _topMostDraft = _topMost.Checked;
            _intervalDraft = _interval.Value;
        }

        private void BuildBody()
        {
            _building = true;
            _lastWidth = ClientSize.Width;
            int scrollY = -_scroll.AutoScrollPosition.Y;
            _scroll.SuspendLayout();
            _scroll.AutoScrollPosition = Point.Empty;
            while (_scroll.Controls.Count > 0) _scroll.Controls[0].Dispose();
            _zhipuEditors.Clear();
            _sectionBands.Clear();
            _sectionProvider = null;
            _tab = 0;
            int y = S(16);
            string text = _source.LoadError ? "配置损坏 · 仅供查看\n编辑与保存已锁定。请修复 config.json 并重新启动。"
                : !_persist ? "模拟预览：设置仅在本次预览生效，不读取或保存真实账号配置。"
                : "账号仅在本机请求对应平台。API Key 保存在本机 config.json。";
            Label note = Label(text, S(20), y, ContentWidth, false);
            if (_source.LoadError) note.ForeColor = PixelTheme.Error;
            y += note.Height + S(4);
            Heading("OpenAI Codex", "codex", ref y);
            _codexEnabled = Check("启用", _codexEnabledDraft, ref y);
            _codexName = Field("显示名称", _codexNameDraft, ref y, false);
            _codexPath = Field("auth.json 路径（留空使用默认路径）", _codexPathDraft, ref y, false);

            Heading("智谱 GLM Coding Plan", "zhipu", ref y);
            for (int i = 0; i < _zhipuDraft.Count; i++)
            {
                int index = i;
                ZhipuCfg z = _zhipuDraft[i];
                Label account = Label("账号 " + (i + 1), S(20), y + S(4), ContentWidth - S(90), false);
                PixelButton remove = MakeButton("移除", false);
                remove.Destructive = true;
                remove.AccessibleName = "移除智谱账号 " + (i + 1);
                remove.SetBounds(S(20) + ContentWidth - S(80), y, S(80), S(32));
                remove.Click += delegate
                {
                    ReadOtherDraft(); ReadZhipuDraft(); _zhipuDraft.RemoveAt(index); BuildBody();
                    if (_zhipuEditors.Count > 0) _zhipuEditors[Math.Min(index, _zhipuEditors.Count - 1)].Name.Focus();
                    else { foreach (Control c in _scroll.Controls) if (c.Name == "add-account") { c.Focus(); break; } }
                };
                Add(remove); y += Math.Max(account.Height, remove.Height) + S(8);
                ZhipuEditor editor = new ZhipuEditor { Draft = z };
                editor.Visible = Check("显示在悬浮窗", z.Visible, ref y);
                editor.Name = Field("显示名称", z.Name, ref y, false);
                editor.Name.AccessibleName = "智谱账号 " + (i + 1) + " 显示名称";
                editor.Key = Field("Coding Plan API Key", z.ApiKey, ref y, true);
                _zhipuEditors.Add(editor);
            }
            PixelButton add = MakeButton("添加智谱账号", false);
            add.Name = "add-account";
            add.SetBounds(S(20), y, S(156), S(36));
            add.Click += delegate
            {
                ReadOtherDraft(); ReadZhipuDraft(); _zhipuDraft.Add(new ZhipuCfg()); BuildBody();
                _scroll.ScrollControlIntoView(_zhipuEditors[_zhipuEditors.Count - 1].Name.Parent);
                _zhipuEditors[_zhipuEditors.Count - 1].Name.Focus();
            };
            Add(add); y += S(52);
            Heading("DeepSeek", "deepseek", ref y);
            _deepseekEnabled = Check("启用", _deepseekEnabledDraft, ref y);
            _deepseekName = Field("显示名称", _deepseekNameDraft, ref y, false);
            _deepseekKey = Field("API Key", _deepseekKeyDraft, ref y, true);
            Heading("窗口", null, ref y);
            _interval = Number("自动刷新间隔（秒）", 10, 3600, _intervalDraft, ref y);
            _topMost = Check("置顶显示", _topMostDraft, ref y);
            if (_source.LoadError)
                foreach (Control control in _scroll.Controls)
                {
                    PixelField field = control as PixelField;
                    if (field != null)
                    {
                        field.Editor.ReadOnly = true;
                        field.Editor.TabStop = false;
                        field.Editor.BackColor = field.BackColor = PixelTheme.Background;
                        field.Editor.ForeColor = PixelTheme.Disabled;
                        field.Editor.AccessibleDescription = "仅供查看；配置损坏，修复并重启后才能编辑。";
                    }
                    else if (control is CheckBox || control is NumericUpDown || control is Button)
                    {
                        control.Enabled = false;
                        control.TabStop = false;
                        control.AccessibleDescription = "配置损坏，当前操作已锁定。";
                    }
                }
            _scroll.AutoScrollMinSize = new Size(0, y + S(16));
            if (_sectionBands.Count > 0) _sectionBands[_sectionBands.Count - 1].Bottom = y + S(16);
            _scroll.ResumeLayout(true);
            _scroll.AutoScrollPosition = new Point(0, scrollY);
            _scroll.Invalidate();
            _building = false;
            LayoutRail();
        }

        private void ShowSaveError(string message)
        {
            _saveError.Text = message;
            _saveError.Visible = true;
            LayoutFooter();
            _saveError.Focus();
            _saveError.Select(0, 0);
            AccessibilityNotifyClients(AccessibleEvents.ValueChange, -1);
        }

        internal void PreviewState(string state)
        {
            if (_persist) throw new InvalidOperationException("Preview states require non-persistent settings.");
            if (state == "save-error") ShowSaveError("保存失败，草稿仍保留。请检查配置文件及写入权限后重试。");
            if (state == "settings-focus") _codexName.Focus();
            if (state == "settings-bottom" || state == "config-error-bottom")
            {
                _interval.Focus();
                _scroll.AutoScrollPosition = new Point(0, _scroll.VerticalScroll.Maximum);
                _rail.Refresh();
            }
        }

        private void SaveClicked(object sender, EventArgs e)
        {
            if (_source.LoadError)
            {
                ShowSaveError("原配置加载失败，不能覆盖。请修复 config.json 并重新启动后修改设置。");
                return;
            }
            ReadZhipuDraft();
            AppConfig cfg = _source.Clone();
            cfg.ZaiAuthorization = _source.ZaiAuthorization;
            cfg.WarnThreshold = _source.WarnThreshold;
            cfg.Codex = new CodexCfg { Enabled = _codexEnabled.Checked, Visible = _source.Codex.Visible,
                Name = _codexName.Text.Trim(), AuthJsonPath = _codexPath.Text.Trim() };
            cfg.Zhipu = _zhipuDraft;
            cfg.DeepSeek = new DeepSeekCfg { Enabled = _deepseekEnabled.Checked, Visible = _source.DeepSeek.Visible,
                Name = _deepseekName.Text.Trim(), ApiKey = _deepseekKey.Text.Trim() };
            cfg.Ui = new UiCfg { Left = _source.Ui.Left, Top = _source.Ui.Top, TopMost = _topMost.Checked };
            cfg.RefreshIntervalSeconds = (int)_interval.Value;
            _saveButton.Enabled = false;
            try
            {
                if (_persist && !_save(cfg))
                {
                    ShowSaveError("保存失败，草稿仍保留。请检查配置文件及写入权限后重试。");
                    return;
                }
                UpdatedConfig = cfg;
                DialogResult = DialogResult.OK;
                Close();
            }
            finally { if (!_saveButton.IsDisposed) _saveButton.Enabled = !_source.LoadError; }
        }

        protected override void Dispose(bool disposing)
        {
            base.Dispose(disposing);
            if (disposing) { if (_bodyFont != null) _bodyFont.Dispose(); if (_sectionFont != null) _sectionFont.Dispose(); }
        }
    }

    internal sealed class PixelField : Panel
    {
        internal readonly TextBox Editor;
        private readonly int _inset, _stroke;
        private bool _error;
        internal bool HasError { get { return _error; } set { _error = value; Invalidate(); } }
        internal PixelField(Font font, float scale)
        {
            _inset = Math.Max(4, (int)Math.Round(8 * scale));
            _stroke = Math.Max(2, (int)Math.Round(2 * scale));
            Height = Math.Max((int)Math.Round(34 * scale), font.Height + (int)Math.Round(12 * scale));
            BackColor = PixelTheme.Surface;
            TabStop = false;
            Editor = new TextBox { Font = font, BorderStyle = BorderStyle.None, BackColor = PixelTheme.Surface,
                ForeColor = PixelTheme.Text, TabIndex = 0 };
            Controls.Add(Editor);
            Editor.GotFocus += delegate { Invalidate(); };
            Editor.LostFocus += delegate { Invalidate(); };
            Resize += delegate { Editor.SetBounds(_inset, Math.Max(1, (Height - Editor.PreferredHeight) / 2), Math.Max(1, Width - 2 * _inset), Editor.PreferredHeight); };
        }
        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            bool editing = Editor.Focused && !Editor.ReadOnly;
            int stroke = editing ? _stroke : 1;
            using (Pen p = new Pen(HasError ? PixelTheme.Error : editing ? PixelTheme.Focus : PixelTheme.Line, stroke))
                e.Graphics.DrawRectangle(p, stroke / 2, stroke / 2, Math.Max(1, Width - stroke), Math.Max(1, Height - stroke));
        }
    }
}
