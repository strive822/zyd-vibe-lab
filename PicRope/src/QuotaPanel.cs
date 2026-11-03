using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Input;
using System.Windows.Threading;
using System.Web.Script.Serialization;

namespace ScreenLine
{
    internal sealed class QuotaRow
    {
        public string Title = "";
        public double? Usage;
        public string Line1 = "";
        public string Line2 = "";
        public string Error = "";
    }

    internal static class QuotaConfigFile
    {
        internal const string Template =
            "{\n" +
            "  \"_说明\": \"额度面板配置：填好 API Key 保存即可，程序每轮刷新都会重新读取；enabled 设为 false 可隐藏对应行\",\n" +
            "  \"refreshMinutes\": 5,\n" +
            "  \"codex\": { \"enabled\": true, \"_说明\": \"无需填 Key：自动读取本机 ~/.codex/auth.json 的登录凭证查询 5 小时与每周额度\" },\n" +
            "  \"zhipu\": { \"enabled\": true, \"apiKey\": \"\", \"_说明\": \"智谱开放平台（bigmodel.cn）的 API Key，用于查询 Coding Plan 的 5 小时与每周用量\" },\n" +
            "  \"deepseek\": { \"enabled\": true, \"apiKey\": \"\", \"_说明\": \"DeepSeek 开放平台的 API Key，用于查询账户余额\" },\n" +
            "  \"workbuddy\": { \"enabled\": true, \"_说明\": \"WorkBuddy 暂无公开查询接口，面板里提供打开应用查看积分的入口\" }\n" +
            "}";

        internal static string PathFor(StateStore store) { return Path.Combine(store.Root, "quotas.json"); }

        internal static Dictionary<string, object> Load(StateStore store)
        {
            string path = PathFor(store);
            try
            {
                if (!File.Exists(path)) File.WriteAllText(path, Template, Encoding.UTF8);
                var serializer = new JavaScriptSerializer();
                var loaded = serializer.Deserialize<Dictionary<string, object>>(File.ReadAllText(path));
                return loaded ?? new Dictionary<string, object>();
            }
            catch (Exception error) { store.Log(error); return new Dictionary<string, object>(); }
        }

        internal static Dictionary<string, object> Section(Dictionary<string, object> config, string name)
        {
            object value;
            return config.TryGetValue(name, out value) ? value as Dictionary<string, object> : null;
        }

        internal static bool Enabled(Dictionary<string, object> section, bool fallback)
        {
            if (section == null) return fallback;
            object value;
            if (!section.TryGetValue("enabled", out value)) return fallback;
            return value is bool ? (bool)value : fallback;
        }

        internal static string Text(Dictionary<string, object> section, string key)
        {
            if (section == null) return "";
            object value;
            return section.TryGetValue(key, out value) ? value as string : null;
        }

        internal static int Minutes(Dictionary<string, object> config)
        {
            object value;
            if (config.TryGetValue("refreshMinutes", out value) && value is int && (int)value >= 1 && (int)value <= 1440) return (int)value;
            return 5;
        }
    }

    internal static class QuotaService
    {
        static readonly HttpClient client = CreateClient();

        static HttpClient CreateClient()
        {
            // .NET Framework 默认协议可能不含 TLS 1.2，显式开启三家接口都需要的版本。
            try
            {
                System.Net.ServicePointManager.SecurityProtocol |= System.Net.SecurityProtocolType.Tls12;
                System.Net.ServicePointManager.Expect100Continue = false;
            }
            catch { }
            var client = new HttpClient();
            client.Timeout = TimeSpan.FromSeconds(15);
            try { client.DefaultRequestHeaders.Accept.ParseAdd("application/json"); } catch { }
            return client;
        }

        static string CodexToken()
        {
            string path = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".codex", "auth.json");
            if (!File.Exists(path)) return null;
            try
            {
                var serializer = new JavaScriptSerializer();
                var auth = serializer.Deserialize<Dictionary<string, object>>(File.ReadAllText(path));
                if (auth == null) return null;
                object token;
                if (auth.TryGetValue("access_token", out token) && token is string) return (string)token;
                object tokens;
                if (auth.TryGetValue("tokens", out tokens) && tokens is Dictionary<string, object>)
                {
                    object inner;
                    if (((Dictionary<string, object>)tokens).TryGetValue("access_token", out inner) && inner is string) return (string)inner;
                }
            }
            catch { }
            return null;
        }

