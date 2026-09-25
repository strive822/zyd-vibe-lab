using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;

namespace QuotaWidget
{
    internal static class Log
    {
        internal static void W(string s)
        {
            try
            {
                File.AppendAllText(
                    Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "startup.log"),
                    DateTime.Now.ToString("HH:mm:ss.fff") + " " + s + "\r\n");
            }
            catch { }
        }
    }

    internal static class Program
    {
        [DllImport("user32.dll")]
        private static extern bool SetProcessDPIAware();

        private static Mutex _mutex;
        private static EventWaitHandle _showSignal;

        [STAThread]
        private static void Main(string[] args)
        {
            bool preview = args != null && Array.IndexOf(args, "--preview") >= 0;
            bool mock = preview || (args != null && Array.IndexOf(args, "--mock") >= 0);
            string previewScenario = "normal";
            float previewScale = 0;
            if (mock && args != null)
                foreach (string arg in args)
                {
                    if (arg.StartsWith("--preview-scenario=")) previewScenario = arg.Substring("--preview-scenario=".Length);
                    if (arg.StartsWith("--preview-scale="))
                    {
                        float selected;
                        if (float.TryParse(arg.Substring("--preview-scale=".Length),
                            System.Globalization.NumberStyles.Float,
                            System.Globalization.CultureInfo.InvariantCulture, out selected) &&
                            (selected == 1f || selected == 1.5f || selected == 2f)) previewScale = selected;
                    }
                }
            string previewInstance = PreviewInstanceSuffix(mock, args);
            bool menuDemo = args != null && Array.IndexOf(args, "--menu-demo") >= 0;
            bool submenuDemo = args != null && Array.IndexOf(args, "--submenu-demo") >= 0;
            bool settingsDemo = args != null && Array.IndexOf(args, "--settings-demo") >= 0;
            Log.W("start, mock=" + mock + " menuDemo=" + menuDemo + " submenuDemo=" + submenuDemo);
            try { SetProcessDPIAware(); }
            catch { }

            bool owned;
            try
            {
                bool createdNew;
                _mutex = new Mutex(true, mock ? @"Local\AIQuotaWidget_Preview_Mutex" + previewInstance : @"Local\AIQuotaWidget_Mutex", out createdNew);
                owned = createdNew;
            }
            catch (AbandonedMutexException)
            {
                // 上个实例异常退出遗留的互斥量：等待方已获得所有权，按首实例继续
                owned = true;
            }
            Log.W("mutex owned=" + owned);
            bool signalCreated;
            _showSignal = new EventWaitHandle(false, EventResetMode.AutoReset,
                mock ? @"Local\AIQuotaWidget_Preview_ShowSignal" + previewInstance : @"Local\AIQuotaWidget_ShowSignal", out signalCreated);
            if (!owned)
            {
                try { _showSignal.Set(); }
                catch { }
                _showSignal.Dispose();
                if (_mutex != null) _mutex.Dispose();
                return;
            }

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            AppConfig cfg = LoadConfiguration(mock, previewScenario, AppConfig.Load);
            Log.W("config loaded, left=" + cfg.Ui.Left + " top=" + cfg.Ui.Top);
            Application.ThreadException += delegate(object s, System.Threading.ThreadExceptionEventArgs e)
            {
                Log.W("ui-thread-exception: " + e.Exception.GetType().Name);
            };
            AppDomain.CurrentDomain.UnhandledException += delegate(object s, UnhandledExceptionEventArgs e)
            {
                Log.W("unhandled-exception: " + (e.ExceptionObject == null ? "unknown" : e.ExceptionObject.GetType().Name));
            };
            WidgetForm form = new WidgetForm(cfg, mock, previewScenario, previewScale);
            if (mock) Log.W("mock mode on");
            if (menuDemo || submenuDemo)
            {
                form.OpenMenuForDemo(submenuDemo);
                Log.W("menu demo opened");
            }
            if (settingsDemo) form.OpenSettingsForDemo();
            Log.W("form constructed");
            try { Application.Run(form); }
            finally { StopSignalWorker(); form.Dispose(); }
            Log.W("app run ended");
            try { _mutex.ReleaseMutex(); }
            catch { }
            if (_mutex != null) _mutex.Dispose();
            if (_showSignal != null) _showSignal.Dispose();
        }

        internal static string PreviewInstanceSuffix(bool mock, string[] args)
        {
            if (!mock || args == null) return "";
            foreach (string arg in args)
            {
                Guid id;
                if (arg.StartsWith("--preview-instance=") && Guid.TryParse(arg.Substring(19), out id))
                    return "_" + id.ToString("N");
            }
            return "";
        }

        // Synthetic previews never consult the credential-bearing production configuration.
        internal static AppConfig LoadConfiguration(bool mock, string scenario, Func<AppConfig> loadProduction)
        {
            if (!mock) return loadProduction();
            AppConfig cfg = new AppConfig();
            cfg.Zhipu.Add(new ZhipuCfg { Name = "智谱（演示）" });
            cfg.Codex.Name = "OpenAI Codex（演示）";
            if (scenario == "reference") { cfg.Codex.Name = "OpenAI Codex"; cfg.Zhipu[0].Name = "智谱"; }
            cfg.DeepSeek.Name = "DeepSeek（演示）";
            cfg.DeepSeek.Enabled = scenario == "balance" || scenario == "many" || scenario == "partial" || scenario == "extreme";
            if (scenario == "many")
                for (int i = 0; i < 14; i++) cfg.Zhipu.Add(new ZhipuCfg { Name = "智谱演示 " + (i + 2) });
            if (scenario == "long")
            {
                cfg.Codex.Name = "OpenAI Codex / Development Workspace / " + new string('A', 64);
                cfg.Zhipu[0].Name = "智谱长名称演示：研发与运营工作流账号，包含完整状态及重置时间";
            }
            if (scenario == "config-error" || scenario == "config-error-bottom") cfg.LoadError = true;
            if (scenario == "no-accounts")
            {
                cfg.Codex.Enabled = false;
                cfg.DeepSeek.Enabled = false;
                cfg.Zhipu.Clear();
            }
            return cfg;
        }

        private static int _signalWorkerStarted;
        private static volatile bool _stopping;

        internal static void StopSignalWorker()
        {
            _stopping = true;
            try { if (_showSignal != null) _showSignal.Set(); } catch (ObjectDisposedException) { }
        }

        // 由 WidgetForm.OnShown 调用：窗体句柄就绪后再启动，避免第二实例的唤起信号在句柄创建前被消费丢失
        public static void StartSignalWorker(WidgetForm form)
        {
            if (Interlocked.Exchange(ref _signalWorkerStarted, 1) == 1) return;
            ThreadPool.QueueUserWorkItem(delegate
            {
                while (!_stopping)
                {
                    try
                    {
                        if (!_showSignal.WaitOne()) return;
                        if (_stopping) return;
                    }
                    catch { return; }
                    try { form.BeginInvoke((Action)form.ShowFromTray); }
                    catch { }
                }
            });
        }
    }
}
