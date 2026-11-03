using System;
using System.Windows;
using System.Windows.Controls;

namespace ScreenLine
{
    internal sealed class ShortcutRow
    {
        internal string Name, Label;
        internal Action Edit;
    }

    internal sealed class ShortcutSettingsWindow : Window
    {
        internal ShortcutSettingsWindow(ShortcutRow[] rows)
        {
            Title = "截图快捷键 · 图绳"; Width = 430; SizeToContent = SizeToContent.Height; ResizeMode = ResizeMode.NoResize;
            WindowStartupLocation = WindowStartupLocation.CenterScreen; ShowInTaskbar = false; Topmost = true;
            FontFamily = new System.Windows.Media.FontFamily("Microsoft YaHei UI");
            var body = new StackPanel { Margin = new Thickness(24) };
            body.Children.Add(new TextBlock { Text = "截图快捷键", FontSize = 20, Margin = new Thickness(0, 0, 0, 4) });
            body.Children.Add(new TextBlock { Text = "为不同截图方式设置独立组合键；不需要的保持“未设置”。", TextWrapping = TextWrapping.Wrap, Foreground = LightTheme.Brush("#65717F"), Margin = new Thickness(0, 0, 0, 12) });
            foreach (var row in rows)
            {
                var line = new DockPanel { Margin = new Thickness(0, 6, 0, 6), LastChildFill = false };
                var edit = LightTheme.Button("修改…", delegate { row.Edit(); }, "quiet");
                DockPanel.SetDock(edit, Dock.Right); edit.VerticalAlignment = VerticalAlignment.Center;
                var stack = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
                stack.Children.Add(new TextBlock { Text = row.Name, FontWeight = FontWeights.SemiBold, VerticalAlignment = VerticalAlignment.Center });
                stack.Children.Add(new TextBlock { Text = row.Label, Foreground = LightTheme.Brush("#65717F"), VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(10, 0, 0, 0) });
                line.Children.Add(stack); line.Children.Add(edit);
                body.Children.Add(line);
            }
            Content = body;
            Loaded += delegate { Activate(); Focus(); };
        }
    }
}