        static string StringAt(Dictionary<string, object> data, string key)
        {
            object value;
            return data != null && data.TryGetValue(key, out value) ? value as string : null;
        }

        static Dictionary<string, object> DictAt(Dictionary<string, object> data, string key)
        {
            object value;
            return data != null && data.TryGetValue(key, out value) ? value as Dictionary<string, object> : null;
        }

        static double? DoubleAt(Dictionary<string, object> data, string key)
        {
            object value;
            if (data == null || !data.TryGetValue(key, out value)) return null;
            if (value is int) return (int)value;
            if (value is double) return (double)value;
            if (value is long) return (long)value;
            return null;
        }

        static string ResetText(double? seconds)
        {
            if (!seconds.HasValue || seconds.Value <= 0) return "";
            var span = TimeSpan.FromSeconds(seconds.Value);
            if (span.TotalDays >= 1) return string.Format("{0}天{1}小时后重置", (int)span.TotalDays, span.Hours);
            if (span.TotalHours >= 1) return string.Format("{0}小时{1}分后重置", span.Hours, span.Minutes);
            return string.Format("{0}分后重置", Math.Max(1, span.Minutes));
        }

        static async Task<string> SendAsync(HttpRequestMessage request)
        {
            using (var response = await client.SendAsync(request).ConfigureAwait(false))
            {
                string body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                if (!response.IsSuccessStatusCode) throw new InvalidOperationException("HTTP " + (int)response.StatusCode);
                return body;
            }
        }

        internal static async Task<QuotaRow> FetchCodex()
        {
            var row = new QuotaRow { Title = "Codex（ChatGPT 订阅）" };
            string token = CodexToken();
            if (string.IsNullOrEmpty(token)) { row.Error = "未找到本机 ~/.codex/auth.json 的登录凭证，请先登录 Codex。"; return row; }
            try
            {
                using (var request = new HttpRequestMessage(HttpMethod.Get, "https://chatgpt.com/backend-api/wham/usage"))
                {
                    request.Headers.TryAddWithoutValidation("Authorization", "Bearer " + token);
                    string body = await SendAsync(request);
                    var serializer = new JavaScriptSerializer();
                    var data = serializer.Deserialize<Dictionary<string, object>>(body);
                    var rateLimit = DictAt(data, "rate_limit");
                    var primary = DictAt(rateLimit, "primary_window");
                    var secondary = DictAt(rateLimit, "secondary_window");
                    double? primaryUsed = DoubleAt(primary, "used_percent");
                    double? weeklyUsed = DoubleAt(secondary, "used_percent");
                    if (!primaryUsed.HasValue && !weeklyUsed.HasValue) { row.Error = "接口未返回额度窗口，请稍后重试。"; return row; }
                    row.Usage = primaryUsed ?? weeklyUsed;
                    string reset1 = DoubleAt(primary, "reset_after_seconds").HasValue ? ResetText(DoubleAt(primary, "reset_after_seconds")) : "";
                    string reset2 = DoubleAt(secondary, "reset_after_seconds").HasValue ? ResetText(DoubleAt(secondary, "reset_after_seconds")) : "";
                    row.Line1 = (primaryUsed.HasValue ? string.Format("5 小时窗口已用 {0:0}%", primaryUsed.Value) + (reset1 == "" ? "" : "（" + reset1 + "）") : "5 小时窗口：无数据");
                    row.Line2 = (weeklyUsed.HasValue ? string.Format("本周额度已用 {0:0}%", weeklyUsed.Value) + (reset2 == "" ? "" : "（" + reset2 + "）") : "本周额度：无数据");
                }
            }
            catch (Exception error) { row.Error = "查询失败：" + error.Message; }
            return row;
        }

