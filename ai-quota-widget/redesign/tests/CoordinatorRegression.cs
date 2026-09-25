using System;
using System.Collections.Generic;
using System.Threading;

namespace QuotaWidget
{
    internal static class CoordinatorRegression
    {
        sealed class Harness : IDisposable
        {
            public DateTime Now = new DateTime(2026, 9, 25, 0, 0, 0, DateTimeKind.Utc);
            public readonly List<Action> Workers = new List<Action>();
            public readonly Queue<Action> Completions = new Queue<Action>();
            public readonly List<AccountRequest> Requests = new List<AccountRequest>();
            public readonly RefreshCoordinator Coordinator;
            public Func<AccountRequest, FetchResult> Result;
            public int Changes;

            public Harness(AppConfig config)
            {
                Result = delegate { return Success(25); };
                Coordinator = new RefreshCoordinator(delegate(AccountRequest request, CancellationToken cancellation)
                    {
                        Requests.Add(request);
                        return Result(request);
                    }, delegate { return Now; }, delegate(Action action) { Completions.Enqueue(action); },
                    delegate { Changes++; }, delegate(Action action) { Workers.Add(action); });
                Coordinator.Reconcile(config);
            }

            public void RunWorker(int index)
            {
                Action work = Workers[index];
                Workers.RemoveAt(index);
                work();
            }

            public void Pump()
            {
                while (Completions.Count > 0) Completions.Dequeue()();
            }

            public void FinishOne() { RunWorker(0); Pump(); }
            public void Dispose()
            {
                Coordinator.Dispose();
                while (Workers.Count > 0) RunWorker(0);
                Pump();
            }
        }

        static AppConfig Config(int count)
        {
            AppConfig config = new AppConfig();
            config.Codex.Enabled = config.DeepSeek.Enabled = false;
            for (int i = 0; i < count; i++) config.Zhipu.Add(new ZhipuCfg
                { Id = "test-" + i, Name = "Account " + i, ApiKey = "synthetic-" + i });
            return config;
        }

        static FetchResult Success(double percent)
        {
            return new FetchResult { Ok = true, StatusCode = 200, Windows = new List<QuotaWindow>
                { new QuotaWindow { Kind = WindowKind.FiveHour, UsedPercent = percent } } };
        }

        public static void Run(Action<string, bool, string> check)
        {
            TestSingleFlightAndAppearance(check);
            TestCredentialsAndLateCompletion(check);
            TestHideDeleteAndExit(check);
            TestRateLimitAndInterval(check);
            TestIdentityAndCancellation(check);
            TestBlockedWorker(check);
        }

        static void TestSingleFlightAndAppearance(Action<string, bool, string> check)
        {
            AppConfig config = Config(2);
            using (Harness h = new Harness(config))
            {
                AccountState first = h.Coordinator.Accounts[0];
                AccountState second = h.Coordinator.Accounts[1];
                check("coordinator: reconcile alone does not request", h.Workers.Count == 0, null);
                h.Coordinator.RefreshDue();
                for (int i = 0; i < 20; i++) h.Coordinator.RefreshNow();
                check("coordinator: repeated refresh coalesces per account", h.Workers.Count == 2 && first.Fetching && second.Fetching, null);
                config.Zhipu[0].Name = "Renamed";
                config.Ui.TopMost = false;
                config.Ui.Left = 999;
                config.Ui.Top = 400;
                h.Coordinator.Reconcile(config);
                h.Coordinator.RefreshDue();
                check("coordinator: appearance changes preserve in-flight state", object.ReferenceEquals(first, h.Coordinator.Accounts[0]) &&
                    first.Name == "Renamed" && first.Fetching && h.Workers.Count == 2, null);
                h.RunWorker(1);
                h.Pump();
                check("coordinator: another account finishes independently", first.Fetching && !second.Fetching && second.Windows.Count == 1, null);
                h.FinishOne();
                check("coordinator: coalesced clicks leave no trailing requests", h.Workers.Count == 0 && h.Requests.Count == 2, null);
                DateTime originalDue = first.NextDue;
                config.Zhipu.Reverse();
                h.Coordinator.Reconcile(config);
                h.Coordinator.RefreshDue();
                check("coordinator: reorder follows stable account identity", object.ReferenceEquals(first, h.Coordinator.Accounts[1]) &&
                    object.ReferenceEquals(second, h.Coordinator.Accounts[0]) && first.NextDue == originalDue && first.Windows.Count == 1 && h.Workers.Count == 0, null);
                h.Coordinator.RefreshNow(first.Key);
                check("coordinator: manual request bypasses ordinary wait only for selected account", h.Workers.Count == 1 && first.Fetching && !second.Fetching, null);
                h.FinishOne();
                h.Now = first.NextDue.AddTicks(-1);
                h.Coordinator.RefreshDue();
                check("coordinator: timer respects due boundary", h.Workers.Count == 0, null);
                h.Now = first.NextDue;
                h.Coordinator.RefreshDue();
                check("coordinator: timer starts on exact due time", h.Workers.Count == 2, null);
                h.FinishOne();
                h.FinishOne();
            }
        }

