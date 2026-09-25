using System;
using System.Drawing;
using System.Windows.Forms;

namespace QuotaWidget
{
    internal static class EdgeRemovalRegression
    {
        internal static void Run(Action<string, bool, string> check)
        {
            foreach (float scale in new[] { 1f, 1.5f, 2f })
            {
                AppConfig config = Program.LoadConfiguration(true, "normal", null);
                using (WidgetForm form = new WidgetForm(config, true, "normal", scale, false))
                using (Bitmap frame = form.RenderFrame())
                {
                    Color header = PixelTheme.ProviderHeader("codex");
                    check("edge-removal: provider band reaches both top corners at " + scale,
                        frame.GetPixel(0, 0).ToArgb() == header.ToArgb()
                        && frame.GetPixel(frame.Width - 1, 0).ToArgb() == header.ToArgb(), null);
                    check("edge-removal: footer reaches both bottom corners at " + scale,
                        frame.GetPixel(0, frame.Height - 1).ToArgb() == PixelTheme.Footer.ToArgb()
                        && frame.GetPixel(frame.Width - 1, frame.Height - 1).ToArgb() == PixelTheme.Footer.ToArgb(), null);
                    bool opaque = true;
                    for (int y = 0; y < frame.Height && opaque; y++)
                        for (int x = 0; x < frame.Width; x++)
                            if (frame.GetPixel(x, y).A != 255) { opaque = false; break; }
                    check("edge-removal: every widget pixel is opaque at " + scale,
                        opaque && form.Opacity == 1, null);
                    UiRegression.Invoke(form, "BuildMenu");
                    ContextMenuStrip menu = (ContextMenuStrip)UiRegression.Field(form, "_menu");
                    bool hasOpacityItem = false;
                    foreach (ToolStripItem item in menu.Items)
                        if (item.Text.Contains("透明")) hasOpacityItem = true;
                    check("edge-removal: menu has no opacity control at " + scale, !hasOpacityItem, null);
                }
            }
            using (SettingsForm settings = new SettingsForm(Program.LoadConfiguration(true, "normal", null), false, false))
            {
                bool hasOpacityControl = false;
                Panel body = (Panel)UiRegression.Field(settings, "_scroll");
                foreach (Control control in body.Controls)
                    if (control.Text.Contains("透明")) hasOpacityControl = true;
                check("edge-removal: settings has no opacity control", !hasOpacityControl, null);
            }
        }
    }
}
