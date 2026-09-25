using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;
using System.Windows.Forms;

namespace QuotaWidget
{
    internal static class ExpansionUiRegression
    {
        [DllImport("user32.dll")]
        private static extern IntPtr SendMessage(IntPtr window, int message, IntPtr wparam, IntPtr lparam);

        internal static void Run(Action<string, bool, string> check)
        {
            using (WidgetForm form = new WidgetForm(Program.LoadConfiguration(true, "normal", null), true, "normal", 1f, false))
            {
                IList<AccountState> accounts = (IList<AccountState>)UiRegression.Field(form, "_accounts");
                check("expansion: first check has meaningful pending text", form.CheckStatusText == "等待首次检查", null);
                DateTime completed = DateTime.UtcNow;
                accounts[0].Apply(new FetchResult { Ok = true, Windows = new List<QuotaWindow> {
                    new QuotaWindow { Kind = WindowKind.FiveHour, UsedPercent = 26 } } },
                    completed.ToLocalTime().AddMinutes(-2), completed.AddMinutes(-2), 10);
                accounts[0].Apply(new FetchResult { Error = "网络连接失败" }, completed.ToLocalTime(), completed, 10);
                UiRegression.Invoke(form, "OnAccountsChanged");
                check("expansion: completed failed request does not imply fresh data",
                    form.CheckStatusText == "最近请求结束 " + completed.ToLocalTime().ToString("HH:mm:ss")
                    && accounts[0].Stale && WidgetForm.AccountStatus(accounts[0]) == "数据过期"
                    && WidgetForm.QuotaValue(accounts[0].Windows[0]) == "74%", null);
                accounts[0].Apply(new FetchResult { Error = "请求过于频繁", StatusCode = 429 }, completed.ToLocalTime(), completed, 10);
                UiRegression.Invoke(form, "OnAccountsChanged");
                check("expansion: limited account retains check semantics and stale notice", form.CheckStatusLabel == "最近请求结束"
                    && WidgetForm.AccountStatus(accounts[0]) == "限流冷却" && WidgetForm.AccountNotice(accounts[0]).Contains("数据过期"), null);
                check("expansion: accessible footer shares visible meaning", form.AccessibilityObject.GetChild(accounts.Count).Value == form.CheckStatusText, null);
                foreach (AccountState account in accounts) account.Visible = false;
                check("expansion: empty footer replaces even a previous timestamp", form.CheckStatusText == "暂无可检查账号", null);
            }
            using (WidgetForm form = new WidgetForm(Program.LoadConfiguration(true, "config-error", null), true, "config-error", 1f, false))
                check("expansion: damaged config footer says checks stopped", form.CheckStatusText == "检查已停止", null);

            foreach (float scale in new[] { 1f, 1.5f, 2f })
            using (WidgetForm form = new WidgetForm(Program.LoadConfiguration(true, "balance", null), true, "balance", scale, false))
            {
                string display = form.BalanceDisplay(new BalanceData { Total = decimal.MaxValue }, (int)(360 * scale));
                bool fits = true;
                foreach (string line in display.Split('\n'))
                {
                    int width = (int)typeof(WidgetForm).GetMethod("TextWidth", BindingFlags.Instance | BindingFlags.NonPublic)
                        .Invoke(form, new[] { (object)line, UiRegression.Field(form, "_number") });
                    fits &= width <= (int)(336 * scale);
                }
                check("expansion: grouped extreme money fits and retains exact value at " + scale, fits
                    && decimal.Parse(display.Replace("\n", ""), NumberStyles.Number, CultureInfo.InvariantCulture) == decimal.MaxValue
                    && Regex.IsMatch(display, @"^\d{1,3}(?:,\n?\d{3})*\.\d{2}$"), null);
                check("expansion: ordinary money groups without changing decimals at " + scale,
                    form.BalanceDisplay(new BalanceData { Total = 1234567.89m }, (int)(360 * scale)) == "1,234,567.89"
                    && form.BalanceDisplay(new BalanceData { Total = .01m }, (int)(288 * scale)) == "0.01", null);
            }

            AppConfig config = Program.LoadConfiguration(true, "config-error", null);
            int saves = 0;
            using (SettingsForm settings = new SettingsForm(config, false, true, 1.5f, delegate { saves++; return true; }))
            {
                settings.StartPosition = FormStartPosition.Manual;
                settings.Location = new Point(-20000, -20000);
                settings.Show();
                Panel body = (Panel)UiRegression.Field(settings, "_scroll");
                check("expansion: damaged settings lock every editor and mutation action", EditorsLocked(body)
                    && !((Button)settings.AcceptButton).Enabled && ((Button)settings.CancelButton).Enabled, null);
                TextBox name = (TextBox)UiRegression.Field(settings, "_codexName");
                string before = name.Text;
                name.Focus(); name.SelectAll();
                SendMessage(name.Handle, 0x0102, new IntPtr('X'), IntPtr.Zero); // WM_CHAR to this synthetic native edit only.
                check("expansion: locked native text rejects user character input", name.Text == before, null);
                foreach (Control control in body.Controls)
                    if (control is Button) ((Button)control).PerformClick();
                check("expansion: disabled add and remove preserve account draft", ((System.Collections.IList)UiRegression.Field(settings, "_zhipuDraft")).Count == config.Zhipu.Count, null);
                settings.ClientSize = new Size(480, 600);
                check("expansion: settings rebuild cannot unlock damaged configuration", EditorsLocked(body), null);
                object[] key = { new Message(), Keys.End };
                bool handled = (bool)typeof(SettingsForm).GetMethod("ProcessCmdKey", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(settings, key);
                check("expansion: locked settings remain keyboard scrollable", handled && body.AutoScrollPosition.Y < 0, null);
                UiRegression.Invoke(settings, "SaveClicked", null, EventArgs.Empty);
                check("expansion: damaged config never invokes saver", saves == 0 && settings.UpdatedConfig == null, null);
                ((Button)settings.CancelButton).PerformClick();
                check("expansion: locked settings can close without mutating source", settings.DialogResult == DialogResult.Cancel
                    && config.LoadError && config.Codex.Name == before, null);
            }
        }

        private static bool EditorsLocked(Control body)
        {
            foreach (Control control in body.Controls)
            {
                PixelField field = control as PixelField;
                if (field != null && (!field.Editor.ReadOnly || field.Editor.TabStop)) return false;
                if ((control is CheckBox || control is NumericUpDown || control is Button) && control.Enabled) return false;
            }
            return body.Enabled;
        }
    }
}
