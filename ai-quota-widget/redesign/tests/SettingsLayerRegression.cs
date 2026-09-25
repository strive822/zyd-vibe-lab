using System;
using System.Drawing;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace QuotaWidget
{
    internal static class SettingsLayerRegression
    {
        [DllImport("user32.dll")] private static extern IntPtr GetWindow(IntPtr window, uint command);
        [DllImport("user32.dll")] private static extern int GetWindowLong(IntPtr window, int index);
        [DllImport("user32.dll")] private static extern bool IsWindowEnabled(IntPtr window);

        private static bool Above(Form dialog, Form owner)
        {
            for (IntPtr window = GetWindow(owner.Handle, 3); window != IntPtr.Zero; window = GetWindow(window, 3))
                if (window == dialog.Handle) return true;
            return false;
        }

        internal static void Run(Action<string, bool, string> check)
        {
            foreach (bool pinned in new[] { true, false })
            foreach (bool save in new[] { false, true })
                CheckModal(check, pinned, save);
            CheckTopBoundary(check);
            CheckShortWorkArea(check);
        }

        private static void CheckTopBoundary(Action<string, bool, string> check)
        {
            foreach (float scale in new[] { 1f, 1.5f, 2f })
            {
                string tag = "settings-layer: top edge scale=" + scale + " ";
                AppConfig config = Program.LoadConfiguration(true, "normal", null);
                Rectangle work = Screen.PrimaryScreen.WorkingArea;
                using (WidgetForm widget = new WidgetForm(config, true, "normal", scale, false))
                using (Timer timer = new Timer { Interval = 20 })
                {
                    widget.Location = new Point(work.Right - widget.Width - 60, work.Top + 4);
                    Point original = widget.Location;
                    widget.Show(); Application.DoEvents();
                    bool observed = false;
                    int ticks = 0;
                    timer.Tick += delegate
                    {
                        SettingsForm modal = null;
                        foreach (Form open in Application.OpenForms)
                            if (open is SettingsForm && GetWindow(open.Handle, 4) == widget.Handle)
                                modal = (SettingsForm)open;
                        if (modal == null || !modal.Visible || !modal.Modal)
                        {
                            if (++ticks > 100 && modal != null)
                            { timer.Stop(); modal.DialogResult = DialogResult.Cancel; modal.Close(); }
                            return;
                        }
                        timer.Stop(); observed = true;
                        try
                        {
                            Button save = (Button)UiRegression.Field(modal, "_saveButton");
                            Button cancel = (Button)UiRegression.Field(modal, "_cancelButton");
                            check(tag + "keeps both windows separate and in work area",
                                modal.Bottom + 8 <= widget.Top && !modal.Bounds.IntersectsWith(widget.Bounds)
                                && work.Contains(modal.Bounds) && work.Contains(widget.Bounds), null);
                            check(tag + "keeps settings actions reachable",
                                save.Visible && cancel.Visible && save.Enabled && cancel.Enabled
                                && work.Contains(save.RectangleToScreen(save.ClientRectangle))
                                && work.Contains(cancel.RectangleToScreen(cancel.ClientRectangle)), null);
                            typeof(WidgetForm).GetField("_uiMessage", BindingFlags.NonPublic | BindingFlags.Instance)
                                .SetValue(widget, "设置窗口打开时仍可能收到较长的状态提示，需要保持两窗不交叠。");
                            UiRegression.Invoke(widget, "OnTick", null, EventArgs.Empty);
                            check(tag + "stays separate after widget content changes",
                                modal.Bottom + 8 <= widget.Top && !modal.Bounds.IntersectsWith(widget.Bounds)
                                && work.Contains(modal.Bounds) && work.Contains(widget.Bounds), null);
                        }
                        finally { modal.DialogResult = DialogResult.Cancel; modal.Close(); }
                    };
                    UiRegression.Invoke(widget, "BuildMenu");
                    timer.Start();
                    ((ContextMenuStrip)UiRegression.Field(widget, "_menu")).Items[1].PerformClick();
                    check(tag + "opens via menu and restores widget position",
                        observed && widget.Location == original, null);
                    widget.Hide();
                }
            }
        }

        private static void CheckShortWorkArea(Action<string, bool, string> check)
        {
            Rectangle screen = Screen.PrimaryScreen.WorkingArea;
            Rectangle work = new Rectangle(screen.Left + 20, screen.Top + 20,
                Math.Min(900, screen.Width - 40), Math.Min(640, screen.Height - 40));
            AppConfig config = Program.LoadConfiguration(true, "many", null);
            using (WidgetForm widget = new WidgetForm(config, true, "many", 2, false))
            using (SettingsForm settings = new SettingsForm(config, false, false, 2, AppConfig.Save))
            {
                int originalHeight = widget.Height;
                widget.Location = new Point(work.Right - widget.Width - 8, work.Top + 4);
                widget.Show();
                settings.Show(widget);
                Application.DoEvents();
                widget.PlaceSettingsAbove(settings, work);
                Button save = (Button)UiRegression.Field(settings, "_saveButton");
                Button cancel = (Button)UiRegression.Field(settings, "_cancelButton");
                check("settings-layer: short work area shrinks scrollable widget before dialog footer",
                    work.Contains(widget.Bounds) && work.Contains(settings.Bounds)
                    && settings.Bottom + 16 <= widget.Top
                    && settings.Height >= 320 && !settings.Bounds.IntersectsWith(widget.Bounds),
                    "work=" + work + " widget=" + widget.Bounds + " settings=" + settings.Bounds);
                check("settings-layer: short work area keeps actual button rectangles on screen",
                    work.Contains(save.RectangleToScreen(save.ClientRectangle))
                    && work.Contains(cancel.RectangleToScreen(cancel.ClientRectangle)), null);
                settings.Close();
                UiRegression.Invoke(widget, "ResizeForContent", false);
                check("settings-layer: closing short-area dialog restores scrollable widget height",
                    widget.Height == originalHeight, null);
                widget.Hide();
            }
        }

        private static void CheckModal(Action<string, bool, string> check, bool pinned, bool save)
        {
            string tag = "settings-layer: pinned=" + pinned + " save=" + save + " ";
            AppConfig config = Program.LoadConfiguration(true, "normal", null);
            config.Ui.TopMost = pinned;
            string name = config.Codex.Name;
            using (WidgetForm widget = new WidgetForm(config, true, "normal", 1, false))
            using (Timer timer = new Timer { Interval = 20 })
            {
                // Both windows are real HWNDs; placement does not set their z-order.
                widget.Location = new Point(Screen.PrimaryScreen.WorkingArea.Right - widget.Width - 60,
                    Screen.PrimaryScreen.WorkingArea.Bottom - widget.Height - 80);
                widget.Show(); Application.DoEvents();
                int ticks = 0; bool observed = false;
                timer.Tick += delegate
                {
                    Form modal = null;
                    foreach (Form open in Application.OpenForms)
                        if (open is SettingsForm && GetWindow(open.Handle, 4) == widget.Handle) modal = open;
                    if (modal == null || !modal.Visible || !modal.Modal || IsWindowEnabled(widget.Handle))
                    {
                        if (++ticks > 100 && modal != null)
                        { timer.Stop(); modal.DialogResult = DialogResult.Cancel; modal.Close(); }
                        return;
                    }
                    timer.Stop(); observed = true;
                    try
                    {
                        Panel footer = (Panel)UiRegression.Field(modal, "_footer");
                        Button saveButton = (Button)UiRegression.Field(modal, "_saveButton");
                        Button cancelButton = (Button)UiRegression.Field(modal, "_cancelButton");
                        check(tag + "compact settings keep fixed actions visible",
                            modal.ClientSize.Width <= 320 && modal.ClientSize.Height <= 340
                            && footer.Visible && saveButton.Visible && cancelButton.Visible
                            && saveButton.Bounds.Right <= footer.ClientSize.Width
                            && cancelButton.Bounds.Left >= 0, null);
                        check(tag + "settings is above owner without covering widget",
                            modal.Bottom + 8 <= widget.Top && !modal.Bounds.IntersectsWith(widget.Bounds)
                            && modal.Right == widget.Right && Above(modal, widget) && !IsWindowEnabled(widget.Handle), null);
                        check(tag + "inherits native topmost band without changing preference",
                            ((GetWindowLong(modal.Handle, -20) & 8) != 0) == pinned && config.Ui.TopMost == pinned, null);
                        typeof(WidgetForm).GetField("_ticks", BindingFlags.NonPublic | BindingFlags.Instance).SetValue(widget, 29);
                        UiRegression.Invoke(widget, "OnTick", null, EventArgs.Empty);
                        widget.RefreshNow();
                        check(tag + "maintenance and refresh do not cover dialog", Above(modal, widget), null);
                        widget.ShowFromTray();
                        check(tag + "restore signal keeps dialog above owner", Above(modal, widget), null);
                        ((TextBox)UiRegression.Field(modal, "_codexName")).Text = "Modal draft";
                        ((CheckBox)UiRegression.Field(modal, "_topMost")).Checked = !pinned;
                        if (save) ((Button)UiRegression.Field(modal, "_saveButton")).PerformClick();
                        else ((Button)UiRegression.Field(modal, "_cancelButton")).PerformClick();
                    }
                    finally { if (modal.DialogResult == DialogResult.None) { modal.DialogResult = DialogResult.Cancel; modal.Close(); } }
                };
                UiRegression.Invoke(widget, "BuildMenu");
                timer.Start();
                // The same menu item used by the main window and tray, not ShowDialog in isolation.
                ((ContextMenuStrip)UiRegression.Field(widget, "_menu")).Items[1].PerformClick();
                check(tag + "menu opens settings", observed, null);
                AppConfig result = (AppConfig)UiRegression.Field(widget, "_cfg");
                bool expectedPinned = save ? !pinned : pinned;
                check(tag + "close preserves or applies chosen topmost state", widget.TopMost == expectedPinned
                    && ((GetWindowLong(widget.Handle, -20) & 8) != 0) == expectedPinned
                    && result.Ui.TopMost == expectedPinned && widget.Visible && widget.Enabled, null);
                check(tag + "save and cancel retain correct draft",
                    result.Codex.Name == (save ? "Modal draft" : name), null);
                widget.Hide();
            }
        }
    }
}
