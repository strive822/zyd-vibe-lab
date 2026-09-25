using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

namespace QuotaWidget
{
    internal static class ProviderRegression
    {
        private const string Usage = "{\"rate_limit\":{\"primary_window\":{\"limit_window_seconds\":18000,\"used_percent\":25}}}";

        public static void Run(Action<string, bool, string> check)
        {
            TestNumbers(check);
            TestBalances(check);
            TestReadOnlyCodex(check);
            TestCodexRetries(check);
            TestCancellationAndErrors(check);
            TestHttpCancellation(check);
        }

        private static void TestNumbers(Action<string, bool, string> check)
        {
            foreach (object invalid in new object[] { "NaN", "Infinity", "-Infinity", double.NaN,
                double.PositiveInfinity, float.NegativeInfinity })
                check("provider: non-finite value rejected", Providers.ToDouble(invalid) == null &&
                    Providers.ClampPercent(invalid) == -1 && Providers.EpochSeconds(invalid) == null, null);
            check("provider: seconds and milliseconds agree", Providers.EpochSeconds(1789900000L) == 1789900000L &&
                Providers.EpochSeconds(1789900000000L) == 1789900000L, null);
            check("provider: epoch outside DateTime range rejected",
                Providers.EpochSeconds(253402300800000L) == null && Providers.EpochSeconds("1e100") == null, null);
            check("provider: last representable epoch millisecond accepted",
                Providers.EpochSeconds(253402300799000L) == Providers.MaxEpochSeconds, null);
            foreach (long invalid in new long[] { 0, -1, long.MinValue, long.MaxValue, Providers.MaxEpochSeconds + 1 })
                check("provider: invalid reset safely displays unknown",
                    Providers.FormatFiveHourReset(invalid, DateTime.Now) == "重置时间未知" &&
                    Providers.FormatWeekReset(invalid, DateTime.Now) == "重置时间未知" &&
                    Providers.FormatResetAnchor(invalid) == null && Providers.FormatTimeAnchor(invalid) == null &&
                    Providers.FormatCountdown(invalid) == null, null);
            string invalidWindow = "{\"rate_limit\":{\"primary_window\":{\"limit_window_seconds\":18000,\"used_percent\":\"NaN\"}," +
                "\"secondary_window\":{\"limit_window_seconds\":604800,\"used_percent\":50,\"reset_at\":253402300800000}}}";
            List<QuotaWindow> windows = Providers.ParseOpenAIUsage(invalidWindow);
            check("provider: invalid quota row does not discard valid row", windows.Count == 1 &&
                windows[0].Kind == WindowKind.Week && windows[0].ResetAt == null, null);
            string hugeDuration = "{\"rate_limit\":{\"primary_window\":{\"limit_window_seconds\":1e30,\"used_percent\":20}}}";
            check("provider: overflowing duration rejected", Providers.ParseOpenAIUsage(hugeDuration).Count == 0 &&
                Providers.ClassifyDurationSeconds(int.MinValue) == WindowKind.Other, null);
            string hugeAfter = "{\"rate_limit\":{\"primary_window\":{\"limit_window_seconds\":18000,\"used_percent\":20,\"reset_after_seconds\":1e100}}}";
            check("provider: overflowing relative reset rejected", Providers.ParseOpenAIUsage(hugeAfter)[0].ResetAt == null, null);
            string hugeZhipuDuration = "{\"data\":{\"limits\":[{\"unit\":6,\"number\":2147483647,\"percentage\":10}]}}";
            check("provider: zhipu duration multiplication cannot wrap", Providers.ParseZhipuUsage(hugeZhipuDuration).Count == 0, null);
            DateTime now = new DateTime(2026, 9, 25, 0, 0, 0, DateTimeKind.Utc);
            check("provider: Retry-After supports seconds and HTTP date",
                Providers.ParseRetryAfter("120", now) == now.AddSeconds(120) &&
                Providers.ParseRetryAfter(now.AddMinutes(3).ToString("r", CultureInfo.InvariantCulture), now) == now.AddMinutes(3), null);
            check("provider: invalid Retry-After ignored", Providers.ParseRetryAfter("-10", now) == null &&
                Providers.ParseRetryAfter("999999999999999999999999", now) == null &&
                Providers.ParseRetryAfter("secret-response-content", now) == null, null);
        }

