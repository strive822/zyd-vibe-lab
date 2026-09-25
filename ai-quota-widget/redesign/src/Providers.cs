using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Web.Script.Serialization;

namespace QuotaWidget
{
    public enum WindowKind { FiveHour = 0, Week = 1, Other = 2 }

    public class QuotaWindow
    {
        public WindowKind Kind;
        public int DurationSeconds;
        public double UsedPercent;
        public long? ResetAt; // epoch 秒；null 表示未知

        public string Label()
        {
            if (Kind == WindowKind.FiveHour) return "5h";
            if (Kind == WindowKind.Week) return "周";
            int s = DurationSeconds;
            if (s > 0 && s % 86400 == 0) return (s / 86400) + "d";
            if (s > 0) return (s / 3600) + "h";
            return "?";
        }
    }

    public class BalanceData
    {
        public string Currency;
        public decimal Total;
        public decimal? Granted;
        public bool Available = true;
    }

    public class FetchResult
    {
        public bool Ok;
        public int StatusCode;
        public string Error;
        public string Warning;
        public bool Stale;
        public bool Canceled;
        public bool RequiresLogin;
        public string AccountIdentity;
        public DateTime? RetryAfterUtc;
        public List<QuotaWindow> Windows = new List<QuotaWindow>();
        public BalanceData Balance;
        public List<BalanceData> Balances = new List<BalanceData>();
    }

    public class CodexAuth
    {
        public string AccessToken;
        public string AccountId;
        public string IdToken;
    }

    public static class Providers
    {
        public const string CodexUsageUrl = "https://chatgpt.com/backend-api/wham/usage";
        public const string ZhipuQuotaUrl = "https://open.bigmodel.cn/api/monitor/usage/quota/limit";
        public const string DeepSeekBalanceUrl = "https://api.deepseek.com/user/balance";
        public const int FiveHourSeconds = 18000;
        public const int WeekSeconds = 604800;

        internal delegate HttpReply HttpSend(string method, string url, Dictionary<string, string> headers,
            string body, CancellationToken cancellationToken);

        internal sealed class HttpReply
        {
            internal int StatusCode;
            internal string Body;
            internal DateTime? RetryAfterUtc;
            internal bool TimedOut;
        }
        static readonly Regex ZhipuCodeRegex = new Regex("\"code\"\\s*:\\s*\"?(1310|1316|1317)\"?", RegexOptions.Compiled);
        static readonly Regex ZhipuDateRegex = new Regex("\\d{4}-\\d{2}-\\d{2}[ T]\\d{2}:\\d{2}:\\d{2}", RegexOptions.Compiled);

        static readonly DateTime EpochUtc = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);
        internal const long MaxEpochSeconds = 253402300799L;

        // ---------- 通用小工具 ----------

        public static long NowUnixSeconds()
        {
            return (long)(DateTime.UtcNow - EpochUtc).TotalSeconds;
        }

        public static double ClampPercent(object value)
        {
            double? n = ToDouble(value);
            if (n == null) return -1;
            if (n.Value < 0) return 0;
            if (n.Value > 100) return 100;
            return n.Value;
        }

