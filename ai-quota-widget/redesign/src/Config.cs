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
        public string Id = Guid.NewGuid().ToString("N");
        public bool Visible = true;
        public string Name = "";
        public string ApiKey = "";
        internal Dictionary<string, object> SourceFields = new Dictionary<string, object>();

        public ZhipuCfg Clone()
        {
            return new ZhipuCfg { Id = Id, Visible = Visible, Name = Name, ApiKey = ApiKey,
                SourceFields = AppConfig.CopyFields(SourceFields) };
        }
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
        public bool TopMost = true;
    }

    public class AppConfig
    {
        public int RefreshIntervalSeconds = 10;
        public string ZaiAuthorization = "raw";
        public int WarnThreshold = 90;
        public CodexCfg Codex = new CodexCfg();
        public List<ZhipuCfg> Zhipu = new List<ZhipuCfg>();
        public DeepSeekCfg DeepSeek = new DeepSeekCfg();
        public UiCfg Ui = new UiCfg();
        public bool LoadError;

        public static string ConfigPath;

        const string AutostartValueName = "AIQuotaWidget";

        public AppConfig Clone()
        {
            AppConfig copy = new AppConfig {
                RefreshIntervalSeconds = RefreshIntervalSeconds,
                ZaiAuthorization = ZaiAuthorization, WarnThreshold = WarnThreshold, LoadError = LoadError,
                Codex = new CodexCfg { Enabled = Codex.Enabled, Visible = Codex.Visible,
                    Name = Codex.Name, AuthJsonPath = Codex.AuthJsonPath },
                DeepSeek = new DeepSeekCfg { Enabled = DeepSeek.Enabled, Visible = DeepSeek.Visible,
                    Name = DeepSeek.Name, ApiKey = DeepSeek.ApiKey },
                Ui = new UiCfg { Left = Ui.Left, Top = Ui.Top, TopMost = Ui.TopMost }
            };
            foreach (ZhipuCfg account in Zhipu) copy.Zhipu.Add(account.Clone());
            return copy;
        }

        internal static Dictionary<string, object> CopyFields(Dictionary<string, object> fields)
        {
            if (fields == null || fields.Count == 0) return new Dictionary<string, object>();
            JavaScriptSerializer json = NewJson();
            return (Dictionary<string, object>)json.DeserializeObject(json.Serialize(fields));
        }

        public static string ZhipuDisplayName(ZhipuCfg account, int index)
        {
            if (!string.IsNullOrWhiteSpace(account.Name)) return account.Name;
            return index == 0 ? "智谱" : "智谱 " + (index + 1);
        }

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
            return LoadFromPath(FindConfigPath());
        }

        public static AppConfig LoadFromPath(string path)
        {
            ConfigPath = path;
            AppConfig cfg = new AppConfig();
            if (!File.Exists(ConfigPath))
            {
                cfg.Zhipu.Add(new ZhipuCfg());
                return cfg;
            }
            try
            {
                string json = File.ReadAllText(ConfigPath, Encoding.UTF8);
                Dictionary<string, object> root = NewJson().DeserializeObject(json) as Dictionary<string, object>;
                if (root == null) throw new InvalidDataException("配置根节点不是对象");
                ValidateStructure(root);
                MapFromDict(cfg, root);
            }
            catch
            {
                // 解析失败：保持默认值但禁止写回，避免后续 Save 覆盖用户手填的 Key
                cfg.LoadError = true;
            }
            return cfg;
        }

        static void MapFromDict(AppConfig cfg, Dictionary<string, object> root)
        {
            cfg.RefreshIntervalSeconds = Clamp(Int(root, "refreshIntervalSeconds", 10), 10, 3600);
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
                    ZhipuCfg zc = new ZhipuCfg();
                    zc.Id = Str(z, "id", "");
                    zc.Visible = Bool(z, "visible", true);
                    zc.Name = Str(z, "name", "");
                    zc.ApiKey = Str(z, "apiKey", "");
                    zc.SourceFields = CopyFields(z);
                    cfg.Zhipu.Add(zc);
                }
            }
            EnsureAccountIds(cfg.Zhipu);
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
                cfg.Ui.TopMost = Bool(ui, "topMost", true);
            }
        }

        public static bool Save(AppConfig cfg)
        {
            string tmp = null;
            bool tempOwned = false;
            try
            {
                if (cfg == null || cfg.LoadError) return false;
                if (string.IsNullOrEmpty(ConfigPath)) ConfigPath = FindConfigPath();

                string dir = Path.GetDirectoryName(ConfigPath);
                if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir)) Directory.CreateDirectory(dir);
                // 在原对象上更新已知字段，保留其他 Agent 或以后版本加入的字段。
                Dictionary<string, object> root = File.Exists(ConfigPath)
                    ? NewJson().DeserializeObject(File.ReadAllText(ConfigPath, Encoding.UTF8)) as Dictionary<string, object>
                    : new Dictionary<string, object>();
                if (root == null) return false;
                ValidateStructure(root);
                EnsureAccountIds(cfg.Zhipu);
                root["refreshIntervalSeconds"] = Clamp(cfg.RefreshIntervalSeconds, 10, 3600);
                root["zaiAuthorization"] = cfg.ZaiAuthorization;
                root["warnThreshold"] = cfg.WarnThreshold;
                Dictionary<string, object> accounts = EnsureDict(root, "accounts");
                Dictionary<string, object> codex = EnsureDict(accounts, "codex");
                codex["enabled"] = cfg.Codex.Enabled;
                codex["visible"] = cfg.Codex.Visible;
                codex["name"] = cfg.Codex.Name;
                codex["authJsonPath"] = cfg.Codex.AuthJsonPath;
                List<object> zhipu = new List<object>();
                for (int i = 0; i < cfg.Zhipu.Count; i++)
                {
                    ZhipuCfg z = cfg.Zhipu[i];
                    // 扩展字段属于账号对象，不随删除或排序转移给同位置的其他账号。
                    Dictionary<string, object> zd = CopyFields(z.SourceFields);
                    zd["id"] = z.Id;
                    zd["visible"] = z.Visible;
                    zd["name"] = z.Name;
                    zd["apiKey"] = z.ApiKey;
                    zhipu.Add(zd);
                }
                accounts["zhipu"] = zhipu;
                Dictionary<string, object> deepseek = EnsureDict(accounts, "deepseek");
                deepseek["enabled"] = cfg.DeepSeek.Enabled;
                deepseek["visible"] = cfg.DeepSeek.Visible;
                deepseek["name"] = cfg.DeepSeek.Name;
                deepseek["apiKey"] = cfg.DeepSeek.ApiKey;
                Dictionary<string, object> ui = EnsureDict(root, "ui");
                ui["left"] = cfg.Ui.Left;
                ui["top"] = cfg.Ui.Top;
                ui.Remove("opacity");
                ui["topMost"] = cfg.Ui.TopMost;
                ui["designVersion"] = 4;
                ui.Remove("mode");
                ui.Remove("collapsed");
                ui.Remove("autoCollapseSeconds");
                tmp = ConfigPath + ".tmp";
                string bak = ConfigPath + ".bak";
                string serialized = NewJson().Serialize(root);
                tempOwned = true;
                File.WriteAllText(tmp, serialized, Encoding.UTF8);
                if (File.Exists(ConfigPath))
                {
                    File.Replace(tmp, ConfigPath, bak, false);
                }
                else File.Move(tmp, ConfigPath);
                return true;
            }
            catch
            {
                // A failed replacement must not leave a second file containing keys.
                if (tempOwned)
                {
                    try { File.Delete(tmp); }
                    catch { }
                }
                return false;
            }
        }

        private static void EnsureAccountIds(List<ZhipuCfg> accounts)
        {
            HashSet<string> seen = new HashSet<string>(StringComparer.Ordinal);
            foreach (ZhipuCfg account in accounts)
            {
                if (!string.IsNullOrWhiteSpace(account.Id) && seen.Add(account.Id)) continue;
                do { account.Id = Guid.NewGuid().ToString("N"); } while (!seen.Add(account.Id));
            }
        }

        private static void ValidateStructure(Dictionary<string, object> root)
        {
            Dictionary<string, object> accounts = RequireObject(root, "accounts");
            RequireObject(root, "ui");
            if (accounts == null) return;
            RequireObject(accounts, "codex");
            RequireObject(accounts, "deepseek");
            object value;
            if (!accounts.TryGetValue("zhipu", out value)) return;
            object[] rows = value as object[];
            if (rows == null) throw new InvalidDataException("accounts.zhipu 不是数组");
            foreach (object row in rows)
                if (!(row is Dictionary<string, object>))
                    throw new InvalidDataException("智谱账号不是对象");
        }

        private static Dictionary<string, object> RequireObject(Dictionary<string, object> parent, string key)
        {
            object value;
            if (!parent.TryGetValue(key, out value)) return null;
            Dictionary<string, object> result = value as Dictionary<string, object>;
            if (result == null) throw new InvalidDataException(key + " 不是对象");
            return result;
        }

        private static Dictionary<string, object> EnsureDict(Dictionary<string, object> parent, string key)
        {
            Dictionary<string, object> value = Dict(parent, key);
            if (value == null) { value = new Dictionary<string, object>(); parent[key] = value; }
            return value;
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

        public static bool SetAutostart(bool enable, string exePath)
        {
            return SetAutostart(enable, exePath, WriteAutostart);
        }

        internal static bool SetAutostart(bool enable, string exePath, Action<bool, string> write)
        {
            try
            {
                write(enable, exePath);
                return true;
            }
            catch { return false; }
        }

        private static void WriteAutostart(bool enable, string exePath)
        {
            using (RegistryKey k = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run"))
            {
                if (k == null) throw new UnauthorizedAccessException();
                if (enable) k.SetValue(AutostartValueName, "\"" + exePath + "\"");
                else k.DeleteValue(AutostartValueName, false);
            }
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
                if (v == null) return def;
                try { return Convert.ToInt32(v, CultureInfo.InvariantCulture); }
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