        private static void TestBalances(Action<string, bool, string> check)
        {
            check("provider: decimal keeps full precision", Providers.ToDecimal("79228162514264337593543950335") == decimal.MaxValue &&
                Providers.ToDecimal("-79228162514264337593543950335") == decimal.MinValue &&
                Providers.ToDecimal("0.1234567890123456789012345678") == 0.1234567890123456789012345678m, null);
            foreach (string invalid in new string[] { "NaN", "Infinity", "-Infinity", "1e100", "79228162514264337593543950336" })
            {
                string body = "{\"is_available\":true,\"balance_infos\":[{\"currency\":\"CNY\",\"total_balance\":\"42.50\"}," +
                    "{\"currency\":\"USD\",\"total_balance\":\"" + invalid + "\"}]}";
                string warning;
                List<BalanceData> balances = Providers.ParseDeepSeekBalances(body, out warning);
                check("provider: invalid total skips only its currency", balances.Count == 1 &&
                    balances[0].Currency == "CNY" && balances[0].Total == 42.50m && !string.IsNullOrEmpty(warning), null);
                body = "{\"is_available\":true,\"balance_infos\":[{\"currency\":\"CNY\",\"total_balance\":\"42.50\",\"granted_balance\":\"" + invalid + "\"}]}";
                balances = Providers.ParseDeepSeekBalances(body, out warning);
                check("provider: invalid granted amount retains total", balances.Count == 1 && balances[0].Total == 42.50m &&
                    balances[0].Granted == null && !string.IsNullOrEmpty(warning), null);
            }
            Providers.HttpSend send = delegate { return Reply(200,
                "{\"balance_infos\":[{\"currency\":\"CNY\",\"total_balance\":\"42.50\"},{\"currency\":\"USD\",\"total_balance\":\"NaN\"}]}"); };
            FetchResult result = Providers.FetchDeepSeek("synthetic-key", CancellationToken.None, send);
            check("provider: partial balance success carries warning", result.Ok && result.Balances.Count == 1 &&
                !string.IsNullOrEmpty(result.Warning), null);
            result = Providers.FetchDeepSeek("synthetic-key", CancellationToken.None, delegate { return Reply(200,
                "{\"balance_infos\":[{\"currency\":\"USD\",\"total_balance\":\"NaN\"}]}"); });
            check("provider: all invalid balances fail safely", !result.Ok && !string.IsNullOrEmpty(result.Error), null);
        }

