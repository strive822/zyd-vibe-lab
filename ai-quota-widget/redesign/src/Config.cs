using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;
using Microsoft.Win32;

namespace QuotaWidget
{
    public class CodexCfg
    {
        public bool Enabled = true;
        public bool Visible = true;
        public string Name = "OpenAI Codex";
        public string AuthJsonPath = "";
    }

    public class ZhipuCfg
    {
        public bool Visible = true;
        public string Name = "";
        public string ApiKey = "";
    }

    public class DeepSeekCfg
    {
        public bool Enabled = false;
        public bool Visible = true;
        public string Name = "DeepSeek";
        public string ApiKey = "";
    }

    public class UiCfg
    {
        public int Left = -1;
        public int Top = -1;
        public bool Collapsed = false;
        public double Opacity = 1.0;
        public bool TopMost = true;
        public string Mode = "bridge";
        public int AutoCollapseSeconds = 3;
    }

    public class AppConfig
    {
        public int RefreshIntervalSeconds = 5;
        public string ZaiAuthorization = "raw";
        public int WarnThreshold = 90;
        public CodexCfg Codex = new CodexCfg();
        public List<ZhipuCfg> Zhipu = new List<ZhipuCfg>();
        public DeepSeekCfg DeepSeek = new DeepSeekCfg();
        public UiCfg Ui = new UiCfg();
        public bool CreatedTemplate;
        public bool LoadError;

        public static string ConfigPath;

        const string AutostartValueName = "AIQuotaWidget";

        static JavaScriptSerializer NewJson()
        {
            return new JavaScriptSerializer { MaxJsonLength = int.MaxValue };
        }

        public static string FindConfigPath()
        {
            string exeDir = AppDomain.CurrentDomain.BaseDirectory;
            string beside = Path.Combine(exeDir, "config.json");
            string parent = Path.GetFullPath(Path.Combine(exeDir, "..", "config.json"));
            if (File.Exists(beside)) return beside;
            if (File.Exists(parent)) return parent;
            return parent; // 默认落在项目根（bin 的上一级）
        }

        public static AppConfig Load()
        {
            ConfigPath = FindConfigPath();
            AppConfig cfg = new AppConfig();
            if (!File.Exists(ConfigPath))
            {
                try
                {
                    cfg.Zhipu.Add(new ZhipuCfg());
                    Save(cfg);
                    cfg.CreatedTemplate = true;
                }
                catch { }
                return cfg;
            }
            try
            {
                string json = File.ReadAllText(ConfigPath, Encoding.UTF8);
                Dictionary<string, object> root = NewJson().DeserializeObject(json) as Dictionary<string, object>;
                if (root != null) MapFromDict(cfg, root);
            }
            catch
            {
                // 解析失败：保持默认值但禁止写回，避免后续 Save 覆盖用户手填的 Key
                cfg.LoadError = true;
            }
            if (cfg.Zhipu.Count == 0) cfg.Zhipu.Add(new ZhipuCfg());
            return cfg;
        }

