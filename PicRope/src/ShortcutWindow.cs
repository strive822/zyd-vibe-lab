using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace ScreenLine
{
    internal sealed class ShortcutWindow : Window
    {
        internal readonly TextBox Input = new TextBox { IsReadOnly = true, Padding = new Thickness(12, 10, 12, 10), FontSize = 16 };
        internal readonly Button SaveButton;
        readonly TextBlock error = new TextBlock { TextWrapping = TextWrapping.Wrap, Foreground = LightTheme.Brush("#B74E4A"), Margin = new Thickness(0, 10, 0, 14) };
        internal uint Modifiers, VirtualKey;

        internal static string Label(uint modifiers, uint key)
        {
            if (key == 0) return "未设置";
            return ((modifiers & 2) != 0 ? "Ctrl+" : "") + ((modifiers & 1) != 0 ? "Alt+" : "")
                + ((modifiers & 4) != 0 ? "Shift+" : "") + ((modifiers & 8) != 0 ? "Win+" : "") + KeyInterop.KeyFromVirtualKey((int)key);
        }

        internal ShortcutWindow(uint modifiers, uint key, Func<uint, uint, bool> save, bool allowClear = false, string heading = "截图快捷键")
        {
            Title = heading + " · 图绳"; Width = 420; Height = 290; ResizeMode = ResizeMode.NoResize;
            WindowStartupLocation = WindowStartupLocation.CenterScreen; ShowInTaskbar = false; Topmost = true;
            FontFamily = new System.Windows.Media.FontFamily("Microsoft YaHei UI");
            var body = new StackPanel { Margin = new Thickness(24) };
            body.Children.Add(new TextBlock { Text = heading, FontSize = 20, Margin = new Thickness(0, 0, 0, 12) });
            body.Children.Add(new TextBlock { Text = "点击下方，按下新的组合键", Margin = new Thickness(0, 0, 0, 10), Foreground = LightTheme.Brush("#65717F") });
            Modifiers = modifiers; VirtualKey = key; Input.Text = Label(modifiers, key); body.Children.Add(Input); body.Children.Add(error);
            SaveButton = LightTheme.Button("保存", delegate
            {
                if (save(Modifiers, VirtualKey)) Close(); else error.Text = "组合键已被占用，请换一组。";
            }, "primary");
            var actionsRow = new DockPanel { LastChildFill = false };
            if (allowClear)
            {
                var clear = LightTheme.Button("禁用", delegate { if (save(0, 0)) Close(); else error.Text = "无法保存设置，请重试。"; });
                DockPanel.SetDock(clear, Dock.Left); actionsRow.Children.Add(clear);
            }
            DockPanel.SetDock(SaveButton, Dock.Right); actionsRow.Children.Add(SaveButton); body.Children.Add(actionsRow); Content = body;
            Input.PreviewKeyDown += delegate(object sender, KeyEventArgs e)
            {
                e.Handled = true;
                Key pressed = e.Key == Key.System ? e.SystemKey : e.Key;
                if (pressed == Key.LeftCtrl || pressed == Key.RightCtrl || pressed == Key.LeftAlt || pressed == Key.RightAlt || pressed == Key.LeftShift || pressed == Key.RightShift || pressed == Key.LWin || pressed == Key.RWin) return;
                uint mods = (uint)Keyboard.Modifiers;
                // WPF 的 Alt/Control/Shift/Windows 位与 RegisterHotKey 一致。
                if (mods == 0 || pressed == Key.Escape || pressed == Key.Tab) { error.Text = "请使用 Ctrl、Alt、Shift 或 Win 搭配其他按键。"; return; }
                Modifiers = mods; VirtualKey = (uint)KeyInterop.VirtualKeyFromKey(pressed); Input.Text = Label(mods, VirtualKey); error.Text = "";
            };
            Loaded += delegate { Activate(); WindowsNative.ActivateEditor(new System.Windows.Interop.WindowInteropHelper(this).Handle); Input.Focus(); };
        }
    }
}