        internal static async Task<QuotaRow> FetchZhipu(string apiKey)
        {
            var row = new QuotaRow { Title = "智谱 GLM Coding Plan" };
            if (string.IsNullOrWhiteSpace(apiKey)) { row.Error = "尚未填写智谱 API Key，请编辑 data\\quotas.json。"; return row; }
            try
            {
                using (var request = new HttpRequestMessage(HttpMethod.Get, "https://open.bigmodel.cn/api/monitor/usage/quota/limit"))
                {
                    request.Headers.TryAddWithoutValidation("Authorization", apiKey);
                    string body = await SendAsync(request);
                    var serializer = new JavaScriptSerializer();
                    var data = serializer.Deserialize<Dictionary<string, object>>(body);
                    var payload = DictAt(data, "data");
                    object limitsObject;
                    object[] limits = null;
                    if (payload != null && payload.TryGetValue("limits", out limitsObject)) limits = limitsObject as object[];
                    if (limits == null || limits.Length == 0) { row.Error = "Key 无效或当前账号没有 Coding Plan 套餐。"; return row; }
                    var parts = new List<string>();
                    double worst = -1;
                    foreach (object entry in limits)
                    {
                        var limit = entry as Dictionary<string, object>;
                        if (limit == null) continue;
                        double? percentage = DoubleAt(limit, "percentage");
                        if (!percentage.HasValue) continue;
                        string type = StringAt(limit, "type");
                        string label = type == "TIME_LIMIT" ? "5 小时窗口" : string.IsNullOrEmpty(type) ? "额度" : type;
                        string reset = ResetText(DoubleAt(limit, "reset_after_seconds"));
                        parts.Add(string.Format("{0} 已用 {1:0}%{2}", label, percentage.Value, reset == "" ? "" : "（" + reset + "）"));
                        if (percentage.Value > worst) worst = percentage.Value;
                    }
                    if (parts.Count == 0) { row.Error = "接口未返回用量数据。"; return row; }
                    row.Usage = worst >= 0 ? worst : (double?)null;
                    row.Line1 = parts[0];
                    row.Line2 = parts.Count > 1 ? string.Join("　", parts.ToArray(), 1, parts.Count - 1) : "";
                }
            }
            catch (Exception error) { row.Error = "查询失败：" + error.Message; }
            return row;
        }