        static void MapFromDict(AppConfig cfg, Dictionary<string, object> root)
        {
            cfg.RefreshIntervalSeconds = Clamp(Int(root, "refreshIntervalSeconds", 5), 5, 3600);
            string scheme = Str(root, "zaiAuthorization", "raw");
            cfg.ZaiAuthorization = scheme == "bearer" ? "bearer" : "raw";
            cfg.WarnThreshold = Clamp(Int(root, "warnThreshold", 90), 5, 100);

            Dictionary<string, object> accounts = Dict(root, "accounts");
            Dictionary<string, object> codex = Dict(accounts, "codex");
            if (codex != null)
            {
                cfg.Codex.Enabled = Bool(codex, "enabled", true);
                cfg.Codex.Visible = Bool(codex, "visible", true);
                cfg.Codex.Name = Str(codex, "name", cfg.Codex.Name);
                cfg.Codex.AuthJsonPath = Str(codex, "authJsonPath", "");
            }
            object[] zhipuArr = Array(accounts, "zhipu");
            if (zhipuArr != null)
            {
                cfg.Zhipu.Clear();
                foreach (object item in zhipuArr)
                {
                    Dictionary<string, object> z = item as Dictionary<string, object>;
                    if (z == null) continue;
                    ZhipuCfg zc = new ZhipuCfg();
                    zc.Visible = Bool(z, "visible", true);
                    zc.Name = Str(z, "name", "");
                    zc.ApiKey = Str(z, "apiKey", "");
                    cfg.Zhipu.Add(zc);
                }
            }
            Dictionary<string, object> ds = Dict(accounts, "deepseek");
            if (ds != null)
            {
                cfg.DeepSeek.Enabled = Bool(ds, "enabled", false);
                cfg.DeepSeek.Visible = Bool(ds, "visible", true);
                cfg.DeepSeek.Name = Str(ds, "name", cfg.DeepSeek.Name);
                cfg.DeepSeek.ApiKey = Str(ds, "apiKey", "");
            }
            Dictionary<string, object> ui = Dict(root, "ui");
            if (ui != null)
            {
                cfg.Ui.Left = Int(ui, "left", -1);
                cfg.Ui.Top = Int(ui, "top", -1);
                cfg.Ui.Collapsed = Bool(ui, "collapsed", false);
                cfg.Ui.Opacity = Dbl(ui, "opacity", 1.0);
                cfg.Ui.TopMost = Bool(ui, "topMost", true);
                string uiMode = Str(ui, "mode", "bridge");
                cfg.Ui.Mode = uiMode == "line" ? "line" : "bridge";
                cfg.Ui.AutoCollapseSeconds = Clamp(Int(ui, "autoCollapseSeconds", 3), 0, 60);
            }
        }

        private static string Esc(string s)
        {
            if (s == null) return "";
            return s.Replace("\\", "\\\\").Replace("\"", "\\\"");
        }

        private static string B(bool v) { return v ? "true" : "false"; }

        private static string BuildPretty(AppConfig cfg)
        {
            StringBuilder sb = new StringBuilder();
            sb.Append("{\n");
            sb.Append("  \"refreshIntervalSeconds\": " + cfg.RefreshIntervalSeconds + ",\n");
            sb.Append("  \"zaiAuthorization\": \"" + Esc(cfg.ZaiAuthorization) + "\",\n");
            sb.Append("  \"warnThreshold\": " + cfg.WarnThreshold + ",\n");
            sb.Append("\n");
            sb.Append("  \"accounts\": {\n");
            sb.Append("    \"codex\": {\n");
            sb.Append("      \"enabled\": " + B(cfg.Codex.Enabled) + ",\n");
            sb.Append("      \"visible\": " + B(cfg.Codex.Visible) + ",\n");
            sb.Append("      \"name\": \"" + Esc(cfg.Codex.Name) + "\",\n");
            sb.Append("      \"authJsonPath\": \"" + Esc(cfg.Codex.AuthJsonPath) + "\"\n");
            sb.Append("    },\n");
            sb.Append("    \"zhipu\": [\n");
            for (int i = 0; i < cfg.Zhipu.Count; i++)
            {
                ZhipuCfg z = cfg.Zhipu[i];
                sb.Append("      {\n");
                sb.Append("      \"visible\": " + B(z.Visible) + ",\n");
                sb.Append("      \"name\": \"" + Esc(z.Name) + "\",\n");
                sb.Append("      \"apiKey\": \"" + Esc(z.ApiKey) + "\"\n");
                sb.Append("      }" + (i < cfg.Zhipu.Count - 1 ? "," : "") + "\n");
            }
            sb.Append("    ],\n");
            sb.Append("    \"deepseek\": {\n");
            sb.Append("      \"enabled\": " + B(cfg.DeepSeek.Enabled) + ",\n");
            sb.Append("      \"visible\": " + B(cfg.DeepSeek.Visible) + ",\n");
            sb.Append("      \"name\": \"" + Esc(cfg.DeepSeek.Name) + "\",\n");
            sb.Append("      \"apiKey\": \"" + Esc(cfg.DeepSeek.ApiKey) + "\"\n");
            sb.Append("    }\n");
            sb.Append("  },\n");
            sb.Append("\n");
            sb.Append("  \"ui\": {\n");
            sb.Append("    \"left\": " + cfg.Ui.Left + ",\n");
            sb.Append("    \"top\": " + cfg.Ui.Top + ",\n");
            sb.Append("    \"opacity\": " + cfg.Ui.Opacity.ToString(System.Globalization.CultureInfo.InvariantCulture) + ",\n");
            sb.Append("    \"topMost\": " + B(cfg.Ui.TopMost) + ",\n");
            sb.Append("    \"mode\": \"" + Esc(cfg.Ui.Mode) + "\",\n");
            sb.Append("    \"autoCollapseSeconds\": " + cfg.Ui.AutoCollapseSeconds + "\n");
            sb.Append("  }\n");
            sb.Append("}\n");
            return sb.ToString();
        }

