using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

namespace QuotaWidget
{
    internal static class UiRegression
    {
        const BindingFlags PrivateInstance = BindingFlags.NonPublic | BindingFlags.Instance;

        public static void Run(Action<string, bool, string> check)
        {
            int productionReads = 0;
            string previousPath = AppConfig.ConfigPath;
            AppConfig mock = Program.LoadConfiguration(true, "many", delegate { productionReads++; throw new Exception("production read"); });
            check("preview: never loads production config", productionReads == 0 && AppConfig.ConfigPath == previousPath, null);
            check("preview: all keys and paths are synthetic", mock.Codex.AuthJsonPath == "" && mock.DeepSeek.ApiKey == "" && mock.Zhipu.TrueForAll(z => z.ApiKey == ""), null);
            check("preview: many accounts exercise scrolling", mock.Zhipu.Count > 10, null);
            foreach (float scale in new[] { 1f, 1.5f, 2f })
            {
                using (WidgetForm form = new WidgetForm(mock, true, "many", scale, false))
                {
                    int body = (int)Field(form, "_bodyHeight");
                    int viewport = (int)Field(form, "_viewportHeight");
                    check("ui: content bounds at scale " + scale, form.Width > 0 && form.Height > 0 && viewport > 0, null);
                    if (body > viewport)
                    {
                        Invoke(form, "OnMouseWheel", new MouseEventArgs(MouseButtons.None, 0, 20, 20, -120));
                        check("ui: many accounts scroll at scale " + scale, (int)Field(form, "_scroll") > 0, null);
                    }
                    form.Hide();
                    check("ui: disposing never writes config", AppConfig.ConfigPath == previousPath, null);
                }
            }

            AppConfig original = Program.LoadConfiguration(true, "normal", null);
            using (SettingsForm settings = new SettingsForm(original, false, false))
            {
                ((TextBox)Field(settings, "_codexName")).Text = "Draft only";
                Invoke(settings, "SaveClicked", null, EventArgs.Empty);
                check("settings: preview saves draft only", settings.UpdatedConfig != null
                    && settings.UpdatedConfig.Codex.Name == "Draft only" && original.Codex.Name != "Draft only", null);
                check("settings: saving retains account ID", settings.UpdatedConfig.Zhipu[0].Id == original.Zhipu[0].Id, null);
            }
            using (SettingsForm settings = new SettingsForm(original, false, false))
            {
                ((TextBox)Field(settings, "_codexName")).Text = "unsaved";
                settings.DialogResult = DialogResult.Cancel;
                check("settings: cancel leaves source unchanged", settings.UpdatedConfig == null && original.Codex.Name != "unsaved", null);
            }
            using (SettingsForm settings = new SettingsForm(original, false, true, 1f, delegate { return false; }))
            {
                settings.StartPosition = FormStartPosition.Manual;
                settings.Location = new Point(-20000, -20000);
                settings.Show();
                TextBox name = (TextBox)Field(settings, "_codexName");
                name.Text = "retry draft";
                Invoke(settings, "SaveClicked", null, EventArgs.Empty);
                check("settings: failed persistence retains editable draft and reports error",
                    settings.UpdatedConfig == null && !settings.IsDisposed && name.Text == "retry draft" &&
                    original.Codex.Name != "retry draft" &&
                    ((TextBox)Field(settings, "_saveError")).Visible &&
                    ((Button)Field(settings, "_saveButton")).Enabled, null);
            }
            original.LoadError = true;
            using (SettingsForm settings = new SettingsForm(original, false, false))
                check("settings: damaged source disables saving", !((Button)settings.AcceptButton).Enabled && settings.UpdatedConfig == null, null);
            using (WidgetForm form = new WidgetForm(original, true, "normal", 1f, false))
            {
                int requests = 0;
                ((RefreshCoordinator)Field(form, "_coordinator")).Dispose();
                using (RefreshCoordinator coordinator = new RefreshCoordinator(
                    delegate { requests++; return new FetchResult { Ok = true }; }, () => DateTime.UtcNow,
                    action => action(), delegate { }, action => action()))
                {
                    coordinator.Reconcile(original);
                    typeof(WidgetForm).GetField("_coordinator", PrivateInstance).SetValue(form, coordinator);
                    typeof(WidgetForm).GetField("_accounts", PrivateInstance).SetValue(form, coordinator.Accounts);
                    Invoke(form, "BuildMenu");
                    ContextMenuStrip menu = (ContextMenuStrip)Field(form, "_menu");
                    ToolStripMenuItem accountMenu = (ToolStripMenuItem)menu.Items[2];
                    accountMenu.DropDownItems[0].PerformClick();
                    accountMenu.DropDownItems[0].PerformClick();
                    form.RefreshNow();
                    Invoke(form, "OnTick", null, EventArgs.Empty);
                    check("ui: invalid config blocks every refresh entry point", requests == 0, null);
                    check("preview: autostart control is disabled", !menu.Items[5].Enabled, null);
                }
            }
            AppConfig lifecycle = Program.LoadConfiguration(true, "no-accounts", null);
            lifecycle.Ui.TopMost = false;
            using (WidgetForm form = new WidgetForm(lifecycle, true, "no-accounts", 1f, false))
            {
                form.Location = new Point(-20000, -20000);
                form.Show();
                form.Close();
                check("ui: ordinary close hides without disposing", !form.Visible && !form.IsDisposed, null);
                form.ShowFromTray();
                check("ui: tray restoration handler shows hidden form", form.Visible && form.WindowState == FormWindowState.Normal, null);
                Invoke(form, "ExitApp");
                check("ui: exit handler closes the form", form.IsDisposed || !form.Visible, null);
            }
        }