        static void TestCredentialsAndLateCompletion(Action<string, bool, string> check)
        {
            AppConfig config = Config(1);
            using (Harness h = new Harness(config))
            {
                AccountState state = h.Coordinator.Accounts[0];
                h.Coordinator.RefreshNow();
                h.FinishOne();
                h.Coordinator.RefreshNow();
                h.RunWorker(0); // Result exists, but UI completion has not run yet.
                config.Zhipu[0].ApiKey = "replacement-key";
                h.Coordinator.Reconcile(config);
                h.Coordinator.RefreshNow();
                check("coordinator: credential edit clears data and waits for old completion", state.Windows.Count == 0 &&
                    state.Fetching && h.Workers.Count == 0, null);
                h.Pump();
                check("coordinator: obsolete success cannot overwrite replacement credentials", state.Windows.Count == 0 &&
                    state.Failures == 0 && h.Workers.Count == 1, null);
                h.Result = delegate { return Success(70); };
                h.FinishOne();
                check("coordinator: replacement snapshots new key and stores only new data", h.Requests[2].ApiKey == "replacement-key" &&
                    h.Requests[1].ApiKey == "synthetic-0" && state.Windows[0].UsedPercent == 70, null);
                h.Coordinator.RefreshNow();
                config.ZaiAuthorization = "bearer";
                h.Coordinator.Reconcile(config);
                h.Coordinator.RefreshNow();
                check("coordinator: authorization scheme edit also cancels and clears cache", state.Windows.Count == 0 && h.Workers.Count == 1, null);
                h.FinishOne(); // Canceled before execution, starts one replacement.
                check("coordinator: canceled queued work does not call provider", h.Requests.Count == 3 && h.Workers.Count == 1, null);
                h.FinishOne();
                check("coordinator: new authorization scheme reaches immutable request", h.Requests[3].AuthorizationScheme == "bearer", null);
            }
        }

