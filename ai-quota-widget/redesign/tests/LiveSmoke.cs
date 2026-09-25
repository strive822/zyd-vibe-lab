using System;
using System.IO;
using System.Security.Cryptography;
using System.Threading;

namespace QuotaWidget
{
    // Explicit opt-in, read-only integration check. Never prints keys, account names,
    // balances, raw responses, credential paths or account identifiers.
    internal static class LiveSmoke
    {
        static string Digest(string path)
        {
            if (!File.Exists(path)) return null;
            using (SHA256 sha = SHA256.Create())
            using (FileStream input = File.OpenRead(path))
                return Convert.ToBase64String(sha.ComputeHash(input));
        }

        static int Main(string[] args)
        {
            if (args.Length != 2 || args[0] != "--config")
            {
                Console.WriteLine("Usage: QuotaLiveSmoke.exe --config <local-config-path>");
                return 2;
            }
            try
            {
                string configBefore = Digest(args[1]);
                AppConfig cfg = AppConfig.LoadFromPath(args[1]);
                if (cfg.LoadError) { Console.WriteLine("CONFIG: invalid; no requests sent"); return 2; }
                if (cfg.Codex.Enabled)
                {
                    string authPath = Providers.ResolveCodexAuthPath(cfg.Codex.AuthJsonPath);
                    string before = Digest(authPath);
                    if (before == null) Console.WriteLine("Codex: UNVERIFIED (no login file)");
                    else
                    {
                        Report("Codex", Providers.FetchCodex(cfg.Codex.AuthJsonPath, CancellationToken.None));
                        Console.WriteLine("Codex login file unchanged: " + (before == Digest(authPath)));
                    }
                }
                else Console.WriteLine("Codex: UNVERIFIED (disabled)");
                for (int i = 0; i < cfg.Zhipu.Count; i++)
                {
                    ZhipuCfg z = cfg.Zhipu[i];
                    string label = "Zhipu #" + (i + 1);
                    if (!z.Visible || string.IsNullOrWhiteSpace(z.ApiKey))
                        Console.WriteLine(label + ": UNVERIFIED (hidden or no key)");
                    else Report(label, Providers.FetchZhipu(z.ApiKey, cfg.ZaiAuthorization, CancellationToken.None));
                }
                if (!cfg.DeepSeek.Enabled || string.IsNullOrWhiteSpace(cfg.DeepSeek.ApiKey))
                    Console.WriteLine("DeepSeek: UNVERIFIED (disabled or no key)");
                else Report("DeepSeek", Providers.FetchDeepSeek(cfg.DeepSeek.ApiKey, CancellationToken.None));
                bool unchanged = configBefore == Digest(args[1]);
                Console.WriteLine("Production config unchanged: " + unchanged);
                return unchanged ? 0 : 1;
            }
            catch (Exception error)
            {
                Console.WriteLine("SMOKE: unable to complete (" + error.GetType().Name + ")");
                return 1;
            }
        }

        static void Report(string provider, FetchResult result)
        {
            Console.WriteLine(provider + ": HTTP " + result.StatusCode + ", parsed=" + result.Ok +
                ", requiresLogin=" + result.RequiresLogin + ", stale=" + result.Stale +
                ", partial=" + !string.IsNullOrEmpty(result.Warning));
        }
    }
}
