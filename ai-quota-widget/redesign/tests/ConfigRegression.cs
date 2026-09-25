using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace QuotaWidget
{
    internal static class ConfigRegression
    {
        public static void Run(Action<string, bool, string> check)
        {
            string oldPath = AppConfig.ConfigPath;
            string directory = Path.Combine(Path.GetTempPath(), "quota-config-regression-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(directory);
            try
            {
                TestAccountIdentity(directory, check);
                TestIdMigration(directory, check);
                TestSourceProtection(directory, check);
                TestNullIntegerDefaults(directory, check);
                TestSaveFailureAndBackup(directory, check);
                TestOpacity(directory, check);
            }
            finally
            {
                AppConfig.ConfigPath = oldPath;
                Directory.Delete(directory, true);
            }
        }

        private static AppConfig LoadFixture(string directory, string name, string json)
        {
            string path = Path.Combine(directory, name + ".json");
            File.WriteAllText(path, json, Encoding.UTF8);
            return AppConfig.LoadFromPath(path);
        }

        private static Dictionary<string, object> SavedRoot()
        {
            return Providers.ParseJsonObject(File.ReadAllText(AppConfig.ConfigPath, Encoding.UTF8));
        }

        private static object[] Accounts(Dictionary<string, object> root)
        {
            return (object[])((Dictionary<string, object>)root["accounts"])["zhipu"];
        }

        private static string Owner(object row)
        {
            return (string)((Dictionary<string, object>)((Dictionary<string, object>)row)["custom"])["owner"];
        }

        private static void TestAccountIdentity(string directory, Action<string, bool, string> check)
        {
            string original = "{\"rootCustom\":true,\"accounts\":{\"accountCustom\":true," +
                "\"codex\":{\"extension\":true},\"deepseek\":{\"extension\":true},\"zhipu\":[" +
                "{\"name\":\"A\",\"apiKey\":\"synthetic-a\",\"custom\":{\"owner\":\"A\"}}," +
                "{\"name\":\"B\",\"apiKey\":\"synthetic-b\",\"custom\":{\"owner\":\"B\"}}]}," +
                "\"ui\":{\"extension\":true}}";
            AppConfig source = LoadFixture(directory, "identity", original);
            string firstId = source.Zhipu[0].Id, secondId = source.Zhipu[1].Id;
            check("config.ids: legacy load generates unique IDs without writing",
                !string.IsNullOrWhiteSpace(firstId) && firstId != secondId &&
                File.ReadAllText(AppConfig.ConfigPath, Encoding.UTF8) == original, null);
            AppConfig draft = source.Clone();
            draft.Zhipu.Reverse();
            draft.Zhipu[0].Name = "renamed";
            draft.Zhipu[0].ApiKey = "synthetic-replacement";
            check("config.clone: editing draft leaves original account unchanged",
                source.Zhipu[1].Name == "B" && source.Zhipu[1].ApiKey == "synthetic-b" &&
                draft.Zhipu[0].Id == secondId, null);
            check("config.identity: reordered draft saves", AppConfig.Save(draft), null);
            Dictionary<string, object> root = SavedRoot();
            object[] rows = Accounts(root);
            check("config.identity: metadata follows reordered and edited accounts",
                Owner(rows[0]) == "B" && Owner(rows[1]) == "A", null);
            Dictionary<string, object> accounts = (Dictionary<string, object>)root["accounts"];
            check("config.identity: unrelated extension fields survive",
                root.ContainsKey("rootCustom") && accounts.ContainsKey("accountCustom") &&
                ((Dictionary<string, object>)accounts["codex"]).ContainsKey("extension") &&
                ((Dictionary<string, object>)accounts["deepseek"]).ContainsKey("extension") &&
                ((Dictionary<string, object>)root["ui"]).ContainsKey("extension"), null);
            AppConfig reloaded = AppConfig.LoadFromPath(AppConfig.ConfigPath);
            check("config.ids: saved IDs survive reload",
                reloaded.Zhipu[0].Id == secondId && reloaded.Zhipu[1].Id == firstId, null);

            source = LoadFixture(directory, "delete-first", original);
            secondId = source.Zhipu[1].Id;
            draft = source.Clone();
            draft.Zhipu.RemoveAt(0);
            check("config.identity: deleting first account saves", AppConfig.Save(draft), null);
            rows = Accounts(SavedRoot());
            check("config.identity: remaining account keeps own metadata and ID",
                rows.Length == 1 && Owner(rows[0]) == "B" &&
                (string)((Dictionary<string, object>)rows[0])["id"] == secondId, null);

            draft = source.Clone();
            ((Dictionary<string, object>)draft.Zhipu[0].SourceFields["custom"])["owner"] = "draft";
            check("config.clone: nested metadata is isolated from canceled draft",
                (string)((Dictionary<string, object>)source.Zhipu[0].SourceFields["custom"])["owner"] == "A", null);
        }

        private static void TestIdMigration(string directory, Action<string, bool, string> check)
        {
            AppConfig cfg = LoadFixture(directory, "ids", "{\"accounts\":{\"zhipu\":[" +
                "{\"id\":\"existing\"},{\"id\":\"existing\"},{},{\"id\":17},{\"id\":\" \"}," +
                "{\"id\":\"external-id\"}]}}");
            HashSet<string> ids = new HashSet<string>(StringComparer.Ordinal);
            bool unique = true;
            foreach (ZhipuCfg account in cfg.Zhipu)
                unique = !string.IsNullOrWhiteSpace(account.Id) && ids.Add(account.Id) && unique;
            check("config.ids: missing, invalid and duplicate IDs are repaired",
                unique && cfg.Zhipu[0].Id == "existing" && cfg.Zhipu[5].Id == "external-id", null);
            check("config.ids: migration saves", AppConfig.Save(cfg), null);
            AppConfig loaded = AppConfig.LoadFromPath(AppConfig.ConfigPath);
            bool stable = loaded.Zhipu.Count == cfg.Zhipu.Count;
            for (int i = 0; stable && i < cfg.Zhipu.Count; i++) stable = cfg.Zhipu[i].Id == loaded.Zhipu[i].Id;
            check("config.ids: repaired IDs are stable after reload", stable, null);
            ZhipuCfg added = new ZhipuCfg();
            check("config.ids: added account has an independent ID",
                !string.IsNullOrWhiteSpace(added.Id) && !ids.Contains(added.Id), null);
        }

        private static void TestSourceProtection(string directory, Action<string, bool, string> check)
        {
            string[] invalid = {
                "{broken", "[]", "null", "{\"accounts\":\"opaque\"}", "{\"accounts\":null}",
                "{\"accounts\":{\"codex\":false}}", "{\"accounts\":{\"deepseek\":[]}}",
                "{\"accounts\":{\"zhipu\":{}}}", "{\"accounts\":{\"zhipu\":[null]}}",
                "{\"accounts\":{\"zhipu\":[\"opaque\"]}}", "{\"ui\":[]}"
            };
            for (int i = 0; i < invalid.Length; i++)
            {
                AppConfig cfg = LoadFixture(directory, "invalid-" + i, invalid[i]);
                AppConfig draft = cfg.Clone();
                check("config.protection: malformed structure " + i + " is preserved",
                    cfg.LoadError && draft.LoadError && !AppConfig.Save(draft) &&
                    File.ReadAllText(AppConfig.ConfigPath, Encoding.UTF8) == invalid[i], null);
            }

            AppConfig failed = LoadFixture(directory, "later-repaired", "{broken").Clone();
            string repaired = "{\"accounts\":{\"zhipu\":[{\"apiKey\":\"synthetic-recovered\"}]}}";
            File.WriteAllText(AppConfig.ConfigPath, repaired, Encoding.UTF8);
            check("config.protection: stale error draft cannot overwrite repaired file",
                !AppConfig.Save(failed) && File.ReadAllText(AppConfig.ConfigPath, Encoding.UTF8) == repaired, null);
            AppConfig fresh = AppConfig.LoadFromPath(AppConfig.ConfigPath);
            check("config.protection: successful reload restores editing", !fresh.LoadError && AppConfig.Save(fresh), null);

            failed = LoadFixture(directory, "later-deleted", "{broken").Clone();
            File.Delete(AppConfig.ConfigPath);
            check("config.protection: stale error draft cannot recreate deleted file",
                !AppConfig.Save(failed) && !File.Exists(AppConfig.ConfigPath), null);

            string missing = Path.Combine(directory, "first-run.json");
            AppConfig firstRun = AppConfig.LoadFromPath(missing);
            check("config.protection: first missing file remains editable",
                !firstRun.LoadError && !File.Exists(missing) && AppConfig.Save(firstRun) && File.Exists(missing), null);

            AppConfig valid = LoadFixture(directory, "changed-on-disk", "{}");
            string changed = "{\"accounts\":17}";
            File.WriteAllText(AppConfig.ConfigPath, changed, Encoding.UTF8);
            check("config.protection: save revalidates current disk structure",
                !AppConfig.Save(valid) && File.ReadAllText(AppConfig.ConfigPath, Encoding.UTF8) == changed, null);
        }

        private static void TestSaveFailureAndBackup(string directory, Action<string, bool, string> check)
        {
            string original = "{\"accounts\":{\"zhipu\":[{\"id\":\"stable\",\"apiKey\":\"synthetic-old\"}]}}";
            AppConfig cfg = LoadFixture(directory, "save-failure", original);
            cfg.Zhipu[0].ApiKey = "synthetic-new";
            string path = AppConfig.ConfigPath;
            string backup = path + ".bak";
            Directory.CreateDirectory(backup); // Force File.Replace to fail after writing the temporary file.
            check("config.save-failure: replacement failure preserves original",
                !AppConfig.Save(cfg) && File.ReadAllText(path, Encoding.UTF8) == original, null);
            check("config.save-failure: credential-bearing temporary file is removed",
                !File.Exists(path + ".tmp"), null);
            Directory.Delete(backup);
            check("config.save-failure: retry keeps draft and saves", AppConfig.Save(cfg) &&
                AppConfig.LoadFromPath(path).Zhipu[0].ApiKey == "synthetic-new", null);
            check("config.backup: previous file is preserved",
                File.ReadAllText(backup, Encoding.UTF8) == original, null);
        }

        private static void TestNullIntegerDefaults(string directory, Action<string, bool, string> check)
        {
            AppConfig cfg = LoadFixture(directory, "null-integers",
                "{\"warnThreshold\":null,\"ui\":{\"left\":null,\"top\":null}}");
            check("config.null-integers: null uses field defaults",
                !cfg.LoadError && cfg.WarnThreshold == 90 && cfg.Ui.Left == -1 && cfg.Ui.Top == -1, null);
        }

        private static void TestOpacity(string directory, Action<string, bool, string> check)
        {
            string[] previous = { "0.7", "\"NaN\"", "\"Infinity\"", "\"not-a-number\"", "null", "false" };
            for (int i = 0; i < previous.Length; i++)
            {
                AppConfig cfg = LoadFixture(directory, "opacity-" + i, "{\"ui\":{\"opacity\":" + previous[i] + "}}");
                check("config.opacity: old value " + i + " is ignored", !cfg.LoadError, null);
                bool saved = AppConfig.Save(cfg);
                string json = System.IO.File.ReadAllText(AppConfig.ConfigPath);
                check("config.opacity: old setting " + i + " is removed on save",
                    saved && !json.Contains("\"opacity\"") && !AppConfig.LoadFromPath(AppConfig.ConfigPath).LoadError, null);
            }
        }
    }
}
