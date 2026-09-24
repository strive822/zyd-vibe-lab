param(
    [string]$in,
    [string]$out,
    [int]$x = 0,
    [int]$y = 0,
    [int]$w = 0,
    [int]$h = 0,
    [int]$zoom = 3
)
# 裁剪放大工具：crop.ps1 -in 输入.png -out 输出.png -x -y -w -h(裁剪区,0=全图) -zoom 放大倍数
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Drawing2D;
public class CR {
  public static void Crop(string inp, string outp, int x, int y, int w, int h, int zoom) {
    using (var src = new Bitmap(inp)) {
      if (w <= 0) w = src.Width;
      if (h <= 0) h = src.Height;
      if (x + w > src.Width) w = src.Width - x;
      if (y + h > src.Height) h = src.Height - y;
      using (var dst = new Bitmap(w * zoom, h * zoom)) {
        using (var g = Graphics.FromImage(dst)) {
          g.InterpolationMode = InterpolationMode.NearestNeighbor;
          g.PixelOffsetMode = PixelOffsetMode.Half;
          g.DrawImage(src, new Rectangle(0, 0, w * zoom, h * zoom), new Rectangle(x, y, w, h), GraphicsUnit.Pixel);
        }
        dst.Save(outp);
      }
    }
  }
}
'@
[CR]::Crop($in, $out, $x, $y, $w, $h, $zoom)
Write-Output ("cropped " + $w + "x" + $h + " at " + $x + "," + $y + " zoom=" + $zoom + " -> " + $out)