        static void TestHideDeleteAndExit(Action<string, bool, string> check)
        {
            AppConfig config = Config(1);
            using (Harness h = new Harness(config))
            {
                AccountState state = h.Coordinator.Accounts[0];
                h.Coordinator.RefreshDue();
                config.Zhipu[0].Visible = false;
                h.Coordinator.Reconcile(config);
                h.FinishOne();
                check("coordinator: hide allows existing request to complete", state.Windows.Count == 1 && h.Requests.Count == 1, null);
                h.Now = state.NextDue.AddSeconds(1);
                h.Coordinator.RefreshDue();
                h.Coordinator.RefreshNow();
                check("coordinator: hidden account suppresses timer and manual requests", h.Workers.Count == 0, null);
                config.Zhipu[0].Visible = true;
                h.Coordinator.Reconcile(config);
                h.Coordinator.RefreshDue();
                check("coordinator: overdue shown account resumes", h.Workers.Count == 1, null);
                h.FinishOne();
                config.Zhipu[0].Visible = false;
                h.Coordinator.Reconcile(config);
                config.Zhipu[0].Visible = true;
                h.Coordinator.Reconcile(config);
                h.Coordinator.RefreshDue();
                check("coordinator: recently refreshed shown account keeps normal due time", h.Workers.Count == 0, null);
                h.Coordinator.RefreshNow();
                h.RunWorker(0);
                ZhipuCfg removed = config.Zhipu[0];
                config.Zhipu.Clear();
                h.Coordinator.Reconcile(config);
                check("coordinator: removed account disappears immediately", h.Coordinator.Accounts.Count == 0, null);
                config.Zhipu.Add(removed);
                h.Coordinator.Reconcile(config);
                AccountState replacement = h.Coordinator.Accounts[0];
                h.Coordinator.RefreshNow();
                check("coordinator: readding ID waits for its retired request slot", !object.ReferenceEquals(state, replacement) && h.Workers.Count == 0, null);
                h.Pump();
                check("coordinator: removed generation is ignored after readd", replacement.Windows.Count == 0 && h.Workers.Count == 1, null);
                h.FinishOne();
                h.Coordinator.RefreshNow();
                h.RunWorker(0);
                config.Zhipu.Clear();
                h.Coordinator.Reconcile(config);
                h.Pump();
                check("coordinator: deleted late result cannot restore account", h.Coordinator.Accounts.Count == 0 && h.Workers.Count == 0, null);
                config.Zhipu.Add(removed);
                h.Coordinator.Reconcile(config);
                h.Coordinator.RefreshNow();
                h.RunWorker(0);
                AccountState exiting = h.Coordinator.Accounts[0];
                int beforeDispose = h.Changes;
                h.Coordinator.Dispose();
                h.Pump();
                h.Coordinator.RefreshDue();
                h.Coordinator.RefreshNow();
                check("coordinator: exit ignores results and further refresh calls", exiting.Windows.Count == 0 &&
                    h.Workers.Count == 0 && h.Changes == beforeDispose, null);
            }
        }

        static void TestRateLimitAndInterval(Action<string, bool, string> check)
        {
            check("policy: rate-limit never shortens long interval", RefreshPolicy.DelaySeconds(3600, 429, 1) == 3600 &&
                RefreshPolicy.DelaySeconds(900, 429, 1) >= 900, null);
            AppConfig config = Config(2);
            using (Harness h = new Harness(config))
            {
                AccountState first = h.Coordinator.Accounts[0];
                DateTime completed = h.Now;
                h.Result = delegate(AccountRequest request) { return request.Key == first.Key ?
                    new FetchResult { StatusCode = 429, Error = "限流", RetryAfterUtc = completed.AddSeconds(120) } : Success(25); };
                h.Coordinator.RefreshNow();
                h.FinishOne();
                h.FinishOne();
                check("coordinator: server retry-after extends local cooldown", first.CooldownUntil == completed.AddSeconds(120) &&
                    first.NextDue == first.CooldownUntil, null);
                config.RefreshIntervalSeconds = 30;
                h.Coordinator.Reconcile(config);
                h.Coordinator.RefreshDue();
                check("coordinator: interval adjustment preserves rate-limit floor", first.NextDue == completed.AddSeconds(120) &&
                    h.Coordinator.Accounts[1].NextDue == completed.AddSeconds(30) && h.Workers.Count == 0, null);
                h.Now = completed.AddSeconds(119);
                h.Coordinator.RefreshNow();
                check("coordinator: manual refresh cannot bypass cooldown but other account refreshes", h.Workers.Count == 1 && !first.Fetching, null);
                h.FinishOne();
                h.Now = completed.AddSeconds(120);
                h.Result = delegate { return Success(55); };
                h.Coordinator.RefreshDue();
                check("coordinator: request resumes at exact cooldown boundary", first.Fetching && h.Workers.Count == 1, null);
                h.FinishOne();
                check("coordinator: recovery clears error and resumes normal cadence", first.Error == null && first.Failures == 0 &&
                    first.CooldownUntil == DateTime.MinValue && first.NextDue == h.Now.AddSeconds(30), null);
                config.RefreshIntervalSeconds = 3600;
                h.Coordinator.Reconcile(config);
                check("coordinator: longer interval recomputes from completion time", first.NextDue == first.LastCompletedUtc.AddSeconds(3600), null);
                h.Result = delegate { return new FetchResult { StatusCode = 429, Error = "限流" }; };
                h.Coordinator.RefreshNow(first.Key);
                h.FinishOne();
                check("coordinator: hourly account cooldown remains at least an hour", first.CooldownUntil == h.Now.AddSeconds(3600), null);
                config.RefreshIntervalSeconds = 10;
                h.Coordinator.Reconcile(config);
                h.Coordinator.RefreshNow(first.Key);
                check("coordinator: shrinking interval cannot erase existing cooldown", first.NextDue == first.CooldownUntil && h.Workers.Count == 0, null);
            }
        }

