using System;
using System.Collections.Generic;
using System.Drawing;
using System.Reflection;
using System.Windows.Forms;

namespace QuotaWidget
{
    internal static class CompactUiRegression
    {
        private const BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
        private static object Call(WidgetForm form, string name, params object[] args)
        { return typeof(WidgetForm).GetMethod(name, Private).Invoke(form, args); }
        private static int Metric(WidgetForm form, string name)
        { return (int)typeof(WidgetForm).GetProperty(name, Private).GetValue(form, null); }

        internal static void Run(Action<string, bool, string> check)
        {
            foreach (float scale in new[] { 1f, 1.5f, 2f })
            using (WidgetForm form = new WidgetForm(Program.LoadConfiguration(true, "reference", null), true, "reference", scale, false))
            {
                IList<AccountState> accounts = (IList<AccountState>)UiRegression.Field(form, "_accounts");
                foreach (AccountState account in accounts)
                {
                    FetchResult result = (FetchResult)typeof(WidgetForm).GetMethod("MockResult", BindingFlags.Static | BindingFlags.NonPublic)
                        .Invoke(null, new object[] { account.Provider, "reference" });
                    account.Apply(result, DateTime.Now, DateTime.UtcNow, 10);
                }
                UiRegression.Invoke(form, "OnAccountsChanged");
                int ordinaryHeight = form.Height;
                if (scale == 1.5f)
                    check("compact: actual 144-DPI layout meets reference area budget", form.Width <= 370 && form.Height <= 265
                        && form.Width * form.Height <= 350 * 230 * 1.15 && form.Width * form.Height >= 350 * 230 * .85,
                        form.Width + "x" + form.Height);
                Font small = (Font)UiRegression.Field(form, "_small");
                check("compact: reading type never below 12 device pixels at " + scale, small.Size >= 12, null);
                bool fits = true, sameTime = true;
                foreach (AccountState account in accounts)
                    foreach (QuotaWindow quota in account.Windows)
                    {
                        string detail = (string)Call(form, "QuotaDetail", quota);
                        int detailWidth = (int)Call(form, "TextWidth", detail, small);
                        fits &= detailWidth <= form.Width - (int)Math.Round(8 * scale) - Metric(form, "QuotaDetailX");
                        sameTime &= detail == (quota.Kind == WindowKind.FiveHour ? "19:26 · 2小时15分" : "29日 08:41 · 3天16小时");
                    }
                check("compact: all four reset rows fit without a second full-width line at " + scale, fits, null);
                check("compact: white-reference reset values and footer are reproduced at " + scale,
                    sameTime && form.CheckStatusText == "最近请求结束 17:11:30", null);
                Font number = (Font)UiRegression.Field(form, "_number");
                check("compact: 100 percent and 20 distinct segments fit at " + scale,
                    (int)Call(form, "TextWidth", "100%", number) <= Metric(form, "QuotaValueWidth")
                    && Metric(form, "QuotaValueWidth") >= 40, null);
                accounts[0].Name = new string('长', 80) + new string('A', 80);
                UiRegression.Invoke(form, "ResizeForContent", false);
                check("compact: long names grow content without reducing type at " + scale, form.Height > ordinaryHeight
                    && small.Size >= 12 && ((Font)UiRegression.Field(form, "_number")).Size == number.Size, null);
                accounts[0].Error = "连接失败，保留本账号旧值"; accounts[0].Stale = true;
                UiRegression.Invoke(form, "ResizeForContent", false);
                check("compact: stale data and reason remain accessible at " + scale,
                    form.AccountAccessibleText(accounts[0]).Contains("数据过期") && form.AccountAccessibleText(accounts[0]).Contains("连接失败"), null);
            }
        }
    }
}
