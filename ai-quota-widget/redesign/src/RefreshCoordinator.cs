using System;
using System.Collections.Generic;
using System.Threading;

namespace QuotaWidget
{
    // Immutable worker input: an in-flight request never reads a mutable config/state.
    public sealed class AccountRequest
    {
        public readonly string Key, Provider, ApiKey, AuthJsonPath, AuthorizationScheme;

        public AccountRequest(string key, string provider, string apiKey, string authJsonPath, string authorizationScheme)
        {
            Key = key;
            Provider = provider;
            ApiKey = apiKey;
            AuthJsonPath = authJsonPath;
            AuthorizationScheme = authorizationScheme;
        }

        internal bool SameParameters(AccountRequest other)
        {
            return other != null && Key == other.Key && Provider == other.Provider &&
                ApiKey == other.ApiKey && AuthJsonPath == other.AuthJsonPath &&
                AuthorizationScheme == other.AuthorizationScheme;
        }
    }

    // All public methods and dispatched completions run on the owner (UI) thread.
    // Only fetch runs on a worker. dispatch must marshal its action to that owner.
    public sealed class RefreshCoordinator : IDisposable
    {
        sealed class Entry
        {
            public AccountState State;
            public AccountRequest Request;
            public long Generation;
            public bool Active, Wanted, InFlight, RestartWhenAvailable;
            public CancellationTokenSource Cancellation;
        }

        readonly Dictionary<string, Entry> _entries = new Dictionary<string, Entry>(StringComparer.Ordinal);
        readonly List<AccountState> _accounts = new List<AccountState>();
        readonly IList<AccountState> _view;
        readonly Func<AccountRequest, CancellationToken, FetchResult> _fetch;
        readonly Func<DateTime> _utcNow;
        readonly Action<Action> _dispatch, _queueWork;
        readonly Action _changed;
        int _intervalSeconds = 10;
        bool _disposed;

        public RefreshCoordinator(Func<AccountRequest, CancellationToken, FetchResult> fetch,
            Func<DateTime> utcNow, Action<Action> dispatch, Action changed)
            : this(fetch, utcNow, dispatch, changed,
                delegate(Action work) { ThreadPool.QueueUserWorkItem(delegate { work(); }); }) { }

        public RefreshCoordinator(Func<AccountRequest, CancellationToken, FetchResult> fetch,
            Func<DateTime> utcNow, Action<Action> dispatch, Action changed, Action<Action> queueWork)
        {
            if (fetch == null) throw new ArgumentNullException("fetch");
            if (utcNow == null) throw new ArgumentNullException("utcNow");
            if (dispatch == null) throw new ArgumentNullException("dispatch");
            if (queueWork == null) throw new ArgumentNullException("queueWork");
            _fetch = fetch;
            _utcNow = utcNow;
            _dispatch = dispatch;
            _changed = changed;
            _queueWork = queueWork;
            _view = _accounts.AsReadOnly();
        }

        public IList<AccountState> Accounts { get { return _view; } }

        public static FetchResult FetchProvider(AccountRequest request, CancellationToken cancellation)
        {
            if (request.Provider == "codex") return Providers.FetchCodex(request.AuthJsonPath, cancellation);
            if (request.Provider == "zhipu") return Providers.FetchZhipu(request.ApiKey, request.AuthorizationScheme, cancellation);
            if (request.Provider == "deepseek") return Providers.FetchDeepSeek(request.ApiKey, cancellation);
            return new FetchResult { Error = "未知服务类型" };
        }

        public void Reconcile(AppConfig config)
        {
            if (_disposed) return;
            if (config == null) throw new ArgumentNullException("config");
            int interval = Math.Max(10, Math.Min(3600, config.RefreshIntervalSeconds));
            bool intervalChanged = interval != _intervalSeconds;
            _intervalSeconds = interval;
            foreach (Entry entry in _entries.Values) entry.Wanted = false;
            _accounts.Clear();
            if (config.Codex.Enabled)
                Include(new AccountRequest("codex", "codex", null, config.Codex.AuthJsonPath, null),
                    config.Codex.Name, config.Codex.Visible, false, intervalChanged);
            HashSet<string> ids = new HashSet<string>(StringComparer.Ordinal);
            for (int i = 0; i < config.Zhipu.Count; i++)
            {
                ZhipuCfg account = config.Zhipu[i];
                // Config loading normally does this; keep programmatic configs safe too.
                if (string.IsNullOrWhiteSpace(account.Id) || !ids.Add(account.Id))
                {
                    do { account.Id = Guid.NewGuid().ToString("N"); } while (!ids.Add(account.Id));
                }
                Include(new AccountRequest("zhipu:" + account.Id, "zhipu", account.ApiKey, null, config.ZaiAuthorization),
                    AppConfig.ZhipuDisplayName(account, i), account.Visible, false, intervalChanged);
            }
            if (config.DeepSeek.Enabled)
                Include(new AccountRequest("deepseek", "deepseek", config.DeepSeek.ApiKey, null, null),
                    config.DeepSeek.Name, config.DeepSeek.Visible, true, intervalChanged);

            List<string> removed = new List<string>();
            foreach (KeyValuePair<string, Entry> pair in _entries)
            {
                Entry entry = pair.Value;
                if (entry.Wanted) continue;
                if (entry.Active)
                {
                    entry.Active = false;
                    entry.Generation++;
                    entry.RestartWhenAvailable = false;
                    Cancel(entry);
                }
                // Keep a tombstone until the actual worker exits, so removing/readding
                // an ID cannot open a second request slot for that same account.
                if (!entry.InFlight) removed.Add(pair.Key);
            }
            foreach (string key in removed) _entries.Remove(key);
            NotifyChanged();
        }