        static void TestIdentityAndCancellation(Action<string, bool, string> check)
        {
            DateTime now = new DateTime(2026, 9, 25, 0, 0, 0, DateTimeKind.Utc);
            AccountState state = new AccountState { Provider = "codex" };
            FetchResult first = Success(30);
            first.AccountIdentity = "account-a";
            state.Apply(first, now.ToLocalTime(), now, 10);
            state.Apply(new FetchResult { StatusCode = 401, Error = "请重新登录", RequiresLogin = true,
                AccountIdentity = "account-b" }, now.ToLocalTime(), now.AddSeconds(10), 10);
            check("state: account switch clears former quota even on failure", state.Windows.Count == 0 &&
                state.LastSuccess == DateTime.MinValue && state.AccountIdentity == "account-b" && state.RequiresLogin && !state.Stale, null);
            FetchResult recovered = Success(65);
            recovered.AccountIdentity = "account-b";
            state.Apply(recovered, now.ToLocalTime(), now.AddSeconds(20), 10);
            check("state: login recovery clears requires-login status", !state.RequiresLogin && state.Error == null && state.Windows.Count == 1, null);
            DateTime previousCompletion = state.LastCompletedUtc;
            DateTime previousDue = state.NextDue;
            state.Fetching = true;
            state.Apply(new FetchResult { Canceled = true }, now.ToLocalTime(), now.AddSeconds(30), 10);
            check("state: cancellation does not alter failure or data clocks", state.Failures == 0 && state.Error == null &&
                !state.Fetching && state.Windows.Count == 1 && state.LastCompletedUtc == previousCompletion && state.NextDue == previousDue, null);
            state.Apply(new FetchResult { StatusCode = 503, Error = "暂不可用", AccountIdentity = "account-b" },
                now.ToLocalTime(), now.AddSeconds(40), 10);
            check("state: same-account failure retains data visibly stale", state.Windows.Count == 1 && state.Stale && state.Failures == 1, null);
            FetchResult limited = Success(100);
            limited.StatusCode = 429;
            limited.Stale = true;
            state.Apply(limited, now.ToLocalTime(), now.AddSeconds(50), 10);
            check("state: parsed rate-limit quota still enforces cooldown", state.CooldownUntil == now.AddSeconds(110) && state.Stale, null);

            AppConfig config = Config(1);
            using (Harness h = new Harness(config))
            {
                h.Result = delegate { throw new InvalidOperationException("secret-response-marker"); };
                h.Coordinator.RefreshNow();
                h.FinishOne();
                AccountState failed = h.Coordinator.Accounts[0];
                check("coordinator: unexpected exceptions report sanitized service error", failed.Error.Contains("智谱") &&
                    !failed.Error.Contains("secret-response-marker") && failed.Failures == 1 && !failed.Fetching, null);
            }
        }