        internal static object Field(object instance, string name)
        {
            return instance.GetType().GetField(name, PrivateInstance).GetValue(instance);
        }

        internal static void Invoke(object instance, string name, params object[] arguments)
        {
            instance.GetType().GetMethod(name, PrivateInstance).Invoke(instance, arguments);
        }

        // Optional rendering diagnostics: draws this application's controls, not the user's desktop.
        public static void RenderPreviews(string output)
        {
            Directory.CreateDirectory(output);
            foreach (float scale in new[] { 1f, 1.5f, 2f })
            foreach (string scenario in new[] { "normal", "stale", "error", "empty", "no-accounts", "balance", "many", "partial", "login", "limited", "long", "extreme", "unknown", "loading", "refresh-error", "config-error" })
            {
                AppConfig config = Program.LoadConfiguration(true, scenario, null);
                using (WidgetForm form = new WidgetForm(config, true, scenario, scale, false))
                {
                    IList<AccountState> accounts = (IList<AccountState>)Field(form, "_accounts");
                    MethodInfo mockResult = typeof(WidgetForm).GetMethod("MockResult", BindingFlags.NonPublic | BindingFlags.Static);
                    foreach (AccountState account in accounts)
                        if (scenario == "loading") account.Fetching = true;
                        else if (scenario != "config-error")
                            account.Apply((FetchResult)mockResult.Invoke(null, new object[] { account.Provider, scenario }), DateTime.Now, DateTime.UtcNow, 10);
                    Invoke(form, "OnAccountsChanged");
                    using (Bitmap bitmap = new Bitmap(form.Width, form.Height))
                    {
                        form.DrawToBitmap(bitmap, form.ClientRectangle);
                        bitmap.Save(Path.Combine(output, scenario + "-" + (scale * 100).ToString("0") + ".png"), ImageFormat.Png);
                    }
                }
            }
            using (SettingsForm settings = new SettingsForm(Program.LoadConfiguration(true, "normal", null), false, false))
            {
                // Standard WinForms child controls need visible handles before WM_PRINT.
                // Keep this synthetic test window off screen; no desktop pixels are captured.
                settings.StartPosition = FormStartPosition.Manual;
                settings.Location = new Point(-20000, -20000);
                settings.Show();
                settings.PerformLayout();
                using (Bitmap bitmap = new Bitmap(settings.Width, settings.Height))
                {
                    settings.DrawToBitmap(bitmap, new Rectangle(Point.Empty, settings.Size));
                    bitmap.Save(Path.Combine(output, "settings.png"), ImageFormat.Png);
                }
                settings.Close();
            }
            foreach (float scale in new[] { 1f, 1.5f, 2f })
            foreach (string state in new[] { "focus", "bottom", "failure", "disabled" })
            {
                AppConfig config = Program.LoadConfiguration(true, "normal", null);
                config.LoadError = state == "disabled";
                using (SettingsForm settings = new SettingsForm(config, false, state == "failure", scale, delegate { return false; }))
                {
                    settings.StartPosition = FormStartPosition.Manual;
                    settings.Location = new Point(-20000, -20000);
                    settings.Show();
                    if (state == "focus") ((TextBox)Field(settings, "_codexName")).Focus();
                    if (state == "failure") Invoke(settings, "SaveClicked", null, EventArgs.Empty);
                    if (state == "bottom")
                    {
                        NumericUpDown interval = (NumericUpDown)Field(settings, "_interval");
                        ((Panel)Field(settings, "_scroll")).ScrollControlIntoView(interval);
                        interval.Focus();
                    }
                    settings.PerformLayout();
                    using (Bitmap bitmap = new Bitmap(settings.Width, settings.Height))
                    {
                        settings.DrawToBitmap(bitmap, new Rectangle(Point.Empty, settings.Size));
                        bitmap.Save(Path.Combine(output, "settings-" + state + "-" + (scale * 100) + ".png"), ImageFormat.Png);
                    }
                    settings.Close();
                }
            }
        }
    }
}
