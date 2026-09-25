using System;
using System.Collections.Generic;
using System.Drawing;
using System.Reflection;
using System.Windows.Forms;

namespace QuotaWidget
{
    internal static class ColorLanguageRegression
    {
        private static double Linear(byte channel)
        { double value = channel / 255.0; return value <= .04045 ? value / 12.92 : Math.Pow((value + .055) / 1.055, 2.4); }
        private static double Luminance(Color c) { return .2126 * Linear(c.R) + .7152 * Linear(c.G) + .0722 * Linear(c.B); }
        private static double Contrast(Color a, Color b)
        { double x = Luminance(a), y = Luminance(b); return (Math.Max(x, y) + .05) / (Math.Min(x, y) + .05); }
        private const BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
        internal static void Run(Action<string, bool, string> check)
        {
            foreach (string provider in new[] { "codex", "zhipu", "deepseek" })
            {
                Color surface = PixelTheme.ProviderSurface(provider);
                check("color: body and status text contrast on " + provider,
                    Contrast(PixelTheme.Text, surface) >= 4.5 && Contrast(PixelTheme.Secondary, surface) >= 4.5
                    && Contrast(PixelTheme.Warning, surface) >= 4.5 && Contrast(PixelTheme.Error, surface) >= 4.5, null);
                check("color: provider heading and remaining value contrast on " + provider,
                    Contrast(PixelTheme.OnAccent, PixelTheme.ProviderHeader(provider)) >= 4.5
                    && Contrast(PixelTheme.Provider(provider), surface) >= 4.5, null);
            }
            check("color: settings input and footer text remain readable", Contrast(PixelTheme.Text, PixelTheme.Surface) >= 4.5
                && Contrast(PixelTheme.Error, PixelTheme.Surface) >= 4.5 && Contrast(PixelTheme.Secondary, PixelTheme.Footer) >= 4.5
                && Contrast(PixelTheme.Error, PixelTheme.Footer) >= 4.5, null);
            foreach (float scale in new[] { 1f, 1.5f, 2f })
            using (WidgetForm form = new WidgetForm(Program.LoadConfiguration(true, "normal", null), true, "normal", scale, false))
            {
                IList<AccountState> accounts = (IList<AccountState>)UiRegression.Field(form, "_accounts");
                foreach (AccountState account in accounts)
                {
                    FetchResult result = (FetchResult)typeof(WidgetForm).GetMethod("MockResult", BindingFlags.Static | BindingFlags.NonPublic)
                        .Invoke(null, new object[] { account.Provider, "normal" });
                    account.Apply(result, DateTime.Now, DateTime.UtcNow, 10);
                }
                UiRegression.Invoke(form, "ResizeForContent", false);
                using (Bitmap frame = form.RenderFrame())
                {
                    int tintPixels = 0, cyanPixels = 0, pinkPixels = 0;
                    for (int y = 0; y < frame.Height; y++)
                        for (int x = 0; x < frame.Width; x++)
                        {
                            int color = frame.GetPixel(x, y).ToArgb();
                            if (color == PixelTheme.ProviderSurface("codex").ToArgb() || color == PixelTheme.ProviderSurface("zhipu").ToArgb()) tintPixels++;
                            if (color == PixelTheme.ProviderHeader("codex").ToArgb()) cyanPixels++;
                            if (color == PixelTheme.ProviderHeader("zhipu").ToArgb()) pinkPixels++;
                        }
                    check("color: provider planes occupy the main reading area at " + scale,
                        tintPixels > frame.Width * frame.Height * .4 && cyanPixels > frame.Width * frame.Height * .04
                        && pinkPixels > frame.Width * frame.Height * .04, null);
                    int header = (int)typeof(WidgetForm).GetMethod("AccountHeaderH", Private).Invoke(form, new object[] { accounts[0], form.Width });
                    int numberHeight = (int)typeof(WidgetForm).GetProperty("QuotaNumberH", Private).GetValue(form, null);
                    int barY = header + numberHeight;
                    int first = frame.Width, last = -1;
                    for (int x = 0; x < frame.Width; x++)
                    {
                        int color = frame.GetPixel(x, barY).ToArgb();
                        if (color == PixelTheme.Provider("codex").ToArgb() || color == PixelTheme.Track.ToArgb())
                        { first = Math.Min(first, x); last = x; }
                    }
                    int valueWidth = (int)typeof(WidgetForm).GetProperty("QuotaValueWidth", Private).GetValue(form, null);
                    check("color: rendered energy rail spans label and value columns at " + scale,
                        first <= Math.Round(8 * scale) && last - first + 1 > valueWidth * 1.6, null);
                }
            }
            foreach (float scale in new[] { 1f, 1.5f, 2f })
            using (Form host = new Form { ShowInTaskbar = false, StartPosition = FormStartPosition.Manual, Location = new Point(-20000, -20000) })
            using (Font font = new Font("Microsoft YaHei UI", 14 * scale, GraphicsUnit.Pixel))
            using (PixelNumber number = new PixelNumber { Maximum = 100, Font = font, Width = (int)(100 * scale), BackColor = PixelTheme.Surface })
            {
                host.Controls.Add(number); host.Show();
                number.Enabled = false;
                Control caption = (Control)typeof(PixelNumber).GetField("_caption", Private).GetValue(number);
                bool readable = true;
                foreach (int value in new[] { 100, 10 })
                {
                    number.Value = value; Application.DoEvents();
                    // NumericUpDown.DrawToBitmap reorders overlapping native children.
                    // Test the caption raster and native z-order separately; composed desktop
                    // screenshots verify their final integration instead of that flattening path.
                    using (Bitmap frame = new Bitmap(caption.Width, caption.Height))
                    {
                        caption.DrawToBitmap(frame, caption.ClientRectangle);
                        int ink = 0;
                        for (int y = 0; y < frame.Height; y++)
                            for (int x = 0; x < frame.Width; x++)
                                if (frame.GetPixel(x, y).ToArgb() == PixelTheme.Secondary.ToArgb()) ink++;
                        readable &= ink > 0;
                    }
                }
                check("color: disabled config numbers paint readable 100 and 10 at " + scale, readable, null);
                check("color: read-only number and spinner stay disabled at " + scale, !number.Enabled && !number.CanSelect
                    && caption.Visible && number.Controls.GetChildIndex(caption) == 0, null);
                number.Enabled = true; Application.DoEvents();
                check("color: enabled numeric input keeps native editing at " + scale, number.CanSelect && !caption.Visible && number.Value == 10, null);
                host.Hide();
            }
        }
    }
}
