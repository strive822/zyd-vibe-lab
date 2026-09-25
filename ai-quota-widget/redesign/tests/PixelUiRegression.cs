using System;
using System.Collections.Generic;
using System.Drawing;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace QuotaWidget
{
    internal static class PixelUiRegression
    {
        [DllImport("user32.dll")]
        private static extern IntPtr SendMessage(IntPtr window, int message, IntPtr wParam, IntPtr lParam);

        internal static void Run(Action<string, bool, string> check)
        {
            check("pixel: missing quota is unknown, not zero", WidgetForm.QuotaValue(null) == "—", null);
            check("pixel: non-finite quota stays unknown", !WidgetForm.Remaining(new QuotaWindow { UsedPercent = double.NaN }).HasValue, null);
            check("pixel: used converts to remaining once", WidgetForm.QuotaValue(new QuotaWindow { UsedPercent = 26 }) == "74%", null);
            foreach (double remaining in new[] { 0.0, 10.0, 25.0, 100.0 })
            {
                int pixels = 0;
                for (int i = 0; i < 20; i++) pixels += WidgetForm.SegmentFillWidth(10, remaining, i);
                check("pixel: exact energy total at " + remaining, pixels == (int)(remaining * 2), null);
            }
            check("pixel: partial segment is not rounded up", WidgetForm.SegmentFillWidth(10, 12, 2) == 4, null);
            check("pixel: subpixel quota never overstates", WidgetForm.SegmentFillWidth(10, .1, 0) == 0, null);
            check("pixel: warning boundary and adjacent values", PixelTheme.QuotaColor(25, "codex") == PixelTheme.Warning
                && PixelTheme.QuotaColor(25.01, "codex") == PixelTheme.Provider("codex")
                && PixelTheme.QuotaColor(24.99, "codex") == PixelTheme.Warning
                && PixelTheme.QuotaColor(10.01, "codex") == PixelTheme.Warning
                && PixelTheme.QuotaColor(10, "codex") == PixelTheme.Error
                && PixelTheme.QuotaColor(9.99, "codex") == PixelTheme.Error, null);

            AccountState stale = new AccountState { Name = "演示账号", Provider = "codex", Stale = true,
                Error = "网络连接失败", Warning = "部分数据异常", Fetching = true, LastSuccess = DateTime.Now.AddMinutes(-2),
                Windows = new List<QuotaWindow> { new QuotaWindow { Kind = WindowKind.FiveHour, UsedPercent = 26 } } };
            check("pixel: refresh does not hide stale and warning", WidgetForm.AccountStatus(stale) == "刷新中"
                && WidgetForm.AccountNotice(stale).Contains("数据过期") && WidgetForm.AccountNotice(stale).Contains("部分数据异常"), null);
            stale.Fetching = false;
            check("pixel: stale label is not duplicated", WidgetForm.AccountStatus(stale) == "数据过期"
                && !WidgetForm.AccountNotice(stale).Contains("数据过期") && WidgetForm.AccountNotice(stale).Contains("网络连接失败"), null);
            string id = Guid.NewGuid().ToString("N");
            check("preview: capture instance is isolated only in mock", Program.PreviewInstanceSuffix(true, new[] { "--preview-instance=" + id }) == "_" + id
                && Program.PreviewInstanceSuffix(false, new[] { "--preview-instance=" + id }) == ""
                && Program.PreviewInstanceSuffix(true, new[] { "--preview-instance=invalid" }) == "", null);

            foreach (float scale in new[] { 1f, 1.5f, 2f })
            using (WidgetForm form = new WidgetForm(Program.LoadConfiguration(true, "normal", null), true, "normal", scale, false))
            {
                int normalWidth = form.Width;
                check("pixel: compact content-measured width at " + scale, form.Width >= (int)(234 * scale) && form.Width <= (int)(360 * scale), null);
                string text = form.AccountAccessibleText(stale);
                check("pixel: accessible data includes value, stale and error at " + scale,
                    text.Contains("74%") && text.Contains("数据过期") && text.Contains("网络连接失败") && text.Contains("最近成功"), null);
                IList<AccountState> accounts = (IList<AccountState>)UiRegression.Field(form, "_accounts");
                accounts[0].Name = new string('长', 70) + new string('A', 90);
                UiRegression.Invoke(form, "ResizeForContent", false);
                int measured = (int)typeof(WidgetForm).GetMethod("AccountHeaderH", BindingFlags.Instance | BindingFlags.NonPublic)
                    .Invoke(form, new object[] { accounts[0], form.Width });
                check("pixel: long mixed name wraps without widening at " + scale, measured > 20 * scale && form.Width == normalWidth, null);
                AccessibleObject first = form.AccessibilityObject.GetChild(0);
                check("pixel: self-drawn account is accessible at " + scale, first.Name == accounts[0].Name && first.Value.Contains("剩余"), null);
                using (Bitmap image = new Bitmap(form.Width, form.Height)) form.DrawToBitmap(image, form.ClientRectangle);
            }
            using (WidgetForm form = new WidgetForm(Program.LoadConfiguration(true, "many", null), true, "many", 1f, false))
            {
                form.HandleNavigationKey(Keys.End);
                check("pixel: keyboard reaches last account", (int)UiRegression.Field(form, "_scroll") ==
                    (int)UiRegression.Field(form, "_bodyHeight") - (int)UiRegression.Field(form, "_viewportHeight"), null);
                form.HandleNavigationKey(Keys.Home);
                check("pixel: keyboard returns to first account", (int)UiRegression.Field(form, "_scroll") == 0, null);
                check("pixel: Tab is not swallowed", !form.HandleNavigationKey(Keys.Tab), null);
            }
            using (WidgetForm form = new WidgetForm(Program.LoadConfiguration(true, "balance", null), true, "balance", 1f, false))
            {
                IList<AccountState> accounts = (IList<AccountState>)UiRegression.Field(form, "_accounts");
                AccountState balance = null;
                foreach (AccountState a in accounts) if (a.IsBalance) balance = a;
                balance.Balances.Add(new BalanceData { Currency = "CNY", Total = decimal.MaxValue, Available = true });
                balance.Balances.Add(new BalanceData { Currency = "USD", Total = .01m, Available = true });
                UiRegression.Invoke(form, "ResizeForContent", false);
                string text = form.AccountAccessibleText(balance);
                check("pixel: extreme balance stays complete with currencies", form.Width <= 360 && text.Replace(",", "").Contains(decimal.MaxValue.ToString("0.00"))
                    && text.Contains("USD 0.01"), null);
                string wrapped = form.BalanceDisplay(balance.Balances[0], form.Width);
                check("pixel: wrapped money preserves all digits and decimal group", wrapped.Replace("\n", "").Replace(",", "") == decimal.MaxValue.ToString("0.00")
                    && wrapped.EndsWith("335.00") && !wrapped.Contains(".\n"), null);
                using (Bitmap image = new Bitmap(form.Width, form.Height)) form.DrawToBitmap(image, form.ClientRectangle);
            }
            AppConfig original = Program.LoadConfiguration(true, "normal", null);
            int saves = 0;
            using (SettingsForm settings = new SettingsForm(original, false, true, 1f, delegate { saves++; return false; }))
            {
                ((TextBox)UiRegression.Field(settings, "_codexName")).Text = "尚未保存的名称";
                UiRegression.Invoke(settings, "SaveClicked", null, EventArgs.Empty);
                TextBox error = (TextBox)UiRegression.Field(settings, "_saveError");
                check("settings: failed save keeps draft and dialog open", saves == 1 && settings.UpdatedConfig == null
                    && settings.DialogResult != DialogResult.OK && !settings.IsDisposed
                    && ((TextBox)UiRegression.Field(settings, "_codexName")).Text == "尚未保存的名称", null);
                check("settings: failure is persistent inline and source unchanged", error.Text.Contains("保存失败")
                    && ((Panel)UiRegression.Field(settings, "_footer")).Height > 64
                    && original.Codex.Name != "尚未保存的名称" && ((Button)settings.AcceptButton).Enabled
                    && !((TextBox)UiRegression.Field(settings, "_codexName")).ReadOnly, null);
            }
            foreach (float scale in new[] { 1f, 1.5f, 2f })
            using (SettingsForm settings = new SettingsForm(original, false, false, scale, delegate { throw new Exception("Preview must not save"); }))
            {
                settings.ClientSize = new Size((int)(320 * scale), Math.Min(settings.ClientSize.Height, (int)(480 * scale)));
                settings.StartPosition = FormStartPosition.Manual;
                settings.Location = new Point(-20000, -20000);
                settings.Show();
                Panel scroll = (Panel)UiRegression.Field(settings, "_scroll");
                bool fits = true;
                foreach (Control c in scroll.Controls) if (c.Right > scroll.ClientSize.Width) fits = false;
                check("settings: narrow fields do not overflow at " + scale, fits && scroll.AutoScrollMinSize.Width == 0, null);
                Panel footer = (Panel)UiRegression.Field(settings, "_footer");
                Button save = (Button)settings.AcceptButton, cancel = (Button)settings.CancelButton;
                check("settings: fixed actions remain reachable at " + scale,
                    save.Right <= footer.Width && cancel.Left >= 0 && save.Bottom <= footer.Height && cancel.Right < save.Left, null);
                Control rail = (Control)UiRegression.Field(settings, "_rail");
                PropertyInfo thumb = typeof(PixelScrollRail).GetProperty("Thumb", BindingFlags.Instance | BindingFlags.NonPublic);
                int beforeThumb = ((Rectangle)thumb.GetValue(rail, null)).Top;
                SendMessage(scroll.Handle, 0x020A, new IntPtr(unchecked((int)0xFF880000)), IntPtr.Zero);
                Application.DoEvents();
                check("settings: wheel over content moves scroll indicator at " + scale,
                    scroll.AutoScrollPosition.Y < 0 && ((Rectangle)thumb.GetValue(rail, null)).Top > beforeThumb, null);
                UiRegression.Invoke(rail, "OnMouseWheel", new MouseEventArgs(MouseButtons.None, 0, 2, 20, -120));
                check("settings: themed rail drives native scroll at " + scale, scroll.AutoScrollPosition.Y < 0, null);
                ((TextBox)UiRegression.Field(settings, "_codexName")).Focus();
                check("settings: focused input scrolls back into view at " + scale,
                    ((TextBox)UiRegression.Field(settings, "_codexName")).Parent.Bottom > 0, null);
                ((TextBox)UiRegression.Field(settings, "_codexName")).Text = "添加前草稿";
                PixelButton add = null;
                foreach (Control c in scroll.Controls) if (c.Name == "add-account") add = (PixelButton)c;
                add.PerformClick();
                UiRegression.Invoke(settings, "SaveClicked", null, EventArgs.Empty);
                check("settings: account add preserves other drafts at " + scale, settings.UpdatedConfig != null
                    && settings.UpdatedConfig.Codex.Name == "添加前草稿" && settings.UpdatedConfig.Zhipu.Count == 2
                    && settings.UpdatedConfig.Zhipu[0].Id == original.Zhipu[0].Id, null);
            }
        }
    }
}