        internal static async Task<QuotaRow> FetchDeepSeek(string apiKey)
        {
            var row = new QuotaRow { Title = "DeepSeek 余额" };
            if (string.IsNullOrWhiteSpace(apiKey)) { row.Error = "尚未填写 DeepSeek API Key，请编辑 data\\quotas.json。"; return row; }
            try
            {
                using (var request = new HttpRequestMessage(HttpMethod.Get, "https://api.deepseek.com/user/balance"))
                {
                    request.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);
                    string body = await SendAsync(request);
                    var serializer = new JavaScriptSerializer();
                    var data = serializer.Deserialize<Dictionary<string, object>>(body);
                    object infosObject;
                    object[] infos = data != null && data.TryGetValue("balance_infos", out infosObject) ? infosObject as object[] : null;
                    if (infos == null || infos.Length == 0) { row.Error = "接口未返回余额信息。"; return row; }
                    var parts = new List<string>();
                    foreach (object entry in infos)
                    {
                        var info = entry as Dictionary<string, object>;
                        if (info == null) continue;
                        string currency = StringAt(info, "currency") ?? "";
                        string total = StringAt(info, "total_balance") ?? "?";
                        string granted = StringAt(info, "granted_balance") ?? "";
                        string symbol = currency == "CNY" ? "¥" : currency == "USD" ? "$" : "";
                        parts.Add(symbol + total + (currency == "" ? "" : " " + currency) + (granted != "" && granted != "0.00" ? "（含赠金 " + symbol + granted + "）" : ""));
                    }
                    row.Line1 = parts.Count > 0 ? "可用余额 " + parts[0] : "无余额数据";
                    row.Line2 = parts.Count > 1 ? string.Join("　", parts.ToArray(), 1, parts.Count - 1) : "查询自 api.deepseek.com/user/balance";
                }
            }
            catch (Exception error) { row.Error = "查询失败：" + error.Message; }
            return row;
        }
    }

    internal sealed class QuotaPanelWindow : Window
    {
        readonly StateStore store;
        readonly StackPanel rows = new StackPanel();
        readonly Dictionary<string, StackPanel> providers = new Dictionary<string, StackPanel>();
        readonly Dictionary<string, TextBlock> valueLines = new Dictionary<string, TextBlock>();
        readonly Dictionary<string, TextBlock> detailLines = new Dictionary<string, TextBlock>();
        readonly Dictionary<string, TextBlock> usageTags = new Dictionary<string, TextBlock>();
        readonly TextBlock status = new TextBlock { FontSize = 11, Foreground = LightTheme.Brush("#65717F") };
        readonly DispatcherTimer timer = new DispatcherTimer();
        readonly Button refresh;
        bool busy;

        internal QuotaPanelWindow(StateStore source)
        {
            store = source;
            Title = "模型额度 · 图绳"; Width = 400; SizeToContent = SizeToContent.Height; ResizeMode = ResizeMode.NoResize;
            WindowStartupLocation = WindowStartupLocation.Manual; ShowInTaskbar = false;
            Topmost = true; ShowActivated = false;
            FontFamily = new FontFamily("Microsoft YaHei UI");
            var body = new StackPanel { Margin = new Thickness(16) };
            BuildRow("codex", "Codex（ChatGPT 订阅）");
            BuildRow("zhipu", "智谱 GLM Coding Plan");
            BuildRow("deepseek", "DeepSeek 余额");
            BuildRow("workbuddy", "WorkBuddy 积分");
            body.Children.Add(rows);
            var footer = new DockPanel { Margin = new Thickness(0, 10, 0, 0), LastChildFill = false };
            refresh = LightTheme.Button("刷新", delegate { RefreshNow(); }, "primary");
            DockPanel.SetDock(refresh, Dock.Left); footer.Children.Add(refresh);
            var config = LightTheme.Button("配置…", delegate { OpenConfig(); }, "quiet");
            DockPanel.SetDock(config, Dock.Left); footer.Children.Add(config);
            status.VerticalAlignment = VerticalAlignment.Center;
            footer.Children.Add(status);
            body.Children.Add(footer);
            Content = body;
            timer.Tick += delegate { RefreshNow(); };
            Loaded += delegate { RestartTimer(); RefreshNow(); };
            Closed += delegate { timer.Stop(); };
        }

        // 托盘菜单手动打开：不依赖绳子是否展开。
        internal void ShowStandalone()
        {
            if (!IsVisible) Show();
            PositionNearRope();
            RefreshNow();
        }

        void BuildRow(string id, string name)
        {
            var value = new TextBlock { FontSize = 13, TextWrapping = TextWrapping.Wrap, Foreground = new SolidColorBrush(Color.FromRgb(40, 48, 58)) };
            var detail = new TextBlock { FontSize = 11.5, TextWrapping = TextWrapping.Wrap, Foreground = LightTheme.Brush("#65717F"), Margin = new Thickness(0, 3, 0, 0) };
            var tag = new TextBlock { FontSize = 12, FontWeight = FontWeights.SemiBold, HorizontalAlignment = HorizontalAlignment.Right };
            var line = new DockPanel { LastChildFill = true };
            var nameText = new TextBlock { Text = name, FontSize = 13, FontWeight = FontWeights.SemiBold, Foreground = Brushes.Black };
            line.Children.Add(tag); DockPanel.SetDock(tag, Dock.Right);
            line.Children.Add(nameText);
            var stack = new StackPanel { Margin = new Thickness(0, 6, 0, 6) };
            stack.Children.Add(line); stack.Children.Add(value); stack.Children.Add(detail);
            rows.Children.Add(stack);
            providers[id] = stack; valueLines[id] = value; detailLines[id] = detail; usageTags[id] = tag;
        }

        void SetRow(string id, QuotaRow row)
        {
            var value = valueLines[id]; var detail = detailLines[id]; var tag = usageTags[id];
            if (row == null) return;
            if (!string.IsNullOrEmpty(row.Error))
            {
                value.Text = row.Error;
                value.Foreground = new SolidColorBrush(Color.FromRgb(183, 78, 74));
                detail.Text = ""; tag.Text = "";
                return;
            }
            value.Text = row.Line1;
            value.Foreground = new SolidColorBrush(Color.FromRgb(40, 48, 58));
            detail.Text = row.Line2;
            if (row.Usage.HasValue)
            {
                double used = row.Usage.Value;
                tag.Text = string.Format("{0:0}%", used);
                tag.Foreground = new SolidColorBrush(used >= 80 ? Color.FromRgb(198, 40, 40) : used >= 50 ? Color.FromRgb(178, 106, 0) : Color.FromRgb(46, 125, 50));
            }
            else tag.Text = "";
        }

        internal void RefreshNow()
        {
            if (busy) return;
            busy = true; refresh.IsEnabled = false;
            var config = QuotaConfigFile.Load(store);
            timer.Stop();
            timer.Interval = TimeSpan.FromMinutes(QuotaConfigFile.Minutes(config));
            var codexSection = QuotaConfigFile.Section(config, "codex");
            var zhipuSection = QuotaConfigFile.Section(config, "zhipu");
            var deepseekSection = QuotaConfigFile.Section(config, "deepseek");
            var workbuddySection = QuotaConfigFile.Section(config, "workbuddy");
            status.Text = "查询中…";
            RunRow("codex", QuotaConfigFile.Enabled(codexSection, true), delegate { return QuotaService.FetchCodex(); });
            RunRow("zhipu", QuotaConfigFile.Enabled(zhipuSection, true), delegate { return QuotaService.FetchZhipu(QuotaConfigFile.Text(zhipuSection, "apiKey")); });
            RunRow("deepseek", QuotaConfigFile.Enabled(deepseekSection, true), delegate { return QuotaService.FetchDeepSeek(QuotaConfigFile.Text(deepseekSection, "apiKey")); });
            var workbuddyValue = valueLines["workbuddy"]; var workbuddyDetail = detailLines["workbuddy"]; var workbuddyTag = usageTags["workbuddy"];
            if (QuotaConfigFile.Enabled(workbuddySection, true))
            {
                workbuddyValue.Text = "暂无公开查询接口，请在 WorkBuddy 应用内查看积分。";
                workbuddyValue.Foreground = new SolidColorBrush(Color.FromRgb(40, 48, 58));
                workbuddyDetail.Text = "已记录原因：WorkBuddy 未提供查询接口，积分仅在其应用内可见。";
                workbuddyTag.Text = "";
            }
            else { workbuddyValue.Text = "已隐藏（quotas.json 中 enabled=false）"; workbuddyDetail.Text = ""; workbuddyTag.Text = ""; }
        }

        void RunRow(string id, bool enabled, Func<Task<QuotaRow>> fetch)
        {
            var value = valueLines[id]; var detail = detailLines[id]; var tag = usageTags[id];
            if (!enabled)
            {
                value.Text = "已隐藏（quotas.json 中 enabled=false）";
                value.Foreground = LightTheme.Brush("#65717F");
                detail.Text = ""; tag.Text = "";
                return;
            }
            value.Text = "查询中…"; value.Foreground = LightTheme.Brush("#65717F"); detail.Text = ""; tag.Text = "";
            int token = Environment.TickCount;
            fetch().ContinueWith(delegate(Task<QuotaRow> task)
            {
                Dispatcher.BeginInvoke(new Action(delegate
                {
                    if (!IsLoaded) return;
                    SetRow(id, task.Status == TaskStatus.RanToCompletion ? task.Result : new QuotaRow { Error = "查询失败：" + task.Exception.GetBaseException().Message });
                    bool anyBusy = false;
                    foreach (var line in valueLines.Values) if (line.Text == "查询中…") anyBusy = true;
                    if (!anyBusy) { busy = false; refresh.IsEnabled = true; status.Text = "最后更新 " + DateTime.Now.ToString("HH:mm:ss") + " · 每 " + (int)timer.Interval.TotalMinutes + " 分钟自动刷新"; timer.Start(); }
                }));
            });
        }

        void RestartTimer() { }

        // 跟随绳子：展开时贴在屏幕右侧、绳子下沿浮出，收起时一起隐藏。
        internal void Follow(bool shelfShown)
        {
            if (shelfShown)
            {
                if (!IsVisible) Show();
                PositionNearRope();
                RefreshNow();
            }
            else if (IsVisible) Hide();
        }

        void PositionNearRope()
        {
            try
            {
                var screen = System.Windows.Forms.Screen.PrimaryScreen;
                double scale = WindowsNative.MonitorScale(screen);
                double left = screen.Bounds.Left / scale;
                double right = screen.Bounds.Right / scale;
                double top = screen.Bounds.Top / scale;
                double bottom = screen.Bounds.Bottom / scale;
                double width = ActualWidth > 0 ? ActualWidth : Width;
                double height = ActualHeight > 0 ? ActualHeight : 360;
                Left = Math.Max(left + 8, right - width - 24);
                Top = Math.Min(top + 228, Math.Max(top + 8, bottom - height - 56));
            }
            catch { }
        }

        void OpenConfig()
        {
            try
            {
                string path = QuotaConfigFile.PathFor(store);
                if (!File.Exists(path)) File.WriteAllText(path, QuotaConfigFile.Template, Encoding.UTF8);
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(store.Root) { UseShellExecute = true });
            }
            catch { }
        }

        protected override void OnMouseDoubleClick(MouseButtonEventArgs e)
        {
            var source = e.OriginalSource as TextBlock;
            if (source != null && source.Text.Contains("WorkBuddy"))
            {
                try
                {
                    var start = new System.Diagnostics.ProcessStartInfo("https://www.workbuddy.cn") { UseShellExecute = true };
                    System.Diagnostics.Process.Start(start);
                }
                catch { }
            }
            base.OnMouseDoubleClick(e);
        }
    }
}
