param([string]$in)
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Text;
using System.Drawing;
using System.Collections.Generic;
public class HX {
  public static string Scan(string path) {
    using (var b = new Bitmap(path)) {
      var counts = new Dictionary<string, int>();
      for (int y = 0; y < b.Height; y++) {
        for (int x = 0; x < b.Width; x++) {
          Color c = b.GetPixel(x, y);
          if (c.A < 200) continue;
          if (c.R < 120 && c.G < 120 && c.B < 120) continue;
          if (Math.Abs(c.R - c.G) < 30 && Math.Abs(c.G - c.B) < 30) continue;
          string key = "#" + c.R.ToString("X2") + c.G.ToString("X2") + c.B.ToString("X2");
          int n;
          counts.TryGetValue(key, out n);
          counts[key] = n + 1;
        }
      }
      var list = new List<KeyValuePair<string, int>>(counts);
      list.Sort(delegate(KeyValuePair<string, int> a, KeyValuePair<string, int> b2) { return b2.Value - a.Value; });
      var outp = new StringBuilder();
      int shown = 0;
      foreach (KeyValuePair<string, int> kv in list) {
        if (shown >= 8) break;
        outp.Append(kv.Key).Append(" x").Append(kv.Value).Append("  ");
        shown++;
      }
      return outp.ToString();
    }
  }
}
'@
Write-Output ([HX]::Scan($in))
