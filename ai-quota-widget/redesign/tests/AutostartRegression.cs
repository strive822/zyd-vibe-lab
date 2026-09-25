using System;
using System.Windows.Forms;

namespace QuotaWidget
{
    internal static class AutostartRegression
    {
        internal static void Run(Action<string, bool, string> check)
        {
            bool attempted = false;
            bool result = AppConfig.SetAutostart(true, "synthetic.exe", delegate(bool enable, string path)
            {
                attempted = enable && path == "synthetic.exe";
                throw new UnauthorizedAccessException();
            });
            check("autostart: registry write failure returns false without real registry access",
                attempted && !result, null);

            AppConfig config = Program.LoadConfiguration(true, "no-accounts", null);
            config.Codex.Enabled = false;
            config.Zhipu.Clear();
            config.DeepSeek.Enabled = false;
            bool enabled = false, fail = true, silentFailure = false;
            int writes = 0;
            using (WidgetForm widget = new WidgetForm(config, false, "normal", 1, false,
                delegate { return enabled; }, delegate(bool next, string path)
                {
                    writes++;
                    if (fail) return false;
                    if (silentFailure) return true;
                    enabled = next;
                    return true;
                }))
            {
                UiRegression.Invoke(widget, "BuildMenu");
                ToolStripMenuItem item = (ToolStripMenuItem)((ContextMenuStrip)UiRegression.Field(widget, "_menu")).Items[5];
                item.PerformClick();
                check("autostart: failed menu action stays unchecked and shows safe error",
                    writes == 1 && !enabled && !item.Checked &&
                    (string)UiRegression.Field(widget, "_uiMessage") ==
                    "开机自启设置失败，请检查当前用户权限后重试。", null);
                fail = false;
                silentFailure = true;
                item.PerformClick();
                check("autostart: unchanged registry state is not reported as success",
                    writes == 2 && !enabled &&
                    (string)UiRegression.Field(widget, "_uiMessage") ==
                    "开机自启设置失败，请检查当前用户权限后重试。", null);
                silentFailure = false;
                item.PerformClick();
                UiRegression.Invoke(widget, "BuildMenu");
                ToolStripMenuItem updated = (ToolStripMenuItem)((ContextMenuStrip)UiRegression.Field(widget, "_menu")).Items[5];
                check("autostart: successful retry updates check state and clears error",
                    writes == 3 && enabled && updated.Checked &&
                    UiRegression.Field(widget, "_uiMessage") == null, null);
            }
        }
    }
}
