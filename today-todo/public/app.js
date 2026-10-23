'use strict';

/**
 * 今日待办 · 前端
 * 服务端是唯一数据源：所有改动发给服务端，再按 version 拉取。
 * 同步策略：操作后立即拉取 + 可见时 3 秒轮询 + 回到前台立即拉取。
 */

(function () {
  const POLL_MS = 3000;
  const MAX_FAILURES = 2;

  const el = {
    composer: document.getElementById('composer'),
    fab: document.getElementById('composer-fab'),
    panel: document.getElementById('composer-panel'),
    input: document.getElementById('new-task'),
    submit: document.getElementById('composer-submit'),
    cancel: document.getElementById('composer-cancel'),
    msg: document.getElementById('form-msg'),
    tasks: document.getElementById('tasks'),
    listNote: document.getElementById('list-note'),
    empty: document.getElementById('empty'),
    loading: document.getElementById('loading'),
    count: document.getElementById('count'),
    today: document.getElementById('today'),
    syncState: document.getElementById('sync-state'),
    offline: document.getElementById('offline'),
    retry: document.getElementById('retry'),
    undo: document.getElementById('undo'),
    undoBtn: document.getElementById('undo-btn'),
    undoClose: document.getElementById('undo-close'),
    announcer: document.getElementById('announcer'),
  };

  const MORPH_MS = 480;

  const state = { version: -1, items: [], doneTtlHours: 24 };

  let busy = false;
  let refreshing = false;
  let failures = 0;
  let pollTimer = null;
  let msgTimer = null;
  let pendingUndo = null;
  let editing = null;      // { id, original }，编辑中不做整表重绘

  /* ------------------------------------------------------------ 网络 */

  async function request(path, options) {
    const init = { cache: 'no-store' };
    if (options) {
      init.method = options.method || 'GET';
      if (options.body !== undefined) {
        init.headers = { 'Content-Type': 'application/json' };
        init.body = JSON.stringify(options.body);
      }
    }

    const res = await fetch(path, init);
    if (!res.ok) {
      let message = '请求失败（' + res.status + '）';
      try {
        const data = await res.json();
        if (data && data.error) message = data.error;
      } catch (_) { /* 非 JSON 错误体 */ }
      const err = new Error(message);
      err.status = res.status;
      throw err;
    }
    return res.status === 204 ? null : res.json();
  }

  const api = {
    list: () => request('/api/todos'),
    create: (text) => request('/api/todos', { method: 'POST', body: { text } }),
    setDone: (id, done) => request('/api/todos/' + id, { method: 'PATCH', body: { done } }),
    setText: (id, text) => request('/api/todos/' + id, { method: 'PATCH', body: { text } }),
    remove: (id) => request('/api/todos/' + id, { method: 'DELETE' }),
  };

  /* ------------------------------------------------------------ 渲染 */

  function remaining() {
    return state.items.reduce((sum, item) => sum + (item.done ? 0 : 1), 0);
  }

  function updateCount() {
    el.count.textContent = String(remaining());
  }

  function buildRow(item) {
    const li = document.createElement('li');
    li.className = 'task' + (item.done ? ' is-done' : '');
    li.dataset.id = item.id;

    const label = document.createElement('label');
    label.className = 'task-main';

    const box = document.createElement('input');
    box.type = 'checkbox';
    box.className = 'task-check';
    box.checked = item.done;
    box.setAttribute('aria-label', (item.done ? '取消完成：' : '标记完成：') + item.text);

    const text = document.createElement('span');
    text.className = 'task-text';
    text.textContent = item.text;

    label.append(box, text);

    const del = document.createElement('button');
    del.type = 'button';
    del.className = 'task-del';
    del.setAttribute('aria-label', '删除：' + item.text);
    del.innerHTML =
      '<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">' +
      '<path d="M2.5 2.5 13.5 13.5M13.5 2.5 2.5 13.5"/></svg>';

    const edit = document.createElement('button');
    edit.type = 'button';
    edit.className = 'task-edit';
    edit.dataset.action = 'edit';
    edit.setAttribute('aria-label', '编辑：' + item.text);
    edit.innerHTML =
      '<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">' +
      '<path d="M2.6 13.4 3.7 9.6 10.8 2.5 13.5 5.2 6.4 12.3 Z"/>' +
      '<path d="M9.4 3.9 12.1 6.6"/></svg>';

    li.append(label, edit, del);
    return li;
  }

  /** 编辑态整行替换：只留输入框和保存/取消，避免误触删除 */
  function buildEditRow(item) {
    const li = document.createElement('li');
    li.className = 'task is-editing';
    li.dataset.id = item.id;

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'task-edit-input';
    input.value = item.text;
    input.maxLength = 200;
    input.autocomplete = 'off';
    input.spellcheck = false;
    input.enterKeyHint = 'done';
    input.setAttribute('aria-label', '编辑任务内容');

    const save = document.createElement('button');
    save.type = 'button';
    save.className = 'task-save';
    save.textContent = '保存';

    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.className = 'task-cancel';
    cancel.textContent = '取消';

    const wrap = document.createElement('div');
    wrap.className = 'task-editor';
    wrap.append(input, save, cancel);

    li.append(wrap);
    return li;
  }

  /** 重绘前记住焦点在哪一行，重绘后放回去，避免轮询把键盘用户的位置冲掉。 */
  function captureFocus() {
    const active = document.activeElement;
    const row = active && active.closest ? active.closest('.task') : null;
    if (!row) return null;
    return {
      id: row.dataset.id,
      control: active.classList.contains('task-del') ? '.task-del' : '.task-check',
    };
  }

  function restoreFocus(saved) {
    if (!saved) return;
    const row = el.tasks.querySelector('[data-id="' + CSS.escape(saved.id) + '"]');
    if (row) {
      const target = row.querySelector(saved.control);
      if (target) {
        target.focus();
        return;
      }
    }
    el.input.focus();
  }

  function ttlLabel() {
    const hours = state.doneTtlHours;
    if (hours >= 1) return Math.round(hours * 10) / 10 + ' 小时';
    return Math.max(1, Math.round(hours * 60)) + ' 分钟';
  }

  function render() {
    const saved = captureFocus();
    const fragment = document.createDocumentFragment();
    for (const item of state.items) fragment.append(buildRow(item));

    el.tasks.replaceChildren(fragment);
    el.empty.hidden = state.items.length !== 0;
    el.loading.hidden = true;

    const hasDone = state.items.some((item) => item.done);
    el.listNote.hidden = !hasDone;
    if (hasDone) el.listNote.textContent = '已完成的会在 ' + ttlLabel() + '后自动清理';

    updateCount();
    restoreFocus(saved);
  }

  function apply(data) {
    state.version = data.version;
    state.items = Array.isArray(data.items) ? data.items : [];
    if (Number.isFinite(data.doneTtlHours)) state.doneTtlHours = data.doneTtlHours;
    render();
  }

  /* ------------------------------------------------------------ 编辑 */

  function focusAction(id, selector) {
    const row = el.tasks.querySelector('[data-id="' + CSS.escape(id) + '"]');
    const target = row ? row.querySelector(selector) : null;
    if (target) target.focus();
    else el.input.focus();
  }

  function startEdit(id) {
    if (editing) return;
    const row = el.tasks.querySelector('[data-id="' + CSS.escape(id) + '"]');
    const item = state.items.find((entry) => entry.id === id);
    if (!row || !item) return;

    editing = { id, original: item.text };
    row.replaceWith(buildEditRow(item));

    const input = el.tasks.querySelector('.task-edit-input');
    if (input) {
      input.focus();
      input.setSelectionRange(input.value.length, input.value.length);
    }
  }

  async function cancelEdit(id) {
    const item = state.items.find((entry) => entry.id === id);
    editing = null;
    if (item) {
      const row = el.tasks.querySelector('[data-id="' + CSS.escape(id) + '"]');
      if (row) row.replaceWith(buildRow(item));
    }
    focusAction(id, '.task-edit');
  }

  async function saveEdit(id) {
    const input = el.tasks.querySelector('.task-edit-input');
    if (!input) return;

    const text = input.value.trim();
    if (!text) {
      notify('任务内容不能为空', 'hint');
      input.focus();
      return;
    }
    if (editing && text === editing.original) {
      await cancelEdit(id);
      return;
    }

    input.disabled = true;
    try {
      await api.setText(id, text);
      editing = null;
      hideMsg();
      await refresh({ force: true });
      focusAction(id, '.task-edit');
    } catch (err) {
      input.disabled = false;
      notify(err.message || '保存失败，请重试', 'error');
      input.focus();
    }
  }

  /* ------------------------------------------------------------ 提示 */

  function notify(message, tone) {
    el.msg.textContent = message;
    el.msg.dataset.tone = tone === 'error' ? 'error' : 'hint';
    el.msg.hidden = false;
    clearTimeout(msgTimer);
    msgTimer = setTimeout(() => { el.msg.hidden = true; }, 3600);
  }

  function hideMsg() {
    el.msg.hidden = true;
    clearTimeout(msgTimer);
  }

  function markInvalid(invalid) {
    if (invalid) el.input.setAttribute('aria-invalid', 'true');
    else el.input.removeAttribute('aria-invalid');
  }

  function showOffline() {
    el.offline.hidden = false;
  }

  function hideOffline() {
    el.offline.hidden = true;
  }

  function stampSync() {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    el.syncState.textContent = '已同步 ' + pad(now.getHours()) + ':' + pad(now.getMinutes()) + ':' + pad(now.getSeconds());
  }

  /* ------------------------------------------------------------ 撤销 */

  function announce(message) {
    el.announcer.textContent = message;
  }

  function showUndo(item) {
    pendingUndo = { text: item.text, done: item.done };
    el.undo.hidden = false;
    document.body.classList.add('has-undo');
    announce('已删除「' + item.text + '」，可撤销');
  }

  function hideUndo() {
    pendingUndo = null;
    el.undo.hidden = true;
    document.body.classList.remove('has-undo');
  }

  async function undoDelete() {
    if (!pendingUndo) return;
    const { text, done } = pendingUndo;
    hideUndo();
    announce('已恢复「' + text + '」');
    try {
      const created = await api.create(text);
      if (done && created && created.item) await api.setDone(created.item.id, true);
      await refresh({ force: true });
    } catch (err) {
      notify('撤销失败，请重新添加：' + text, 'error');
    }
  }

  /* ------------------------------------------------------------ 同步 */

  async function refresh(options) {
    if (refreshing) return;
    refreshing = true;
    const force = Boolean(options && options.force);

    try {
      const data = await api.list();
      failures = 0;
      hideOffline();
      if (editing) {
        // 编辑中不重绘整张表，避免打断输入；保存或取消后会强制刷新
        el.loading.hidden = true;
      } else if (force || data.version !== state.version) {
        apply(data);
      } else {
        el.loading.hidden = true;
      }
      stampSync();
    } catch (err) {
      failures += 1;
      if (failures >= MAX_FAILURES) showOffline();
      el.syncState.textContent = '同步失败';
      if (state.version === -1) {
        el.loading.textContent = '连不上电脑上的服务，检查运行窗口是否还在。';
        el.loading.hidden = false;
      }
    } finally {
      refreshing = false;
    }
  }

  function startPolling() {
    stopPolling();
    if (document.visibilityState !== 'visible') return;
    pollTimer = window.setInterval(() => {
      if (!busy && !refreshing) refresh();
    }, POLL_MS);
  }

  function stopPolling() {
    if (pollTimer) {
      window.clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  /* ------------------------------------------------------------ 交互 */

  /* ------------------------------------------------------------ 添加面板 */

  let composerOpen = false;
  let composerTimer = null;
  let originRect = null;

  /** 展开后的落点：右下角锚定，宽度不超过视口；窄屏会自动往左展开。 */
  function panelRect(from) {
    const margin = 16;
    const vw = window.innerWidth;
    const width = Math.min(470, vw - margin * 2);
    const height = Math.min(300, Math.round(window.innerHeight * 0.62));
    const expandRight = from.left + width <= vw - margin;
    const left = expandRight ? from.left : Math.max(margin, vw - margin - width);
    const top = Math.max(margin, from.bottom - height);
    return { left, top, width, height };
  }

  function openComposer() {
    if (composerOpen) return;
    composerOpen = true;

    originRect = el.composer.getBoundingClientRect();
    el.composer.style.position = 'fixed';
    el.composer.style.left = originRect.left + 'px';
    el.composer.style.top = originRect.top + 'px';
    el.composer.style.right = 'auto';
    el.composer.style.bottom = 'auto';
    el.composer.style.width = originRect.width + 'px';
    el.composer.style.height = originRect.height + 'px';
    el.composer.style.marginTop = '0';

    const target = panelRect(originRect);

    // 先按 FAB 的尺寸落位并强制重排，再写目标尺寸，宽高才会真的走过渡而不是瞬间跳变
    void el.composer.offsetWidth;

    el.composer.style.left = target.left + 'px';
    el.composer.style.top = target.top + 'px';
    el.composer.style.width = target.width + 'px';
    el.composer.style.height = target.height + 'px';
    el.composer.classList.add('is-open');
    el.fab.setAttribute('aria-expanded', 'true');

    clearTimeout(composerTimer);
    composerTimer = window.setTimeout(() => {
      el.panel.hidden = false;
      el.composer.classList.add('is-in');
      el.input.focus();
      const end = el.input.value.length;
      el.input.setSelectionRange(end, end);
    }, MORPH_MS);
  }

  function closeComposer(options) {
    if (!composerOpen) return;
    composerOpen = false;
    clearTimeout(composerTimer);

    el.composer.classList.remove('is-in');
    el.panel.hidden = true;
    el.fab.setAttribute('aria-expanded', 'false');
    markInvalid(false);

    // 沿同一条曲线收回 FAB 原来的矩形
    if (originRect) {
      el.composer.style.left = originRect.left + 'px';
      el.composer.style.top = originRect.top + 'px';
      el.composer.style.width = originRect.width + 'px';
      el.composer.style.height = originRect.height + 'px';
    }
    el.composer.classList.remove('is-open');

    composerTimer = window.setTimeout(() => {
      el.composer.style.cssText = '';
      if (!options || options.restoreFocus !== false) el.fab.focus();
    }, MORPH_MS);
  }

  async function submitComposer() {
    if (busy) return;

    const text = el.input.value.trim();
    if (!text) {
      markInvalid(true);
      notify('先写一件要做的事，空白任务不会添加', 'hint');
      el.input.focus();
      return;
    }

    busy = true;
    el.submit.disabled = true;
    try {
      await api.create(text);
      el.input.value = '';
      markInvalid(false);
      hideMsg();
      closeComposer();
      await refresh({ force: true });
    } catch (err) {
      notify(err.message || '添加失败，请重试', 'error');
      el.input.focus();
    } finally {
      busy = false;
      el.submit.disabled = false;
    }
  }

  el.fab.addEventListener('click', openComposer);
  el.cancel.addEventListener('click', () => closeComposer());
  el.submit.addEventListener('click', submitComposer);

  el.input.addEventListener('input', () => {
    if (el.input.hasAttribute('aria-invalid')) markInvalid(false);
  });

  el.input.addEventListener('keydown', (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      event.preventDefault();
      submitComposer();
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && composerOpen) {
      event.preventDefault();
      closeComposer();
    }
  });

  document.addEventListener('pointerdown', (event) => {
    if (!composerOpen) return;
    if (el.composer.contains(event.target)) return;
    closeComposer({ restoreFocus: false });
  });

  el.tasks.addEventListener('change', async (event) => {
    const box = event.target.closest('.task-check');
    if (!box) return;
    const row = box.closest('.task');
    const id = row.dataset.id;
    const done = box.checked;
    const item = state.items.find((entry) => entry.id === id);

    // 先给即时反馈，失败再回滚
    if (item) item.done = done;
    row.classList.toggle('is-done', done);
    updateCount();

    try {
      await api.setDone(id, done);
      await refresh({ force: true });
    } catch (err) {
      if (item) item.done = !done;
      box.checked = !done;
      row.classList.toggle('is-done', !done);
      updateCount();
      notify(err.message || '勾选失败，请重试', 'error');
    }
  });

  el.tasks.addEventListener('click', async (event) => {
    const editButton = event.target.closest('.task-edit');
    if (editButton) {
      startEdit(editButton.closest('.task').dataset.id);
      return;
    }

    const saveButton = event.target.closest('.task-save');
    if (saveButton) {
      await saveEdit(saveButton.closest('.task').dataset.id);
      return;
    }

    const cancelButton = event.target.closest('.task-cancel');
    if (cancelButton) {
      await cancelEdit(cancelButton.closest('.task').dataset.id);
      return;
    }

    const button = event.target.closest('.task-del');
    if (!button) return;
    const row = button.closest('.task');
    const id = row.dataset.id;
    const item = state.items.find((entry) => entry.id === id);

    button.disabled = true;
    try {
      await api.remove(id);
      state.items = state.items.filter((entry) => entry.id !== id);
      render();
      if (item) showUndo(item);
      await refresh({ force: true });
    } catch (err) {
      button.disabled = false;
      notify(err.message || '删除失败，请重试', 'error');
    }
  });

  el.tasks.addEventListener('keydown', (event) => {
    if (!event.target.classList.contains('task-edit-input')) return;
    const row = event.target.closest('.task');
    if (event.key === 'Enter') {
      event.preventDefault();
      saveEdit(row.dataset.id);
    } else if (event.key === 'Escape') {
      event.preventDefault();
      cancelEdit(row.dataset.id);
    }
  });

  el.undoBtn.addEventListener('click', undoDelete);
  el.undoClose.addEventListener('click', hideUndo);

  el.retry.addEventListener('click', () => refresh({ force: true }));

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      refresh();
      startPolling();
    } else {
      stopPolling();
    }
  });

  window.addEventListener('focus', () => refresh());
  window.addEventListener('online', () => refresh({ force: true }));
  window.addEventListener('offline', showOffline);
  window.addEventListener('pageshow', (event) => {
    if (event.persisted) refresh({ force: true });
  });

  /* ------------------------------------------------------------ 启动 */

  function renderToday() {
    const now = new Date();
    const week = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][now.getDay()];
    const pad = (n) => String(n).padStart(2, '0');
    el.today.textContent = (now.getMonth() + 1) + '月' + now.getDate() + '日 ' + week;
    // 用本地时间拼，不用 toISOString（那是 UTC，东八区会差一天）
    el.today.setAttribute(
      'datetime',
      now.getFullYear() + '-' + pad(now.getMonth() + 1) + '-' + pad(now.getDate())
    );
  }

  renderToday();
  refresh({ force: true });
  startPolling();
})();
