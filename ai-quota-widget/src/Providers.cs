using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Net;
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
        public string Error;
        public string Warning;
        public bool Stale;
        public List<QuotaWindow> Windows = new List<QuotaWindow>();
        public BalanceData Balance;
    }

    public class CodexAuth
    {
        public string AccessToken;
        public string RefreshToken;
        public string AccountId;
        public string IdToken;
        public string RawJson;
    }

    public static class Providers
    {
        public const string CodexClientId = "app_EMoamEEZ73f0CkXaXp7hrann";
        public const string CodexUsageUrl = "https://chatgpt.com/backend-api/wham/usage";
        public const string ZhipuQuotaUrl = "https://open.bigmodel.cn/api/monitor/usage/quota/limit";
        public const string DeepSeekBalanceUrl = "https://api.deepseek.com/user/balance";
        public const string OpenAiTokenUrl = "https://auth.openai.com/oauth/token";
        public const int FiveHourSeconds = 18000;
        public const int WeekSeconds = 604800;

        static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = int.MaxValue };
        static readonly Regex ZhipuCodeRegex = new Regex("\"code\"\\s*:\\s*\"?(1310|1316|1317)\"?", RegexOptions.Compiled);
        static readonly Regex ZhipuDateRegex = new Regex("\\d{4}-\\d{2}-\\d{2}[ T]\\d{2}:\\d{2}:\\d{2}", RegexOptions.Compiled);

        static readonly DateTime EpochUtc = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);

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
            if (value is int || value is long || value is double || value is decimal || value is float || value is short || value is byte)
                return Convert.ToDouble(value, CultureInfo.InvariantCulture);
            string s = value as string;
            if (s != null)
            {
                s = s.Trim();
                if (s.Length == 0) return null;
                double d;
                if (double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out d)) return d;
                return null;
            }
            return null;
        }

        public static long? EpochSeconds(object value)
        {
            double? n = ToDouble(value);
            if (n == null || n.Value <= 0) return null;
            long v = (long)Math.Floor(n.Value);
            if (v > 10000000000L) v /= 1000; // 毫秒 → 秒
            return v;
        }

        public static WindowKind ClassifyDurationSeconds(int seconds)
        {
            if (Math.Abs(seconds - FiveHourSeconds) < 60) return WindowKind.FiveHour;
            if (Math.Abs(seconds - WeekSeconds) < 60) return WindowKind.Week;
            return WindowKind.Other;
        }

        public static string FormatCountdown(long? resetAt)
        {
            if (resetAt == null) return null;
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
            try { return AsDict(Json.DeserializeObject(json)); }
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
            if (duration == null || duration.Value <= 0 || used < 0) return;
            QuotaWindow qw = new QuotaWindow();
            qw.DurationSeconds = (int)Math.Floor(duration.Value);
            qw.UsedPercent = used;
            qw.Kind = ClassifyDurationSeconds(qw.DurationSeconds);
            long? resetAt = EpochSeconds(GetItem(w, "reset_at"));
            if (resetAt == null)
            {
                double? after = ToDouble(GetItem(w, "reset_after_seconds"));
                if (after != null) resetAt = NowUnixSeconds() + (long)Math.Max(0, Math.Floor(after.Value));
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
            auth.RefreshToken = AsStr(GetItem(tokens, "refresh_token"));
            auth.AccountId = AsStr(GetItem(tokens, "account_id"));
            auth.IdToken = AsStr(GetItem(tokens, "id_token"));
            auth.RawJson = json;
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
            string path = ResolveCodexAuthPath(authJsonPath);
            for (int i = 0; i < 3; i++)
            {
                try
                {
                    if (!File.Exists(path)) return null;
                    string json = File.ReadAllText(path, Encoding.UTF8);
                    CodexAuth auth = ParseCodexAuth(json);
                    if (auth == null || string.IsNullOrEmpty(auth.AccessToken)) return auth;
                    return auth;
                }
                catch (IOException)
                {
                    Thread.Sleep(120); // Codex 桌面端可能正在重写该文件，稍后重试
                }
                catch { return null; }
            }
            return null;
        }

        public static string RefreshCodexToken(CodexAuth auth, string authJsonPath, out bool persistedToDisk)
        {
            persistedToDisk = false;
            try
            {
                if (auth == null || string.IsNullOrEmpty(auth.RefreshToken)) return null;
                string reqBody = Json.Serialize(new Dictionary<string, object>
                {
                    { "client_id", CodexClientId },
                    { "grant_type", "refresh_token" },
                    { "refresh_token", auth.RefreshToken }
                });
                int status;
                string respText;
                int st = HttpRequest("POST", OpenAiTokenUrl, new Dictionary<string, string>(), reqBody, out respText);
                status = st;
                if (status != 200) return null;
                Dictionary<string, object> root = ParseJsonObject(respText);
                if (root == null) return null;
                string newAccess = AsStr(GetItem(root, "access_token"));
                if (string.IsNullOrEmpty(newAccess)) return null;
                string newRefresh = AsStr(GetItem(root, "refresh_token"));

                // 备份并回写 auth.json（保留其他字段；任何失败都不破坏原文件）
                Dictionary<string, object> doc = ParseJsonObject(auth.RawJson);
                if (doc != null)
                {
                    Dictionary<string, object> tokens = AsDict(GetItem(doc, "tokens"));
                    if (tokens != null)
                    {
                        tokens["access_token"] = newAccess;
                        if (!string.IsNullOrEmpty(newRefresh)) tokens["refresh_token"] = newRefresh;
                        try
                        {
                            string path = ResolveCodexAuthPath(authJsonPath);
                            string dir = Path.GetDirectoryName(path);
                            if (!string.IsNullOrEmpty(dir) && Directory.Exists(dir))
                            {
                                // 原子替换：写临时文件后 File.Replace，避免半截文件损坏登录态
                                string tmp = path + ".tmp";
                                string bak = path + ".bak";
                                string newJson = Json.Serialize(doc);
                                File.WriteAllText(tmp, newJson, Encoding.UTF8);
                                if (File.Exists(path))
                                {
                                    try { if (File.Exists(bak)) File.Delete(bak); }
                                    catch { }
                                    File.Replace(tmp, path, bak, false);
                                }
                                else File.Move(tmp, path);
                                persistedToDisk = true;
                            }
                        }
                        catch { }
                    }
                }
                return newAccess;
            }
            catch { return null; }
        }

        public static FetchResult FetchCodex(string authJsonPath)
        {
            FetchResult result = new FetchResult();
            try
            {
                CodexAuth auth = ReadCodexAuth(authJsonPath);
                if (auth == null) { result.Error = "无法读取 ~/.codex/auth.json（未登录 Codex？）"; return result; }
                if (string.IsNullOrEmpty(auth.AccessToken)) { result.Error = "auth.json 中没有 access_token"; return result; }
                for (int attempt = 0; attempt < 2; attempt++)
                {
                    var headers = new Dictionary<string, string>();
                    headers["Authorization"] = "Bearer " + auth.AccessToken;
                    if (!string.IsNullOrEmpty(auth.AccountId)) headers["chatgpt-account-id"] = auth.AccountId;
                    headers["originator"] = "codex-usage-widget";
                    string body;
                    int status = HttpRequest("GET", CodexUsageUrl, headers, null, out body);
                    if (status == 200)
                    {
                        List<QuotaWindow> windows = ParseOpenAIUsage(body);
                        if (windows.Count == 0) { result.Error = "Codex 未返回可识别额度窗口"; return result; }
                        result.Ok = true;
                        result.Windows = windows;
                        return result;
                    }
                    if ((status == 401 || status == 403) && attempt == 0)
                    {
                        bool persisted;
                        string newToken = RefreshCodexToken(auth, authJsonPath, out persisted);
                        if (!string.IsNullOrEmpty(newToken))
                        {
                            auth.AccessToken = newToken;
                            if (!persisted)
                                result.Warning = "新 token 已取得但写回 auth.json 失败，重启后可能需重新登录";
                            continue;
                        }
                        result.Error = "Codex 凭据过期且刷新失败，请重新登录 Codex";
                        return result;
                    }
                    result.Error = "Codex usage HTTP " + status + (string.IsNullOrEmpty(body) ? "" : (": " + Truncate(body, 120)));
                    return result;
                }
            }
            catch (Exception ex) { result.Error = "Codex 异常: " + ex.Message; }
            return result;
        }

        // ---------- 智谱 GLM Coding Plan ----------

        static int DurationFromZhipuUnit(int unit, int number)
        {
            if (unit == 3) return number * 3600;   // 小时
            if (unit == 6) return number * 604800; // 周
            if (unit == 2) return number * 86400;  // 天（尽力而为）
            return 0;
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
                if (unit == null || number == null || used < 0) continue;
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
                    qw.ResetAt = (long)(dt.ToUniversalTime() - EpochUtc).TotalSeconds;
            }
            list.Add(qw);
            return list;
        }

        public static FetchResult FetchZhipu(string apiKey, string scheme)
        {
            FetchResult result = new FetchResult();
            try
            {
                if (string.IsNullOrEmpty(apiKey)) { result.Error = "未配置 API Key"; return result; }
                var headers = new Dictionary<string, string>();
                headers["Authorization"] = scheme == "bearer" ? "Bearer " + apiKey : apiKey;
                string body;
                int status = HttpRequest("GET", ZhipuQuotaUrl, headers, null, out body);
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
                        result.Windows = windows;
                        return result;
                    }
                }
                result.Error = "智谱 HTTP " + status + (string.IsNullOrEmpty(body) ? "" : (": " + Truncate(body, 120)));
            }
            catch (Exception ex) { result.Error = "智谱异常: " + ex.Message; }
            return result;
        }

        // ---------- DeepSeek 余额 ----------

        public static BalanceData ParseDeepSeekBalance(string json)
        {
            Dictionary<string, object> root = ParseJsonObject(json);
            if (root == null) return null;
            object availObj = GetItem(root, "is_available");
            bool available = !(availObj is bool) || (bool)availObj;
            object[] infos = AsArray(GetItem(root, "balance_infos"));
            if (infos == null || infos.Length == 0) return null;
            Dictionary<string, object> first = AsDict(infos[0]);
            if (first == null) return null;
            double? total = ToDouble(GetItem(first, "total_balance"));
            string currency = AsStr(GetItem(first, "currency"));
            if (total == null && string.IsNullOrEmpty(currency)) return null;
            BalanceData b = new BalanceData();
            b.Currency = string.IsNullOrEmpty(currency) ? "CNY" : currency;
            b.Total = total == null ? 0m : (decimal)total.Value;
            double? granted = ToDouble(GetItem(first, "granted_balance"));
            b.Granted = granted == null ? (decimal?)null : Convert.ToDecimal(granted.Value);
            b.Available = available;
            return b;
        }

        public static FetchResult FetchDeepSeek(string apiKey)
        {
            FetchResult result = new FetchResult();
            try
            {
                if (string.IsNullOrEmpty(apiKey)) { result.Error = "未配置 API Key"; return result; }
                var headers = new Dictionary<string, string>();
                headers["Authorization"] = "Bearer " + apiKey;
                string body;
                int status = HttpRequest("GET", DeepSeekBalanceUrl, headers, null, out body);
                if (status == 200)
                {
                    BalanceData balance = ParseDeepSeekBalance(body);
                    if (balance == null) { result.Error = "DeepSeek 未返回可识别余额"; return result; }
                    result.Ok = true;
                    result.Balance = balance;
                    return result;
                }
                result.Error = "DeepSeek HTTP " + status + (string.IsNullOrEmpty(body) ? "" : (": " + Truncate(body, 120)));
            }
            catch (Exception ex) { result.Error = "DeepSeek 异常: " + ex.Message; }
            return result;
        }

        // ---------- HTTP ----------

        public static int HttpRequest(string method, string url, Dictionary<string, string> headers, string body, out string responseText)
        {
            responseText = null;
            try
            {
                ServicePointManager.SecurityProtocol |= (SecurityProtocolType)3072 | (SecurityProtocolType)768 | SecurityProtocolType.Tls;
                HttpWebRequest req = (HttpWebRequest)WebRequest.Create(url);
                req.Method = method;
                req.Timeout = 10000;
                req.ReadWriteTimeout = 10000;
                req.UserAgent = "ai-quota-widget/1.0";
                req.Accept = "application/json";
                if (headers != null)
                {
                    foreach (KeyValuePair<string, string> kv in headers)
                    {
                        if (!string.IsNullOrEmpty(kv.Value)) req.Headers[kv.Key] = kv.Value;
                    }
                }
                if (body != null)
                {
                    byte[] data = Encoding.UTF8.GetBytes(body);
                    req.ContentType = "application/json";
                    req.ContentLength = data.Length;
                    using (Stream s = req.GetRequestStream()) { s.Write(data, 0, data.Length); }
                }
                try
                {
                    using (HttpWebResponse resp = (HttpWebResponse)req.GetResponse())
                    using (StreamReader sr = new StreamReader(resp.GetResponseStream(), Encoding.UTF8))
                    {
                        responseText = sr.ReadToEnd();
                        return (int)resp.StatusCode;
                    }
                }
                catch (WebException ex)
                {
                    HttpWebResponse errResp = ex.Response as HttpWebResponse;
                    if (errResp != null)
                    {
                        using (StreamReader sr = new StreamReader(errResp.GetResponseStream(), Encoding.UTF8))
                        {
                            responseText = sr.ReadToEnd();
                        }
                        return (int)errResp.StatusCode;
                    }
                    return 0; // 网络不通 / 代理故障
                }
            }
            catch { return 0; }
        }
    }
}