        static void TestBlockedWorker(Action<string, bool, string> check)
        {
            AppConfig config = Config(2);
            DateTime now = new DateTime(2026, 9, 25, 0, 0, 0, DateTimeKind.Utc);
            ManualResetEvent blockedStarted = new ManualResetEvent(false);
            ManualResetEvent releaseBlocked = new ManualResetEvent(false);
            ManualResetEvent independentFinished = new ManualResetEvent(false);
            Queue<Action> ui = new Queue<Action>();
            int activeFirst = 0, maxActiveFirst = 0, firstCalls = 0;
            bool oldCancellationSeen = false;
            RefreshCoordinator coordinator = new RefreshCoordinator(delegate(AccountRequest request, CancellationToken cancellation)
                {
                    if (request.Key == "zhipu:test-1")
                    {
                        independentFinished.Set();
                        return Success(15);
                    }
                    int active = Interlocked.Increment(ref activeFirst);
                    if (active > maxActiveFirst) maxActiveFirst = active;
                    int number = Interlocked.Increment(ref firstCalls);
                    try
                    {
                        if (number == 1)
                        {
                            blockedStarted.Set();
                            releaseBlocked.WaitOne(5000);
                            oldCancellationSeen = cancellation.IsCancellationRequested;
                        }
                        return Success(number == 1 ? 10 : 80);
                    }
                    finally { Interlocked.Decrement(ref activeFirst); }
                }, delegate { return now; }, delegate(Action action) { lock (ui) ui.Enqueue(action); }, delegate { });
            try
            {
                coordinator.Reconcile(config);
                coordinator.RefreshNow();
                bool started = blockedStarted.WaitOne(5000);
                bool independent = independentFinished.WaitOne(5000);
                check("coordinator: blocked provider does not block another worker", started && independent, null);
                config.Zhipu[0].ApiKey = "new-blocked-key";
                coordinator.Reconcile(config);
                for (int i = 0; i < 10; i++) coordinator.RefreshNow("zhipu:test-0");
                check("coordinator: canceled running request retains sole request slot", firstCalls == 1 && activeFirst == 1, null);
                releaseBlocked.Set();
                bool finished = PumpUntil(ui, delegate { return firstCalls == 2 && !coordinator.Accounts[0].Fetching; }, 5000);
                check("coordinator: replacement begins only after blocked worker leaves", finished && oldCancellationSeen && maxActiveFirst == 1, null);
                check("coordinator: canceled result ignored and replacement applies", coordinator.Accounts[0].Windows.Count == 1 &&
                    coordinator.Accounts[0].Windows[0].UsedPercent == 80 && coordinator.Accounts[0].Failures == 0, null);
            }
            finally
            {
                releaseBlocked.Set();
                coordinator.Dispose();
                PumpUntil(ui, delegate { return Interlocked.CompareExchange(ref activeFirst, 0, 0) == 0; }, 5000);
                blockedStarted.Dispose();
                releaseBlocked.Dispose();
                independentFinished.Dispose();
            }
        }

        static bool PumpUntil(Queue<Action> ui, Func<bool> completed, int timeoutMilliseconds)
        {
            System.Diagnostics.Stopwatch watch = System.Diagnostics.Stopwatch.StartNew();
            do
            {
                Action action = null;
                lock (ui) { if (ui.Count > 0) action = ui.Dequeue(); }
                if (action != null) action();
                else Thread.Sleep(1);
                if (completed()) return true;
            }
            while (watch.ElapsedMilliseconds < timeoutMilliseconds);
            return false;
        }
    }
}
