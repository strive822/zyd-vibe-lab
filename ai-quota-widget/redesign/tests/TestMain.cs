using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace QuotaWidget
{
    // Providers.cs 解析层单元测试入口。
    // 用 .NET Framework 自带 csc（C#5）编译，仅依赖 System.dll / System.Core.dll / System.Web.Extensions.dll。
    public static class TestMain
    {
        static int failures = 0;

        static int Main(string[] args)
        {
            string fixturesDir = FindFixturesDir();
            if (fixturesDir == null)
            {
                Console.Error.WriteLine("ERROR: cannot locate tests/fixtures directory (tried BaseDirectory/../tests/fixtures and CWD/tests/fixtures)");
                return 2;
            }

            string openaiSample = ReadFixture(fixturesDir, "openai_sample.json");
            string openaiClamp = ReadFixture(fixturesDir, "openai_clamp.json");
            string zhipuSample = ReadFixture(fixturesDir, "zhipu_sample.json");
            string zhipu429 = ReadFixture(fixturesDir, "zhipu_429.json");
            string deepseekSample = ReadFixture(fixturesDir, "deepseek_sample.json");

            TestOpenAISample(openaiSample);
            TestOpenAIClamp(openaiClamp);
            TestZhipuSample(zhipuSample);
            TestZhipu429(zhipu429);
            TestDeepSeekBalance(deepseekSample);
            TestCodexAuthDirect();
            TestCodexAuthIdTokenFallback();
            TestClassifyDurationSeconds();
            TestFormatCountdownNull();
            TestClampPercent();

            Console.WriteLine();
            if (failures == 0)
            {
                Console.WriteLine("SUMMARY: all tests passed");
                return 0;
            }
            Console.WriteLine("SUMMARY: " + failures + " assertion(s) FAILED");
            return 1;
        }

        // ---------- fixtures ----------

        static string FindFixturesDir()
        {
            string[] candidates = new string[]
            {
                Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..\\tests\\fixtures"),
                Path.Combine(Directory.GetCurrentDirectory(), "tests\\fixtures")
            };
            foreach (string candidate in candidates)
            {
                try
                {
                    if (Directory.Exists(candidate)) return Path.GetFullPath(candidate);
                }
                catch { }
            }
            return null;
        }

        static string ReadFixture(string dir, string name)
        {
            return File.ReadAllText(Path.Combine(dir, name), Encoding.UTF8);
        }

        // ---------- 断言工具 ----------

        static void Check(string name, bool condition, string detail)
        {
            if (condition)
            {
                Console.WriteLine("[PASS] " + name);
            }
            else
            {
                failures++;
                Console.WriteLine("[FAIL] " + name + (detail == null ? "" : ("  -> " + detail)));
            }
        }

        static bool Near(double actual, double expected)
        {
            return Math.Abs(actual - expected) <= 0.01;
        }

        static string Show(object value)
        {
            return value == null ? "<null>" : value.ToString();
        }

        // ---------- 用例 ----------

        static void TestOpenAISample(string json)
        {
            List<QuotaWindow> windows = Providers.ParseOpenAIUsage(json);
            Check("openai.sample: count == 2", windows != null && windows.Count == 2,
                "count=" + (windows == null ? "<null>" : windows.Count.ToString()));
            if (windows == null || windows.Count < 2) return;

            QuotaWindow primary = windows[0];
            Check("openai.sample: primary.Kind == FiveHour", primary.Kind == WindowKind.FiveHour, "kind=" + primary.Kind);
            Check("openai.sample: primary.UsedPercent ~= 34.2", Near(primary.UsedPercent, 34.2), "used=" + primary.UsedPercent);
            Check("openai.sample: primary.ResetAt != null && > now(unix s)",
                primary.ResetAt != null && primary.ResetAt.Value > Providers.NowUnixSeconds(),
                "resetAt=" + Show(primary.ResetAt) + " now=" + Providers.NowUnixSeconds());

            QuotaWindow secondary = windows[1];
            Check("openai.sample: secondary.Kind == Week", secondary.Kind == WindowKind.Week, "kind=" + secondary.Kind);
            Check("openai.sample: secondary.UsedPercent ~= 12.5", Near(secondary.UsedPercent, 12.5), "used=" + secondary.UsedPercent);
            Check("openai.sample: secondary.ResetAt == 1789900000 (ms->s)",
                secondary.ResetAt == 1789900000L, "resetAt=" + Show(secondary.ResetAt));
        }

        static void TestOpenAIClamp(string json)
        {
            List<QuotaWindow> windows = Providers.ParseOpenAIUsage(json);
            Check("openai.clamp: count == 1", windows != null && windows.Count == 1,
                "count=" + (windows == null ? "<null>" : windows.Count.ToString()));
            if (windows == null || windows.Count < 1) return;
            Check("openai.clamp: UsedPercent == 100", windows[0].UsedPercent == 100.0, "used=" + windows[0].UsedPercent);
        }

        static void TestZhipuSample(string json)
        {
            List<QuotaWindow> windows = Providers.ParseZhipuUsage(json);
            Check("zhipu.sample: count == 3", windows != null && windows.Count == 3,
                "count=" + (windows == null ? "<null>" : windows.Count.ToString()));
            if (windows == null || windows.Count < 3) return;

            Check("zhipu.sample: [0] Kind == FiveHour", windows[0].Kind == WindowKind.FiveHour, "kind=" + windows[0].Kind);
            Check("zhipu.sample: [0] UsedPercent ~= 34.0", Near(windows[0].UsedPercent, 34.0), "used=" + windows[0].UsedPercent);
            Check("zhipu.sample: [0] ResetAt == 1789890000", windows[0].ResetAt == 1789890000L, "resetAt=" + Show(windows[0].ResetAt));

            Check("zhipu.sample: [1] Kind == Week", windows[1].Kind == WindowKind.Week, "kind=" + windows[1].Kind);
            Check("zhipu.sample: [1] UsedPercent ~= 2.0", Near(windows[1].UsedPercent, 2.0), "used=" + windows[1].UsedPercent);
            Check("zhipu.sample: [1] ResetAt == 1790000000", windows[1].ResetAt == 1790000000L, "resetAt=" + Show(windows[1].ResetAt));

            Check("zhipu.sample: [2] Kind == Other", windows[2].Kind == WindowKind.Other, "kind=" + windows[2].Kind);
            Check("zhipu.sample: [2] DurationSeconds == 2592000", windows[2].DurationSeconds == 2592000, "duration=" + windows[2].DurationSeconds);
            Check("zhipu.sample: [2] UsedPercent ~= 10.0", Near(windows[2].UsedPercent, 10.0), "used=" + windows[2].UsedPercent);
            Check("zhipu.sample: [2] ResetAt == 1791000000", windows[2].ResetAt == 1791000000L, "resetAt=" + Show(windows[2].ResetAt));
        }

        static void TestZhipu429(string body)
        {
            List<QuotaWindow> windows = Providers.ParseZhipu429(body);
            Check("zhipu.429: count == 1", windows != null && windows.Count == 1,
                "count=" + (windows == null ? "<null>" : windows.Count.ToString()));
            if (windows == null || windows.Count < 1) return;
            Check("zhipu.429: Kind == FiveHour", windows[0].Kind == WindowKind.FiveHour, "kind=" + windows[0].Kind);
            Check("zhipu.429: UsedPercent == 100", windows[0].UsedPercent == 100.0, "used=" + windows[0].UsedPercent);
            Check("zhipu.429: ResetAt != null", windows[0].ResetAt != null, "resetAt=<null>");
        }

        static void TestDeepSeekBalance(string json)
        {
            BalanceData balance = Providers.ParseDeepSeekBalance(json);
            Check("deepseek.sample: parsed", balance != null, "balance=<null>");
            if (balance == null) return;
            Check("deepseek.sample: Currency == CNY", balance.Currency == "CNY", "currency=" + Show(balance.Currency));
            Check("deepseek.sample: Total == 42.50", balance.Total == 42.50m, "total=" + balance.Total.ToString());
            Check("deepseek.sample: Granted == 10.00", balance.Granted != null && balance.Granted.Value == 10.00m,
                "granted=" + Show(balance.Granted));
            Check("deepseek.sample: Available == true", balance.Available, "available=" + balance.Available);
        }

        static void TestCodexAuthDirect()
        {
            string json = "{\"OPENAI_API_KEY\":null,\"auth_mode\":\"chatgpt\",\"last_refresh\":\"2026-09-22T00:00:00\",\"tokens\":{\"id_token\":\"e30.x.sig\",\"access_token\":\"at\",\"refresh_token\":\"rt\",\"account_id\":\"acct_direct\"}}";
            CodexAuth auth = Providers.ParseCodexAuth(json);
            Check("codex.auth: parsed", auth != null, "auth=<null>");
            if (auth == null) return;
            Check("codex.auth: AccountId == acct_direct", auth.AccountId == "acct_direct", "accountId=" + Show(auth.AccountId));
            Check("codex.auth: AccessToken == at", auth.AccessToken == "at", "accessToken=" + Show(auth.AccessToken));
            Check("codex.auth: RefreshToken == rt", auth.RefreshToken == "rt", "refreshToken=" + Show(auth.RefreshToken));
        }

        // 测试侧 Base64Url 编码：标准 Base64 后 '+'→'-'、'/'→'_'，去掉 '=' 填充（与 Providers.Base64UrlDecode 互逆）。
        static string Base64UrlEncode(byte[] bytes)
        {
            string s = Convert.ToBase64String(bytes);
            s = s.Replace('+', '-').Replace('/', '_');
            while (s.EndsWith("=")) s = s.Substring(0, s.Length - 1);
            return s;
        }

        static void TestCodexAuthIdTokenFallback()
        {
            string payload = "{\"https://api.openai.com/auth\":{\"chatgpt_account_id\":\"acct_from_id\"},\"sub\":\"u\"}";
            string idToken = "x." + Base64UrlEncode(Encoding.UTF8.GetBytes(payload)) + ".sig";
            string json = "{\"OPENAI_API_KEY\":null,\"auth_mode\":\"chatgpt\",\"tokens\":{\"id_token\":\"" + idToken + "\",\"access_token\":\"at2\",\"refresh_token\":\"rt2\",\"account_id\":\"\"}}";
            CodexAuth auth = Providers.ParseCodexAuth(json);
            Check("codex.idtoken: parsed", auth != null, "auth=<null>");
            if (auth == null) return;
            Check("codex.idtoken: AccountId == acct_from_id", auth.AccountId == "acct_from_id",
                "accountId=" + Show(auth.AccountId));
        }

        static void TestClassifyDurationSeconds()
        {
            Check("classify: 18000 -> FiveHour", Providers.ClassifyDurationSeconds(18000) == WindowKind.FiveHour,
                "kind=" + Providers.ClassifyDurationSeconds(18000));
            Check("classify: 604800 -> Week", Providers.ClassifyDurationSeconds(604800) == WindowKind.Week,
                "kind=" + Providers.ClassifyDurationSeconds(604800));
            Check("classify: 3600 -> Other", Providers.ClassifyDurationSeconds(3600) == WindowKind.Other,
                "kind=" + Providers.ClassifyDurationSeconds(3600));
        }

        static void TestFormatCountdownNull()
        {
            Check("format-countdown: null -> null", Providers.FormatCountdown(null) == null,
                "result=" + Show(Providers.FormatCountdown(null)));
        }

        static void TestClampPercent()
        {
            double fromInt = Providers.ClampPercent(150);
            Check("clamp-percent: 150 -> 100", fromInt == 100.0, "result=" + fromInt);

            double fromString = Providers.ClampPercent("12.5");
            Check("clamp-percent: \"12.5\" ~= 12.5", Near(fromString, 12.5), "result=" + fromString);

            double fromNull = Providers.ClampPercent(null);
            Check("clamp-percent: null -> -1", fromNull == -1.0, "result=" + fromNull);
        }
    }
}
