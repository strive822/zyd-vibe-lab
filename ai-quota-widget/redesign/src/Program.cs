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
            bool mock = args != null && Array.IndexOf(args, "--mock") >= 0;
            bool menuDemo = args != null && Array.IndexOf(args, "--menu-demo") >= 0;
            Log.W("start, mock=" + mock + " menuDemo=" + menuDemo);
            try { SetProcessDPIAware(); }
            catch { }

            bool owned;
            try
            {
                bool createdNew;
                _mutex = new Mutex(true, @"Local\AIQuotaWidget_Mutex", out createdNew);
                owned = createdNew;
            }
            catch (AbandonedMutexException)
            {
                // 上个实例异常退出遗留的互斥量：等待方已获得所有权，按首实例继续
                owned = true;
            }
            Log.W("mutex owned=" + owned);
            bool signalCreated;
            _showSignal = new EventWaitHandle(false, EventResetMode.AutoReset, @"Local\AIQuotaWidget_ShowSignal", out signalCreated);
            if (!owned)
            {
                try { _showSignal.Set(); }
                catch { }
                return;
            }

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            AppConfig cfg = AppConfig.Load();
            Log.W("config loaded, mode=" + cfg.Ui.Mode + " opacity=" + cfg.Ui.Opacity + " left=" + cfg.Ui.Left + " top=" + cfg.Ui.Top);
            Application.ThreadException += delegate(object s, System.Threading.ThreadExceptionEventArgs e)
            {
                Log.W("ui-thread-exception: " + e.Exception);
            };
            AppDomain.CurrentDomain.UnhandledException += delegate(object s, UnhandledExceptionEventArgs e)
            {
                Log.W("unhandled-exception: " + e.ExceptionObject);
            };
            WidgetForm form = new WidgetForm(cfg, mock);
            if (mock) Log.W("mock mode on");
            if (menuDemo)
            {
                form.OpenMenuForDemo();
                Log.W("menu demo opened");
            }
            Log.W("form constructed");
            Application.Run(form);
            Log.W("app run ended");
            try { _mutex.ReleaseMutex(); }
            catch { }
        }

        private static int _signalWorkerStarted;

        // 由 WidgetForm.OnShown 调用：窗体句柄就绪后再启动，避免第二实例的唤起信号在句柄创建前被消费丢失
        public static void StartSignalWorker(WidgetForm form)
        {
            if (Interlocked.Exchange(ref _signalWorkerStarted, 1) == 1) return;
            ThreadPool.QueueUserWorkItem(delegate
            {
                while (true)
                {
                    try
                    {
                        if (!_showSignal.WaitOne()) return;
                    }
                    catch { return; }
                    try { form.BeginInvoke((Action)form.ShowFromTray); }
                    catch { }
                }
            });
        }
    }
}