        public static void Save(AppConfig cfg)
        {
            try
            {
                if (cfg.LoadError) return; // 配置解析失败时禁止覆盖写回
                if (string.IsNullOrEmpty(ConfigPath)) ConfigPath = FindConfigPath();

                string dir = Path.GetDirectoryName(ConfigPath);
                if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir)) Directory.CreateDirectory(dir);
                // 手拼格式化 JSON：字段固定、逐行缩进，方便 notepad 里查找编辑；原子写 + 上一版备份
                string tmp = ConfigPath + ".tmp";
                string bak = ConfigPath + ".bak";
                File.WriteAllText(tmp, BuildPretty(cfg), Encoding.UTF8);
                if (File.Exists(ConfigPath))
                {
                    try { if (File.Exists(bak)) File.Delete(bak); }
                    catch { }
                    File.Replace(tmp, ConfigPath, bak, false);
                }
                else File.Move(tmp, ConfigPath);
            }
            catch { }
        }

        // ---- 注册表开机自启（HKCU，无需管理员） ----

        public static bool GetAutostart()
        {
            try
            {
                using (RegistryKey k = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run", false))
                {
                    if (k == null) return false;
                    return k.GetValue(AutostartValueName) != null;
                }
            }
            catch { return false; }
        }

        public static void SetAutostart(bool enable, string exePath)
        {
            try
            {
                using (RegistryKey k = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run"))
                {
                    if (k == null) return;
                    if (enable) k.SetValue(AutostartValueName, "\"" + exePath + "\"");
                    else
                    {
                        try { k.DeleteValue(AutostartValueName, false); }
                        catch { }
                    }
                }
            }
            catch { }
        }

        // ---- 弱类型取值工具 ----

        static Dictionary<string, object> Dict(Dictionary<string, object> d, string key)
        {
            object v;
            if (d != null && d.TryGetValue(key, out v)) return v as Dictionary<string, object>;
            return null;
        }

        static object[] Array(Dictionary<string, object> d, string key)
        {
            object v;
            if (d != null && d.TryGetValue(key, out v)) return v as object[];
            return null;
        }

        static string Str(Dictionary<string, object> d, string key, string def)
        {
            object v;
            if (d != null && d.TryGetValue(key, out v))
            {
                string s = v as string;
                if (s != null) return s;
            }
            return def;
        }

        static bool Bool(Dictionary<string, object> d, string key, bool def)
        {
            object v;
            if (d != null && d.TryGetValue(key, out v))
            {
                if (v is bool) return (bool)v;
            }
            return def;
        }

        static int Int(Dictionary<string, object> d, string key, int def)
        {
            object v;
            if (d != null && d.TryGetValue(key, out v))
            {
                try { return Convert.ToInt32(v, CultureInfo.InvariantCulture); }
                catch { }
            }
            return def;
        }

        static double Dbl(Dictionary<string, object> d, string key, double def)
        {
            object v;
            if (d != null && d.TryGetValue(key, out v))
            {
                try { return Convert.ToDouble(v, CultureInfo.InvariantCulture); }
                catch { }
            }
            return def;
        }

        static int Clamp(int v, int lo, int hi)
        {
            return v < lo ? lo : (v > hi ? hi : v);
        }
    }
}
