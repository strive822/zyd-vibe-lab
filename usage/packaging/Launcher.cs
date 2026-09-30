using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using System.Windows.Forms;

[assembly: AssemblyTitle("usage")]
[assembly: AssemblyDescription("额度、快捷文本与每日提醒")]
[assembly: AssemblyVersion("0.1.0.0")]
[assembly: AssemblyFileVersion("0.1.0.0")]

internal static class Launcher
{
    // Windows argv quoting with no shell, including trailing backslashes.
    private static string Quote(string value)
    {
        StringBuilder result = new StringBuilder("\"");
        int slashes = 0;
        foreach (char item in value)
        {
            if (item == '\\') { slashes++; continue; }
            result.Append('\\', item == '"' ? slashes * 2 + 1 : slashes);
            result.Append(item);
            slashes = 0;
        }
        result.Append('\\', slashes * 2);
        return result.Append('"').ToString();
    }

    [STAThread]
    private static int Main(string[] args)
    {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        string python = Path.Combine(root, "runtime", "pythonw.exe");
        string script = Path.Combine(root, "app", "run_app.py");
        try
        {
            if (!File.Exists(python) || !File.Exists(script))
                throw new FileNotFoundException();
            StringBuilder arguments = new StringBuilder("-B ").Append(Quote(script));
            foreach (string argument in args) arguments.Append(' ').Append(Quote(argument));
            ProcessStartInfo start = new ProcessStartInfo(python, arguments.ToString());
            start.WorkingDirectory = root;
            start.UseShellExecute = false;
            start.CreateNoWindow = true;
            using (Process process = Process.Start(start)) { if (process == null) throw new IOException(); }
            return 0;
        }
        catch (Exception)
        {
            MessageBox.Show("usage未能启动。请完整解压压缩包，不要单独移动启动文件。", "usage", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return 1;
        }
    }
}