        void Include(AccountRequest request, string name, bool visible, bool balance, bool intervalChanged)
        {
            Entry entry;
            if (!_entries.TryGetValue(request.Key, out entry))
            {
                entry = new Entry();
                _entries.Add(request.Key, entry);
            }
            bool newAccount = !entry.Active;
            bool parametersChanged = !request.SameParameters(entry.Request);
            if (newAccount)
            {
                entry.State = new AccountState();
                entry.Generation++;
            }
            else if (parametersChanged)
            {
                entry.State.ClearData();
                entry.Generation++;
            }
            if (newAccount || parametersChanged)
            {
                entry.RestartWhenAvailable = entry.InFlight;
                Cancel(entry);
            }
            entry.Request = request;
            entry.Active = entry.Wanted = true;
            AccountState state = entry.State;
            state.Key = request.Key;
            state.Provider = request.Provider;
            state.ApiKey = request.ApiKey;
            state.AuthJsonPath = request.AuthJsonPath;
            state.AuthorizationScheme = request.AuthorizationScheme;
            state.Name = string.IsNullOrWhiteSpace(name) ? request.Provider : name;
            state.Visible = visible;
            state.IsBalance = balance;
            state.Fetching = entry.InFlight;
            if (intervalChanged && !newAccount && !parametersChanged)
            {
                state.NextDue = state.LastCompletedUtc == DateTime.MinValue ? DateTime.MinValue
                    : state.LastCompletedUtc.AddSeconds(_intervalSeconds);
                if (state.CooldownUntil > state.NextDue) state.NextDue = state.CooldownUntil;
            }
            _accounts.Add(state);
        }

        public void RefreshDue()
        {
            if (_disposed) return;
            foreach (AccountState state in _accounts) TryStart(_entries[state.Key], false);
        }

        public void RefreshNow()
        {
            if (_disposed) return;
            foreach (AccountState state in _accounts) TryStart(_entries[state.Key], true);
        }

        public void RefreshNow(string key)
        {
            if (_disposed || key == null) return;
            Entry entry;
            if (_entries.TryGetValue(key, out entry)) TryStart(entry, true);
        }

        void TryStart(Entry entry, bool manual)
        {
            if (_disposed || !entry.Active || !entry.State.Visible || entry.InFlight) return;
            DateTime now = _utcNow();
            if (now < entry.State.CooldownUntil || (!manual && now < entry.State.NextDue)) return;
            entry.InFlight = entry.State.Fetching = true;
            entry.RestartWhenAvailable = false;
            CancellationTokenSource cancellation = new CancellationTokenSource();
            entry.Cancellation = cancellation;
            long generation = entry.Generation;
            AccountRequest request = entry.Request;
            NotifyChanged();
            try
            {
                _queueWork(delegate
                {
                    FetchResult result;
                    try
                    {
                        cancellation.Token.ThrowIfCancellationRequested();
                        result = _fetch(request, cancellation.Token);
                        if (cancellation.IsCancellationRequested) result = new FetchResult { Canceled = true };
                    }
                    catch (OperationCanceledException) { result = new FetchResult { Canceled = true }; }
                    catch { result = new FetchResult { Error = ProviderName(request.Provider) + "请求失败，请稍后重试" }; }
                    finally { cancellation.Dispose(); }
                    // A destroyed form may reject a final marshal. The worker and its
                    // token source are already released; no state is touched off-thread.
                    try { _dispatch(delegate { Complete(entry, generation, result); }); }
                    catch (ObjectDisposedException) { }
                    catch (InvalidOperationException) { }
                });
            }
            catch
            {
                cancellation.Dispose();
                Complete(entry, generation, new FetchResult { Error = ProviderName(request.Provider) + "无法启动刷新，请稍后重试" });
            }
        }

        void Complete(Entry entry, long generation, FetchResult result)
        {
            entry.InFlight = false;
            entry.Cancellation = null;
            entry.State.Fetching = false;
            if (_disposed) return;
            if (!entry.Active)
            {
                _entries.Remove(entry.Request.Key);
                return;
            }
            if (entry.Generation == generation)
            {
                DateTime now = _utcNow();
                entry.State.Apply(result, now.ToLocalTime(), now, _intervalSeconds);
            }
            NotifyChanged();
            if (entry.RestartWhenAvailable) TryStart(entry, false);
        }

        static string ProviderName(string provider)
        {
            return provider == "codex" ? "Codex " : provider == "zhipu" ? "智谱 " : provider == "deepseek" ? "DeepSeek " : "服务";
        }

        static void Cancel(Entry entry)
        {
            if (entry.Cancellation == null) return;
            try { entry.Cancellation.Cancel(); }
            catch (ObjectDisposedException) { }
        }

        void NotifyChanged() { if (_changed != null && !_disposed) _changed(); }

        public void Dispose()
        {
            if (_disposed) return;
            _disposed = true;
            foreach (Entry entry in _entries.Values)
            {
                entry.Active = false;
                entry.Generation++;
                entry.RestartWhenAvailable = false;
                Cancel(entry);
            }
        }
    }
}
