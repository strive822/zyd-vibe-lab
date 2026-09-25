using System;
using System.Collections.Generic;

namespace QuotaWidget
{
    public sealed class AccountState
    {
        public string Key, Name, Provider, ApiKey, AuthJsonPath, AuthorizationScheme, Error, Warning, AccountIdentity;
        public bool Visible = true, IsBalance, Stale, Fetching, RequiresLogin;
        public List<QuotaWindow> Windows = new List<QuotaWindow>();
        public List<BalanceData> Balances = new List<BalanceData>();
        public DateTime LastSuccess = DateTime.MinValue;
        public DateTime LastCompletedUtc = DateTime.MinValue;
        public DateTime NextDue = DateTime.MinValue;
        public DateTime CooldownUntil = DateTime.MinValue;
        public int Failures;

        internal void ClearData()
        {
            Windows = new List<QuotaWindow>();
            Balances = new List<BalanceData>();
            Error = Warning = AccountIdentity = null;
            Stale = RequiresLogin = false;
            LastSuccess = LastCompletedUtc = NextDue = CooldownUntil = DateTime.MinValue;
            Failures = 0;
        }

        public void Apply(FetchResult result, DateTime localNow, DateTime utcNow, int intervalSeconds)
        {
            Fetching = false;
            if (result != null && result.Canceled) return;
            // A failed request can still identify a newly selected Codex account. Never
            // show the former account's last good data under that new identity.
            if (result != null && !string.IsNullOrEmpty(result.AccountIdentity))
            {
                if (!string.Equals(AccountIdentity, result.AccountIdentity, StringComparison.Ordinal)) ClearData();
                AccountIdentity = result.AccountIdentity;
            }
            LastCompletedUtc = utcNow;
            RequiresLogin = result != null && result.RequiresLogin;
            if (result != null && result.Ok)
            {
                Windows = result.Windows ?? new List<QuotaWindow>();
                Balances = result.Balances ?? new List<BalanceData>();
                if (IsBalance && Balances.Count == 0 && result.Balance != null) Balances.Add(result.Balance);
                Warning = result.Warning;
                Error = null;
                Stale = result.Stale;
                LastSuccess = localNow;
                Failures = 0;
            }
            else
            {
                Failures++;
                Error = result == null || string.IsNullOrEmpty(result.Error) ? "请求失败" : Providers.Truncate(result.Error, 100);
                Stale = Windows.Count > 0 || Balances.Count > 0;
            }
            NextDue = utcNow.AddSeconds(RefreshPolicy.DelaySeconds(intervalSeconds,
                result == null ? 0 : result.StatusCode, Failures));
            if (result != null && result.StatusCode == 429)
            {
                CooldownUntil = NextDue;
                if (result.RetryAfterUtc.HasValue && result.RetryAfterUtc.Value > CooldownUntil)
                    CooldownUntil = result.RetryAfterUtc.Value;
                NextDue = CooldownUntil;
            }
            else CooldownUntil = DateTime.MinValue;
        }
    }
}
