using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Media.Effects;
using System.Windows.Threading;

namespace ScreenLine
{
    // 屏幕顶端的常驻小挂钩：只有悬浮到这个具体的木夹上，绳子才会展开。
    internal sealed class HookWindow : Window
    {
        readonly ShelfWindow shelf;
        readonly StateStore store;
        readonly ClothesClip clip;
        readonly Border halo = new Border();
        readonly ScaleTransform grow = new ScaleTransform(1, 1);
        readonly DispatcherTimer settle = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(260) };
        bool leaving;

        internal HookWindow(ShelfWindow shelf, StateStore store)
        {
            this.shelf = shelf;
            this.store = store;
            Width = 44; Height = 52;
            WindowStyle = WindowStyle.None;
            ResizeMode = ResizeMode.NoResize;
            AllowsTransparency = true;
            Background = Brushes.Transparent;
            ShowInTaskbar = false;
            ShowActivated = false;
            Topmost = true;
            Title = "PicRope · 挂钩";
            RenderTransformOrigin = new Point(0.5, 0.3);
            RenderTransform = grow;
            FontFamily = new FontFamily("Microsoft YaHei UI");

            halo.Width = 40; halo.Height = 44; halo.CornerRadius = new CornerRadius(12);
            halo.Background = new SolidColorBrush(Color.FromArgb(214, 255, 255, 255));
            halo.BorderBrush = new SolidColorBrush(Color.FromRgb(206, 214, 224));
            halo.BorderThickness = new Thickness(1);
            halo.Effect = new DropShadowEffect { BlurRadius = 12, ShadowDepth = 2, Opacity = 0.22 };
            halo.Opacity = 0.92;
            clip = new ClothesClip(LineTheme.FromId(store.State.Theme), 0);
            clip.HorizontalAlignment = HorizontalAlignment.Center;
            clip.VerticalAlignment = VerticalAlignment.Center;
            clip.Margin = new Thickness(0, 4, 0, 0);
            var stack = new Grid();
            stack.Children.Add(halo);
            stack.Children.Add(clip);
            Content = stack;
            ToolTip = "悬浮这里展开图绳";
            ToolTipService.SetInitialShowDelay(this, 900);

            MouseEnter += delegate { leaving = false; settle.Stop(); Enter(); };
            MouseLeave += delegate { leaving = true; settle.Stop(); settle.Start(); };
            settle.Tick += delegate
            {
                settle.Stop();
                if (!leaving) return;
                // 鼠标离开挂钩后，若已移到绳子上则继续保持展开。
                var cursor = WindowsNative.Cursor();
                if (shelf.HoveringContents(cursor)) { leaving = false; return; }
                shelf.SetHookHover(false);
                Animate(1, 0.94);
            };
            SourceInitialized += delegate
            {
                var handle = new WindowInteropHelper(this).Handle;
                WindowsNative.PrepareOverlay(handle);
                Reposition();
            };
            Microsoft.Win32.SystemEvents.DisplaySettingsChanged += delegate { Dispatcher.BeginInvoke(new Action(Reposition)); };
            Loaded += delegate { Reposition(); };
        }

        void Enter()
        {
            Animate(1.12, 1);
            shelf.SetHookHover(true);
            if (store.State.RevealOnTopHover) shelf.Reveal(true, false, 0);
        }

        void Animate(double scale, double opacity)
        {
            var duration = TimeSpan.FromMilliseconds(140);
            grow.BeginAnimation(ScaleTransform.ScaleXProperty, new DoubleAnimation(scale, duration));
            grow.BeginAnimation(ScaleTransform.ScaleYProperty, new DoubleAnimation(scale, duration));
            halo.BeginAnimation(OpacityProperty, new DoubleAnimation(opacity, duration));
        }

        void Reposition()
        {
            try
            {
                var screen = System.Windows.Forms.Screen.PrimaryScreen;
                double scale = WindowsNative.MonitorScale(screen);
                // 用 WPF 的逻辑坐标定位，系统会按屏幕缩放换算成物理像素，避免顶部中央跑偏。
                Left = screen.Bounds.Left / scale + (screen.Bounds.Width / scale - Width) / 2;
                Top = screen.Bounds.Top / scale;
            }
            catch { }
        }
    }
}