        private static void TestReadOnlyCodex(Action<string, bool, string> check)
        {
            string directory = Path.Combine(Path.GetTempPath(), "quota-provider-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(directory);
            string path = Path.Combine(directory, "auth.json");
            const string original = "{\"tokens\":{\"access_token\":\"synthetic-access\",\"refresh_token\":\"synthetic-refresh\",\"account_id\":\"synthetic-account\"}}";
            try
            {
                File.WriteAllText(path, original, Encoding.UTF8);
                DateTime modified = File.GetLastWriteTimeUtc(path);
                int calls = 0;
                bool onlyUsageGets = true;
                FetchResult result = Providers.FetchCodex(path, CancellationToken.None,
                    delegate(string method, string url, Dictionary<string, string> headers, string body, CancellationToken token)
                    {
                        calls++;
                        onlyUsageGets &= method == "GET" && url == Providers.CodexUsageUrl && body == null;
                        return Reply(401, "synthetic-secret-body");
                    }, Providers.ReadCodexAuth);
                check("provider: unchanged Codex auth does not retry", calls == 1 && result.RequiresLogin && !result.Ok, null);
                check("provider: Codex performs usage GET only", onlyUsageGets, null);
                check("provider: auth bytes, timestamp, and sibling files unchanged", File.ReadAllText(path, Encoding.UTF8) == original &&
                    File.GetLastWriteTimeUtc(path) == modified && Directory.GetFiles(directory).Length == 1, null);
                check("provider: failed Codex request retains observed identity", result.AccountIdentity == "synthetic-account", null);
            }
            finally { Directory.Delete(directory, true); }
        }

        private static void TestCodexRetries(Action<string, bool, string> check)
        {
            foreach (int finalStatus in new int[] { 200, 401, 503 })
            {
                int reads = 0, calls = 0;
                bool newCredentialUsed = false;
                FetchResult result = Providers.FetchCodex("unused-synthetic-path", CancellationToken.None,
                    delegate(string method, string url, Dictionary<string, string> headers, string body, CancellationToken token)
                    {
                        calls++;
                        if (calls == 1) return Reply(401, null);
                        newCredentialUsed = headers["Authorization"] == "Bearer new-synthetic-token" && headers["chatgpt-account-id"] == "account-B";
                        return Reply(finalStatus, Usage);
                    }, delegate { reads++; return Auth(reads == 1 ? "old-synthetic-token" : "new-synthetic-token", reads == 1 ? "account-A" : "account-B"); });
                check("provider: changed auth retries at most once", reads == 2 && calls == 2 && newCredentialUsed, null);
                check("provider: changed account identity returned even on failure", result.AccountIdentity == "account-B" &&
                    result.Ok == (finalStatus == 200) && result.RequiresLogin == (finalStatus == 401), null);
            }
            int forbiddenReads = 0, forbiddenCalls = 0;
            FetchResult forbidden = Providers.FetchCodex("unused", CancellationToken.None,
                delegate { forbiddenCalls++; return Reply(403, "synthetic-secret-body"); },
                delegate { forbiddenReads++; return Auth("synthetic-token", "account-A"); });
            check("provider: 403 never triggers auth retry", forbiddenCalls == 1 && forbiddenReads == 1 &&
                !forbidden.RequiresLogin && forbidden.StatusCode == 403, null);
            int sameTokenReads = 0, sameTokenCalls = 0;
            FetchResult sameToken = Providers.FetchCodex("unused", CancellationToken.None,
                delegate { sameTokenCalls++; return Reply(sameTokenCalls == 1 ? 401 : 200, Usage); },
                delegate { sameTokenReads++; return Auth("same-synthetic-token", sameTokenReads == 1 ? "account-A" : "account-B"); });
            check("provider: changed account ID allows one retry", sameToken.Ok && sameTokenCalls == 2 && sameToken.AccountIdentity == "account-B", null);
            FetchResult missing = Providers.FetchCodex("unused", CancellationToken.None,
                delegate { throw new Exception("HTTP must not run without auth"); }, delegate { return null; });
            check("provider: missing auth requests official login", missing.RequiresLogin && missing.AccountIdentity == null, null);
            FetchResult fingerprint = Providers.FetchCodex("unused", CancellationToken.None,
                delegate { return Reply(500, null); }, delegate { return Auth("secret-token-value", null); });
            check("provider: missing ID uses safe credential fingerprint", fingerprint.AccountIdentity != null &&
                fingerprint.AccountIdentity.StartsWith("token-sha256:") && !fingerprint.AccountIdentity.Contains("secret-token-value"), null);
        }

        private static void TestCancellationAndErrors(Action<string, bool, string> check)
        {
            int calls = 0, reads = 0;
            Providers.HttpSend send = delegate { calls++; return Reply(200, Usage); };
            using (CancellationTokenSource canceled = new CancellationTokenSource())
            {
                canceled.Cancel();
                FetchResult codex = Providers.FetchCodex("unused", canceled.Token, send, delegate { reads++; return Auth("synthetic", "A"); });
                FetchResult zhipu = Providers.FetchZhipu("synthetic", "raw", canceled.Token, send);
                FetchResult deepseek = Providers.FetchDeepSeek("synthetic", canceled.Token, send);
                check("provider: pre-canceled work never reads auth or sends", reads == 0 && calls == 0 &&
                    codex.Canceled && zhipu.Canceled && deepseek.Canceled && codex.Error == null &&
                    zhipu.Error == null && deepseek.Error == null, null);
            }
            using (CancellationTokenSource active = new CancellationTokenSource())
            {
                FetchResult canceled = Providers.FetchDeepSeek("synthetic", active.Token,
                    delegate { active.Cancel(); active.Token.ThrowIfCancellationRequested(); return null; });
                check("provider: in-flight cancellation is not a failure", canceled.Canceled && !canceled.Ok && canceled.Error == null, null);
            }
            const string secret = "synthetic-secret-body-and-path";
            FetchResult error = Providers.FetchDeepSeek("synthetic", CancellationToken.None, delegate { return Reply(400, secret); });
            FetchResult thrown = Providers.FetchZhipu("synthetic", "raw", CancellationToken.None, delegate { throw new Exception(secret); });
            check("provider: response and exception contents never reach errors", error.Error != null && !error.Error.Contains(secret) &&
                thrown.Error != null && !thrown.Error.Contains(secret), null);
            DateTime retryAt = DateTime.UtcNow.AddMinutes(5);
            FetchResult limited = Providers.FetchDeepSeek("synthetic", CancellationToken.None,
                delegate { return new Providers.HttpReply { StatusCode = 429, RetryAfterUtc = retryAt }; });
            check("provider: rate-limit deadline reaches scheduler", limited.StatusCode == 429 && limited.RetryAfterUtc == retryAt, null);
        }

        private static void TestHttpCancellation(Action<string, bool, string> check)
        {
            // A loopback socket simulates a server that never sends response headers; no account endpoint is used.
            TcpListener listener = new TcpListener(IPAddress.Loopback, 0);
            using (ManualResetEvent accepted = new ManualResetEvent(false))
            using (ManualResetEvent release = new ManualResetEvent(false))
            using (ManualResetEvent finished = new ManualResetEvent(false))
            using (CancellationTokenSource cancellation = new CancellationTokenSource())
            {
                listener.Start();
                int port = ((IPEndPoint)listener.LocalEndpoint).Port;
                bool canceled = false;
                Thread server = new Thread(delegate()
                {
                    try
                    {
                        using (TcpClient client = listener.AcceptTcpClient())
                        {
                            accepted.Set();
                            release.WaitOne(5000);
                        }
                    }
                    catch (SocketException) { }
                    catch (ObjectDisposedException) { }
                });
                Thread requester = new Thread(delegate()
                {
                    try { Providers.SendHttp("GET", "http://127.0.0.1:" + port + "/", null, null, cancellation.Token); }
                    catch (OperationCanceledException) { canceled = true; }
                    finally { finished.Set(); }
                });
                server.IsBackground = requester.IsBackground = true;
                try
                {
                    server.Start();
                    requester.Start();
                    bool reachedServer = accepted.WaitOne(3000);
                    cancellation.Cancel();
                    bool returned = finished.WaitOne(3000);
                    check("provider: cancellation aborts blocked HTTP", reachedServer && returned && canceled, null);
                }
                finally
                {
                    cancellation.Cancel();
                    release.Set();
                    listener.Stop();
                    server.Join(3000);
                    requester.Join(3000);
                }
            }
        }

        private static CodexAuth Auth(string token, string accountId)
        {
            return new CodexAuth { AccessToken = token, AccountId = accountId };
        }

        private static Providers.HttpReply Reply(int status, string body)
        {
            return new Providers.HttpReply { StatusCode = status, Body = body };
        }
    }
}
