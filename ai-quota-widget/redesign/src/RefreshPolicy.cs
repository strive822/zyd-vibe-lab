using System;

namespace QuotaWidget
{
    public static class RefreshPolicy
    {
        // Each account has its own due time. A failed provider does not delay the others.
        public static int DelaySeconds(int configuredSeconds, int statusCode, int consecutiveFailures)
        {
            int normal = Math.Max(10, Math.Min(3600, configuredSeconds));
            // The cap limits additional backoff, never the user's normal interval.
            if (statusCode == 429) return Math.Max(normal, Math.Max(60, Math.Min(600, normal * 6)));
            if (consecutiveFailures <= 0) return normal;
            int exponent = Math.Min(5, consecutiveFailures - 1);
            int backoff = 10 << exponent;
            return Math.Max(normal, Math.Min(300, backoff));
        }
    }
}