        public static double? ToDouble(object value)
        {
            if (value == null) return null;
            double number;
            if (value is int || value is long || value is double || value is decimal || value is float || value is short || value is byte)
                number = Convert.ToDouble(value, CultureInfo.InvariantCulture);
            else
            {
                string s = value as string;
                if (string.IsNullOrWhiteSpace(s) ||
                    !double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out number)) return null;
            }
            return double.IsNaN(number) || double.IsInfinity(number) ? (double?)null : number;
        }

        public static decimal? ToDecimal(object value)
        {
            if (value == null) return null;
            if (value is decimal) return (decimal)value;
            if (!(value is string || value is int || value is long || value is double ||
                value is float || value is short || value is byte)) return null;
            decimal number;
            return decimal.TryParse(Convert.ToString(value, CultureInfo.InvariantCulture), NumberStyles.Float,
                CultureInfo.InvariantCulture, out number) ? (decimal?)number : null;
        }

        public static long? EpochSeconds(object value)
        {
            double? n = ToDouble(value);
            if (n == null || n.Value <= 0) return null;
            double seconds = n.Value > 10000000000L ? n.Value / 1000 : n.Value;
            if (seconds < 1 || seconds > MaxEpochSeconds) return null;
            return (long)Math.Floor(seconds);
        }

        private static bool TryResetTime(long? resetAt, out DateTime local)
        {
            local = DateTime.MinValue;
            if (resetAt == null || resetAt.Value <= 0 || resetAt.Value > MaxEpochSeconds) return false;
            try { local = EpochUtc.AddSeconds(resetAt.Value).ToLocalTime(); return true; }
            catch (ArgumentOutOfRangeException) { return false; }
        }

        public static WindowKind ClassifyDurationSeconds(int seconds)
        {
            if (Math.Abs((long)seconds - FiveHourSeconds) < 60) return WindowKind.FiveHour;
            if (Math.Abs((long)seconds - WeekSeconds) < 60) return WindowKind.Week;
            return WindowKind.Other;
        }

        private static readonly string[] WeekDayNames = { "周日", "周一", "周二", "周三", "周四", "周五", "周六" };

        // 周窗口的绝对重置锚点：给可计划性，代替小时级倒计时心算
        public static string FormatResetAnchor(long? resetAt)
        {
            DateTime dt;
            if (!TryResetTime(resetAt, out dt)) return null;
            return WeekDayNames[(int)dt.DayOfWeek] + " " + dt.ToString("HH:mm");
        }

        // 5h 窗口的绝对时刻：同日 HH:mm，跨天补日期
        public static string FormatTimeAnchor(long? resetAt)
        {
            DateTime dt;
            if (!TryResetTime(resetAt, out dt)) return null;
            if (dt.Date == DateTime.Now.Date) return dt.ToString("HH:mm");
            if (dt.Date == DateTime.Now.Date.AddDays(1)) return "明 " + dt.ToString("HH:mm");
            return dt.ToString("M/d HH:mm");
        }

        public static string FormatCountdown(long? resetAt)
        {
            DateTime ignored;
            if (!TryResetTime(resetAt, out ignored)) return null;
            long secs = resetAt.Value - NowUnixSeconds();
            if (secs < 0) secs = 0;
            long d = secs / 86400;
            long h = (secs % 86400) / 3600;
            long m = (secs % 3600) / 60;
            if (d > 0) return d + "d" + h + "h";
            if (h > 0) return h + "h" + m + "m";
            if (m > 0) return m + "m";
            return "<1m";
        }

        public static string FormatFiveHourReset(long? resetAt, DateTime now)
        {
            DateTime dt;
            if (!TryResetTime(resetAt, out dt)) return "重置时间未知";
            string anchor = dt.Date == now.Date ? dt.ToString("HH:mm")
                : dt.ToString("d日 HH:mm");
            long minutes = Math.Max(0, (long)Math.Ceiling((dt - now).TotalMinutes));
            return anchor + " · " + (minutes / 60) + "小时" + (minutes % 60) + "分";
        }

        public static string FormatWeekReset(long? resetAt, DateTime now)
        {
            DateTime dt;
            if (!TryResetTime(resetAt, out dt)) return "重置时间未知";
            long hours = Math.Max(0, (long)Math.Ceiling((dt - now).TotalHours));
            return dt.ToString("d日 HH:mm") +
                " · " + (hours / 24) + "天" + (hours % 24) + "小时";
        }

        public static string Truncate(string s, int max)
        {
            if (s == null) return null;
            return s.Length <= max ? s : s.Substring(0, max) + "…";
        }

        static Dictionary<string, object> AsDict(object o) { return o as Dictionary<string, object>; }
        static object[] AsArray(object o) { return o as object[]; }
        static string AsStr(object o) { return o as string; }

        static object GetItem(Dictionary<string, object> d, string key)
        {
            object v;
            if (d != null && d.TryGetValue(key, out v)) return v;
            return null;
        }

        public static Dictionary<string, object> ParseJsonObject(string json)
        {
            if (string.IsNullOrEmpty(json)) return null;
            try { return AsDict(new JavaScriptSerializer { MaxJsonLength = int.MaxValue }.DeserializeObject(json)); }
            catch { return null; }
        }

        // ---------- OpenAI Codex ----------

        public static List<QuotaWindow> ParseOpenAIUsage(string json)
        {
            var list = new List<QuotaWindow>();
            Dictionary<string, object> root = ParseJsonObject(json);
            if (root == null) return list;
            Dictionary<string, object> rateLimit = AsDict(GetItem(root, "rate_limit"));
            if (rateLimit == null) return list;
            AddOpenAIWindow(list, AsDict(GetItem(rateLimit, "primary_window")));
            AddOpenAIWindow(list, AsDict(GetItem(rateLimit, "secondary_window")));
            return list;
        }

        static void AddOpenAIWindow(List<QuotaWindow> list, Dictionary<string, object> w)
        {
            if (w == null) return;
            double? duration = ToDouble(GetItem(w, "limit_window_seconds"));
            double used = ClampPercent(GetItem(w, "used_percent"));
            if (duration == null || duration.Value < 1 || duration.Value > int.MaxValue || used < 0) return;
            QuotaWindow qw = new QuotaWindow();
            qw.DurationSeconds = (int)Math.Floor(duration.Value);
            qw.UsedPercent = used;
            qw.Kind = ClassifyDurationSeconds(qw.DurationSeconds);
            long? resetAt = EpochSeconds(GetItem(w, "reset_at"));
            if (resetAt == null)
            {
                double? after = ToDouble(GetItem(w, "reset_after_seconds"));
                long now = NowUnixSeconds();
                if (after != null && after.Value >= 0 && after.Value <= MaxEpochSeconds - now)
                    resetAt = now + (long)Math.Floor(after.Value);
            }
            qw.ResetAt = resetAt;
            list.Add(qw);
        }

        public static string ResolveCodexAuthPath(string configured)
        {
            if (!string.IsNullOrEmpty(configured)) return Environment.ExpandEnvironmentVariables(configured);
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".codex", "auth.json");
        }

        public static CodexAuth ParseCodexAuth(string json)
        {
            Dictionary<string, object> root = ParseJsonObject(json);
            if (root == null) return null;
            Dictionary<string, object> tokens = AsDict(GetItem(root, "tokens"));
            if (tokens == null) return null;
            CodexAuth auth = new CodexAuth();
            auth.AccessToken = AsStr(GetItem(tokens, "access_token"));
            auth.AccountId = AsStr(GetItem(tokens, "account_id"));
            auth.IdToken = AsStr(GetItem(tokens, "id_token"));
            if (string.IsNullOrEmpty(auth.AccountId) && !string.IsNullOrEmpty(auth.IdToken))
                auth.AccountId = AccountIdFromIdToken(auth.IdToken);
            return auth;
        }

        public static string AccountIdFromIdToken(string idToken)
        {
            try
            {
                if (string.IsNullOrEmpty(idToken)) return null;
                string[] parts = idToken.Split('.');
                if (parts.Length < 2) return null;
                string json = Encoding.UTF8.GetString(Base64UrlDecode(parts[1]));
                Dictionary<string, object> payload = ParseJsonObject(json);
                if (payload == null) return null;
                Dictionary<string, object> authClaim = AsDict(GetItem(payload, "https://api.openai.com/auth"));
                if (authClaim == null) return null;
                return AsStr(GetItem(authClaim, "chatgpt_account_id"));
            }
            catch { return null; }
        }

        public static byte[] Base64UrlDecode(string input)
        {
            string s = input.Replace('-', '+').Replace('_', '/');
            int pad = s.Length % 4;
            if (pad == 2) s += "==";
            else if (pad == 3) s += "=";
            else if (pad == 1) s += "===";
            return Convert.FromBase64String(s);
        }

        public static CodexAuth ReadCodexAuth(string authJsonPath)
        {
            return ReadCodexAuth(authJsonPath, CancellationToken.None);
        }

        public static CodexAuth ReadCodexAuth(string authJsonPath, CancellationToken cancellationToken)
        {
            cancellationToken.ThrowIfCancellationRequested();
            string path = ResolveCodexAuthPath(authJsonPath);
            for (int i = 0; i < 3; i++)
            {
                cancellationToken.ThrowIfCancellationRequested();
                try
                {
                    if (!File.Exists(path)) return null;
                    string json = File.ReadAllText(path, Encoding.UTF8);
                    cancellationToken.ThrowIfCancellationRequested();
                    return ParseCodexAuth(json);
                }
                catch (OperationCanceledException) { throw; }
                catch (IOException)
                {
                    // The official client may be replacing its file. Wait without blocking cancellation.
                    if (i < 2 && cancellationToken.WaitHandle.WaitOne(120))
                        cancellationToken.ThrowIfCancellationRequested();
                }
                catch { return null; }
            }
            return null;
        }

        private static string CodexIdentity(CodexAuth auth)
        {
            if (auth == null) return null;
            if (!string.IsNullOrEmpty(auth.AccountId)) return auth.AccountId;
            if (string.IsNullOrEmpty(auth.AccessToken)) return null;
            // When the account ID is absent, never expose the credential as a cache key.
            using (SHA256 sha = SHA256.Create())
                return "token-sha256:" + BitConverter.ToString(sha.ComputeHash(
                    Encoding.UTF8.GetBytes(auth.AccessToken))).Replace("-", "").ToLowerInvariant();
        }

        public static FetchResult FetchCodex(string authJsonPath)
        {
            return FetchCodex(authJsonPath, CancellationToken.None);
        }

        public static FetchResult FetchCodex(string authJsonPath, CancellationToken cancellationToken)
        {
            return FetchCodex(authJsonPath, cancellationToken, SendHttp, ReadCodexAuth);
        }

        internal static FetchResult FetchCodex(string authJsonPath, CancellationToken cancellationToken,
            HttpSend send, Func<string, CancellationToken, CodexAuth> readAuth)
        {
            FetchResult result = new FetchResult();
            try
            {
                cancellationToken.ThrowIfCancellationRequested();
                CodexAuth auth = readAuth(authJsonPath, cancellationToken);
                cancellationToken.ThrowIfCancellationRequested();
                result.AccountIdentity = CodexIdentity(auth);
                if (auth == null || string.IsNullOrEmpty(auth.AccessToken))
                {
                    result.RequiresLogin = true;
                    result.Error = "无法读取 Codex 登录信息，请在官方客户端重新登录";
                    return result;
                }
                for (int attempt = 0; attempt < 2; attempt++)
                {
                    cancellationToken.ThrowIfCancellationRequested();
                    result.AccountIdentity = CodexIdentity(auth);
                    var headers = new Dictionary<string, string>();
                    headers["Authorization"] = "Bearer " + auth.AccessToken;
                    if (!string.IsNullOrEmpty(auth.AccountId)) headers["chatgpt-account-id"] = auth.AccountId;
                    headers["originator"] = "codex-usage-widget";
                    HttpReply response = send("GET", CodexUsageUrl, headers, null, cancellationToken);
                    cancellationToken.ThrowIfCancellationRequested();
                    result.StatusCode = response.StatusCode;
                    result.RetryAfterUtc = response.RetryAfterUtc;
                    if (response.StatusCode == 200)
                    {
                        List<QuotaWindow> windows = ParseOpenAIUsage(response.Body);
                        if (windows.Count == 0) { result.Error = "Codex 未返回可识别额度窗口"; return result; }
                        result.Ok = true;
                        result.Windows = windows;
                        return result;
                    }
                    if (response.StatusCode == 401)
                    {
                        if (attempt == 0)
                        {
                            CodexAuth current = readAuth(authJsonPath, cancellationToken);
                            cancellationToken.ThrowIfCancellationRequested();
                            string currentIdentity = CodexIdentity(current);
                            if (currentIdentity != null) result.AccountIdentity = currentIdentity;
                            if (current != null && !string.IsNullOrEmpty(current.AccessToken) &&
                                (current.AccessToken != auth.AccessToken || current.AccountId != auth.AccountId))
                            {
                                auth = current;
                                continue;
                            }
                        }
                        result.RequiresLogin = true;
                        result.Error = "Codex 登录已失效，请在官方客户端重新登录";
                        return result;
                    }
                    result.Error = response.StatusCode == 403 ? "Codex 拒绝访问，请检查账号权限" :
                        RequestError("Codex", response);
                    return result;
                }
            }
            catch (OperationCanceledException) { result.Canceled = true; }
            catch { result.Error = "Codex 查询失败，请稍后重试"; }
            return result;
        }

        // ---------- 智谱 GLM Coding Plan ----------

        static int DurationFromZhipuUnit(int unit, int number)
        {
            long scale = unit == 3 ? 3600 : unit == 6 ? 604800 : unit == 2 ? 86400 : 0;
            long seconds = scale * number;
            return seconds > 0 && seconds <= int.MaxValue ? (int)seconds : 0;
        }

        public static List<QuotaWindow> ParseZhipuUsage(string json)
        {
            var list = new List<QuotaWindow>();
            Dictionary<string, object> root = ParseJsonObject(json);
            if (root == null) return list;
            Dictionary<string, object> data = AsDict(GetItem(root, "data"));
            if (data == null) return list;
            object[] limits = AsArray(GetItem(data, "limits"));
            if (limits == null) return list;
            foreach (object item in limits)
            {
                Dictionary<string, object> limit = AsDict(item);
                if (limit == null) continue;
                double? unit = ToDouble(GetItem(limit, "unit"));
                double? number = ToDouble(GetItem(limit, "number"));
                double used = ClampPercent(GetItem(limit, "percentage"));
                if (unit == null || number == null || used < 0 || unit < 0 || unit > int.MaxValue ||
                    number <= 0 || number > int.MaxValue || unit != Math.Floor(unit.Value) ||
                    number != Math.Floor(number.Value)) continue;
                int seconds = DurationFromZhipuUnit((int)unit.Value, (int)number.Value);
                if (seconds <= 0) continue;
                QuotaWindow qw = new QuotaWindow();
                qw.DurationSeconds = seconds;
                qw.UsedPercent = used;
                qw.Kind = ClassifyDurationSeconds(seconds);
                qw.ResetAt = EpochSeconds(GetItem(limit, "nextResetTime"));
                list.Add(qw);
            }
            return DedupeWindows(list);
        }

        // 与参考实现 normalizeWindows 的去重语义一致：5h/周按类别去重，其他窗口按时长去重
        static List<QuotaWindow> DedupeWindows(List<QuotaWindow> list)
        {
            List<QuotaWindow> result = new List<QuotaWindow>();
            HashSet<string> seen = new HashSet<string>();
            foreach (QuotaWindow w in list)
            {
                string key = w.Kind == WindowKind.Other ? "d" + w.DurationSeconds : "k" + (int)w.Kind;
                if (!seen.Add(key)) continue;
                result.Add(w);
            }
            return result;
        }

        public static List<QuotaWindow> ParseZhipu429(string body)
        {
            var list = new List<QuotaWindow>();
            if (string.IsNullOrEmpty(body)) return list;
            Match codeMatch = ZhipuCodeRegex.Match(body);
            if (!codeMatch.Success) return list;
            string code = codeMatch.Groups[1].Value;
            QuotaWindow qw = new QuotaWindow();
            qw.DurationSeconds = code == "1316" ? FiveHourSeconds : WeekSeconds;
            qw.UsedPercent = 100;
            qw.Kind = ClassifyDurationSeconds(qw.DurationSeconds);
            Match dateMatch = ZhipuDateRegex.Match(body);
            if (dateMatch.Success)
            {
                DateTime dt;
                if (DateTime.TryParse(dateMatch.Value, CultureInfo.InvariantCulture, DateTimeStyles.None, out dt))
                {
                    long seconds = (long)(dt.ToUniversalTime() - EpochUtc).TotalSeconds;
                    if (seconds > 0 && seconds <= MaxEpochSeconds) qw.ResetAt = seconds;
                }
            }
            list.Add(qw);
            return list;
        }

        public static FetchResult FetchZhipu(string apiKey, string scheme)
        {
            return FetchZhipu(apiKey, scheme, CancellationToken.None);
        }

        public static FetchResult FetchZhipu(string apiKey, string scheme, CancellationToken cancellationToken)
        {
            return FetchZhipu(apiKey, scheme, cancellationToken, SendHttp);
        }

        internal static FetchResult FetchZhipu(string apiKey, string scheme, CancellationToken cancellationToken,
            HttpSend send)
        {
            FetchResult result = new FetchResult();
            try
            {
                cancellationToken.ThrowIfCancellationRequested();
                if (string.IsNullOrEmpty(apiKey)) { result.Error = "未配置 API Key"; return result; }
                var headers = new Dictionary<string, string>();
                headers["Authorization"] = scheme == "bearer" ? "Bearer " + apiKey : apiKey;
                HttpReply response = send("GET", ZhipuQuotaUrl, headers, null, cancellationToken);
                cancellationToken.ThrowIfCancellationRequested();
                string body = response.Body;
                int status = response.StatusCode;
                result.StatusCode = status;
                result.RetryAfterUtc = response.RetryAfterUtc;
                if (status == 200)
                {
                    List<QuotaWindow> windows = ParseZhipuUsage(body);
                    if (windows.Count == 0) { result.Error = "智谱未返回可识别额度窗口"; return result; }
                    result.Ok = true;
                    result.Windows = windows;
                    return result;
                }
                if (status == 429)
                {
                    List<QuotaWindow> windows = ParseZhipu429(body);
                    if (windows.Count > 0)
                    {
                        result.Ok = true; // 额度耗尽也是有效数据（100% + 重置时间）
                        result.Stale = true; // 429 推算的数据按“过期”标记，与参考实现一致
                        result.Warning = "接口限流，额度根据错误信息推算";
                        result.Windows = windows;
                        return result;
                    }
                }
                result.Error = RequestError("智谱", response);
            }
            catch (OperationCanceledException) { result.Canceled = true; }
            catch { result.Error = "智谱查询失败，请稍后重试"; }
            return result;
        }

        // ---------- DeepSeek 余额 ----------

        public static BalanceData ParseDeepSeekBalance(string json)
        {
            List<BalanceData> balances = ParseDeepSeekBalances(json);
            return balances.Count == 0 ? null : balances[0];
        }

        public static List<BalanceData> ParseDeepSeekBalances(string json)
        {
            string warning;
            return ParseDeepSeekBalances(json, out warning);
        }

        public static List<BalanceData> ParseDeepSeekBalances(string json, out string warning)
        {
            warning = null;
            List<BalanceData> balances = new List<BalanceData>();
            Dictionary<string, object> root = ParseJsonObject(json);
            if (root == null) return balances;
            object availObj = GetItem(root, "is_available");
            bool available = !(availObj is bool) || (bool)availObj;
            object[] infos = AsArray(GetItem(root, "balance_infos"));
            if (infos == null) return balances;
            foreach (object info in infos)
            {
                Dictionary<string, object> item = AsDict(info);
                if (item == null) { warning = "部分余额数据无效，已忽略异常字段"; continue; }
                decimal? total = ToDecimal(GetItem(item, "total_balance"));
                string currency = AsStr(GetItem(item, "currency"));
                if (total == null || string.IsNullOrWhiteSpace(currency))
                {
                    warning = "部分余额数据无效，已忽略异常字段";
                    continue;
                }
                BalanceData b = new BalanceData();
                b.Currency = currency.Trim();
                b.Total = total.Value;
                object granted = GetItem(item, "granted_balance");
                b.Granted = ToDecimal(granted);
                if (granted != null && b.Granted == null) warning = "部分余额数据无效，已忽略异常字段";
                b.Available = available;
                balances.Add(b);
            }
            return balances;
        }

        public static FetchResult FetchDeepSeek(string apiKey)
        {
            return FetchDeepSeek(apiKey, CancellationToken.None);
        }

        public static FetchResult FetchDeepSeek(string apiKey, CancellationToken cancellationToken)
        {
            return FetchDeepSeek(apiKey, cancellationToken, SendHttp);
        }

        internal static FetchResult FetchDeepSeek(string apiKey, CancellationToken cancellationToken, HttpSend send)
        {
            FetchResult result = new FetchResult();
            try
            {
                cancellationToken.ThrowIfCancellationRequested();
                if (string.IsNullOrEmpty(apiKey)) { result.Error = "未配置 API Key"; return result; }
                var headers = new Dictionary<string, string>();
                headers["Authorization"] = "Bearer " + apiKey;
                HttpReply response = send("GET", DeepSeekBalanceUrl, headers, null, cancellationToken);
                cancellationToken.ThrowIfCancellationRequested();
                int status = response.StatusCode;
                result.StatusCode = status;
                result.RetryAfterUtc = response.RetryAfterUtc;
                if (status == 200)
                {
                    string warning;
                    List<BalanceData> balances = ParseDeepSeekBalances(response.Body, out warning);
                    if (balances.Count == 0) { result.Error = "DeepSeek 未返回可识别余额"; return result; }
                    result.Warning = warning;
                    result.Ok = true;
                    result.Balance = balances[0];
                    result.Balances = balances;
                    return result;
                }
                result.Error = RequestError("DeepSeek", response);
            }
            catch (OperationCanceledException) { result.Canceled = true; }
            catch { result.Error = "DeepSeek 查询失败，请稍后重试"; }
            return result;
        }

        // ---------- HTTP ----------

        private static string RequestError(string provider, HttpReply response)
        {
            if (response.StatusCode == 0) return provider + (response.TimedOut ? "请求超时，请稍后重试" : "网络连接失败");
            if (response.StatusCode == 401) return provider + "凭据无效，请检查账号设置";
            if (response.StatusCode == 403) return provider + "拒绝访问，请检查账号权限";
            if (response.StatusCode == 429) return provider + "请求受限，请等待冷却结束";
            return provider + " HTTP " + response.StatusCode;
        }

        public static int HttpRequest(string method, string url, Dictionary<string, string> headers, string body,
            out string responseText)
        {
            return HttpRequest(method, url, headers, body, CancellationToken.None, out responseText);
        }

        public static int HttpRequest(string method, string url, Dictionary<string, string> headers, string body,
            CancellationToken cancellationToken, out string responseText)
        {
            HttpReply reply = SendHttp(method, url, headers, body, cancellationToken);
            responseText = reply.Body;
            return reply.StatusCode;
        }

        internal static DateTime? ParseRetryAfter(string value, DateTime utcNow)
        {
            if (string.IsNullOrWhiteSpace(value)) return null;
            long seconds;
            if (long.TryParse(value, NumberStyles.None, CultureInfo.InvariantCulture, out seconds))
            {
                if (seconds < 0 || seconds > (DateTime.MaxValue - utcNow).TotalSeconds) return null;
                try { return utcNow.AddSeconds(seconds); }
                catch (ArgumentOutOfRangeException) { return null; }
            }
            DateTime date;
            if (DateTime.TryParseExact(value, "r", CultureInfo.InvariantCulture,
                DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal, out date) && date > utcNow)
                return date;
            return null;
        }

        private static HttpReply ReadResponse(HttpWebResponse response, CancellationToken cancellationToken)
        {
            using (response)
            using (StreamReader reader = new StreamReader(response.GetResponseStream(), Encoding.UTF8))
            {
                HttpReply reply = new HttpReply { StatusCode = (int)response.StatusCode,
                    RetryAfterUtc = ParseRetryAfter(response.Headers["Retry-After"], DateTime.UtcNow) };
                reply.Body = reader.ReadToEnd();
                cancellationToken.ThrowIfCancellationRequested();
                return reply;
            }
        }

        internal static HttpReply SendHttp(string method, string url, Dictionary<string, string> headers, string body,
            CancellationToken cancellationToken)
        {
            cancellationToken.ThrowIfCancellationRequested();
            try
            {
                ServicePointManager.SecurityProtocol |= (SecurityProtocolType)3072;
                HttpWebRequest req = (HttpWebRequest)WebRequest.Create(url);
                req.Method = method;
                req.Timeout = 10000;
                req.ReadWriteTimeout = 10000;
                req.UserAgent = "ai-quota-widget/1.0";
                req.Accept = "application/json";
                if (headers != null)
                    foreach (KeyValuePair<string, string> kv in headers)
                        if (!string.IsNullOrEmpty(kv.Value)) req.Headers[kv.Key] = kv.Value;
                using (cancellationToken.Register(delegate { req.Abort(); }))
                {
                    cancellationToken.ThrowIfCancellationRequested();
                    try
                    {
                        if (body != null)
                        {
                            byte[] data = Encoding.UTF8.GetBytes(body);
                            req.ContentType = "application/json";
                            req.ContentLength = data.Length;
                            using (Stream stream = req.GetRequestStream()) stream.Write(data, 0, data.Length);
                        }
                        return ReadResponse((HttpWebResponse)req.GetResponse(), cancellationToken);
                    }
                    catch (WebException error)
                    {
                        // Abort reports a WebException: cancellation must not become a network failure.
                        if (cancellationToken.IsCancellationRequested)
                        {
                            if (error.Response != null) error.Response.Close();
                            cancellationToken.ThrowIfCancellationRequested();
                        }
                        HttpWebResponse response = error.Response as HttpWebResponse;
                        if (response != null) return ReadResponse(response, cancellationToken);
                        return new HttpReply { TimedOut = error.Status == WebExceptionStatus.Timeout };
                    }
                }
            }
            catch (OperationCanceledException) { throw; }
            catch
            {
                cancellationToken.ThrowIfCancellationRequested();
                return new HttpReply();
            }
        }
    }
}
