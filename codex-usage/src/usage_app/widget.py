"""Real state and time in the M1 frozen composition; no new page or fake data."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFontMetricsF, QHelpEvent, QKeyEvent, QPainter
from PySide6.QtWidgets import QToolTip

from countdown import Countdown, present_countdown
from main import DETAIL_COUNTDOWN_X, DETAIL_META_X, INK, MUTED, LeafPrototype
from quota_visual import QuotaSample, lowest_remaining

from .models import ERROR_MESSAGES, Provider, ProviderState, RecoveryKind, Status
from .messages import product_message
from .presentation import compact_amount, quota_sample, trust_mark, window_for
from .rules import BenefitResult, BenefitStatus, RULES, RuleEngine
from .runtime import UsageRuntime


class LiveLeaf(LeafPrototype):
    def __init__(self, runtime: UsageRuntime, *, expanded: bool = False, reduced_motion: bool = False) -> None:
        self.runtime = runtime
        self.rules = RuleEngine()
        self._benefit_minute: int | None = None
        self._benefit_cache: dict[Provider, BenefitResult] = {}
        self._dock_benefit_status: tuple[BenefitStatus, ...] | None = None
        self._presentation_now: datetime | None = None
        self._last_countdowns: tuple[tuple[str, str, Countdown | None], ...] | None = None
        self._last_live_sample = quota_sample(runtime.states)
        super().__init__(expanded=expanded, reduced_motion=reduced_motion)
        self.setWindowTitle("usage")
        self.setAccessibleName("usage：三平台资源状态")
        runtime.changed.connect(self._data_changed)
        runtime.storage_failed.connect(self._storage_problem)

    def _now(self) -> datetime:
        return datetime.now().astimezone()

    def _sample(self) -> QuotaSample:
        return quota_sample(self.runtime.states)

    def _benefit(self, provider: Provider) -> BenefitResult:
        now = self._now()
        minute = int(now.timestamp()) // 60
        if minute != self._benefit_minute:
            self._benefit_minute = minute
            self._benefit_cache = {key: self.rules.evaluate(now, rule) for key, rule in RULES.items()}
        return self._benefit_cache[provider]

    def _on_tick(self) -> None:
        expanded = self._progress > .001
        interval = 250 if expanded else 1000
        if self._tick.interval() != interval:
            self._tick.setInterval(interval)
        changed = False
        if expanded:
            now = self._now()
            current = tuple((provider.value, window.id, present_countdown(window.next_recovery_at, now))
                            for provider, state in self.runtime.states.items() if state.snapshot
                            for window in state.snapshot.windows)
            changed = current != self._last_countdowns
            self._last_countdowns = current
            self._presentation_now = now
        else:
            self._presentation_now = None
            self._last_countdowns = None
        # Resource/freshness changes and reminder animation already emit update.
        # A quiet collapsed dial needs a paint only at a benefit-rule change.
        statuses = tuple(self._benefit(provider).status for provider in (Provider.GLM, Provider.DEEPSEEK))
        if changed or statuses != self._dock_benefit_status:
            self.update()
        self._dock_benefit_status = statuses

    def _data_changed(self) -> None:
        self._presentation_now = None
        self._last_countdowns = None
        sample = self._sample()
        previous, self._last_live_sample = self._last_live_sample, sample
        if previous != sample and not self.reduced_motion:
            self._quota_animation.stop()
            self._previous_sample = previous
            self._quota_animation.setStartValue(0.0)
            self._quota_animation.setEndValue(1.0)
            self._quota_animation.start()
        self.update()

    def _storage_problem(self, message: str) -> None:
        # Never replace data from another provider or report a save succeeded.
        self.setAccessibleDescription(product_message(message))

    def expand(self) -> None:
        self._presentation_now = None
        self._tick.setInterval(250)
        super().expand()
        self.runtime.set_expanded(True)

    def collapse(self) -> None:
        super().collapse()
        if not self.pinned and not self.hasFocus() and not self._drag_pending:
            self.runtime.set_expanded(False)

    def _provider_stale(self, provider: str) -> bool:
        state = self.runtime.states.get(Provider(provider))
        return bool(state and state.retained)

    def _trust_mark(self, provider: str, sample: QuotaSample) -> str:
        mark = trust_mark(self.runtime.states.get(Provider(provider)))
        return mark or super()._trust_mark(provider, sample)

    def _trust_caption(self, mark: str) -> str:
        return {"断": "未连", "权": "授权", "验": "待验", "错": "离线", "等": "冷却", "读": "读取"}.get(mark, super()._trust_caption(mark))

    def _balance_trust_mark(self, sample: QuotaSample) -> str:
        return trust_mark(self.runtime.states.get(Provider.DEEPSEEK)) or ("缺" if sample.deepseek_balance is None else "")

    def _benefit_enabled(self, provider: str) -> bool:
        return self._benefit(Provider(provider)).status == BenefitStatus.DISCOUNT

    def _benefit_mark(self, provider: str) -> str:
        status = self._benefit(Provider(provider)).status
        return "半" if status == BenefitStatus.DISCOUNT else "?" if status == BenefitStatus.UNVERIFIED else ""

    def _paint_benefit_word(self, p: QPainter, x: float, y: float, suffix: str) -> None:
        provider = Provider.GLM if suffix == "耗" else Provider.DEEPSEEK
        result = self._benefit(provider)
        if result.status == BenefitStatus.DISCOUNT:
            super()._paint_benefit_word(p, x, y, suffix)
        elif result.status == BenefitStatus.UNVERIFIED:
            self._text(p, x, y, "待验", 8.1, MUTED)

    def _stamp(self, state: ProviderState | None) -> str:
        if not state or not state.snapshot:
            return "未更新"
        label = "保留" if state.retained else "更新"
        return f"{label} {state.snapshot.last_success_at.astimezone():%H:%M}"

    def _state_description(self, state: ProviderState | None) -> str:
        if state is None or not state.account.enabled:
            return "尚未连接"
        if state.error:
            return ERROR_MESSAGES[state.error]
        return {Status.LOADING: "正在读取", Status.DISCONNECTED: "尚未连接",
                Status.FRESH: "官方只读数据", Status.STALE: "保留上次成功数据"}.get(state.status, "暂时不可用")

    def _paint_time_content(self, p: QPainter, detail: str, now: datetime) -> None:
        # Animation frames interpolate one sampled presentation. Re-reading
        # wall time on every frame can cross a millisecond recovery boundary
        # mid-transition and make two consecutive seconds appear as one jump.
        if self._presentation_now is None:
            self._presentation_now = now
        now = self._presentation_now
        states = self.runtime.states
        left = self._visual_edge() == "left"
        title_x = 145 if left else 95
        if detail:
            provider = Provider(detail)
            state = states.get(provider)
            self._text(p, title_x, 54, {Provider.CODEX: "Codex", Provider.GLM: "GLM", Provider.DEEPSEEK: "DeepSeek"}[provider],
                       9.5, self._provider_color(detail) if provider != Provider.DEEPSEEK else self.theme.balance, True)
            if provider != Provider.DEEPSEEK:
                self._text(p, DETAIL_META_X + (52 if left else 0), 54, self._stamp(state), 9, MUTED)
            if not state or not state.snapshot:
                self._text(p, 105 if left else 95, 83, self._state_description(state), 11, INK, True)
                self._text(p, 95, 107, "暂无成功快照", 9, MUTED)
                return
            if provider == Provider.DEEPSEEK:
                balances = state.snapshot.balances if state and state.snapshot else ()
                if balances:
                    if len(balances) == 1:
                        balance = balances[0]
                        detail_text = f"赠 {compact_amount(balance.granted, balance.currency)}" if balance.granted is not None else "赠 未知"
                        detail_text += f" · 充 {compact_amount(balance.topped_up, balance.currency)}" if balance.topped_up is not None else " · 充 未知"
                        if QFontMetricsF(self._font(10.2)).horizontalAdvance(detail_text) > 125:
                            detail_text = "余额明细可悬停"
                        self._text(p, 105 if left else 95, 81, detail_text, 10.2, INK)
                    elif len(balances) == 2 and all(item.currency in ("CNY", "USD") for item in balances):
                        content = " · ".join(compact_amount(item.total, item.currency) for item in balances)
                        if QFontMetricsF(self._font(10.2, True, True)).horizontalAdvance(content) > 125:
                            content = "多币种 · 悬停详查"
                        self._text(p, 105 if left else 95, 81, content, 10.2, self.theme.balance, True, numeric=True)
                    else:
                        self._text(p, 105 if left else 95, 81, f"{len(balances)} 币种 · 悬停详查", 10.2, INK)
                    available = balances[0].is_available
                    label = "可用" if available is True else "不可用" if available is False else "可用性未知"
                    self._text(p, 95, 106, f"{self._stamp(state)} · {label}", 9, MUTED)
                else:
                    self._text(p, 105 if left else 95, 83, self._state_description(state), 11, INK, True)
                    self._text(p, 95, 107, "未将未知金额视为零", 9, MUTED)
                return
            for key, duration, y in (("5h", 300, 80), ("周", 10080, 106)):
                window = window_for(state, duration)
                at = window.next_recovery_at.astimezone() if window and window.next_recovery_at else None
                label = f"{key} {at:%H:%M}" if at and duration == 300 else f"{key} {at:%m/%d}" if at else key
                self._text(p, 105 if left and y == 80 else 95, y, label, 9, MUTED)
                self._paint_countdown(p, f"live-{detail}-{key}", present_countdown(at, now),
                                      DETAIL_COUNTDOWN_X + (8 if left and y == 80 else 0), y, 10)
            return
        sample = self._sample()
        lowest = lowest_remaining(sample, include_week=True)
        if lowest is None:
            loading = any(state.status == Status.LOADING for state in states.values())
            self._text(p, title_x, 56, "usage", 9.6, MUTED, True)
            self._text(p, 105 if left else 95, 85, "正在读取" if loading else "四窗额度未知", 12, INK, True)
            self._text(p, 95, 107, "按平台查看连接状态", 9, MUTED)
            return
        provider_name, window_name, value = lowest
        provider = Provider(provider_name)
        state = states.get(provider)
        window = window_for(state, 300 if window_name == "5h" else 10080)
        at = window.next_recovery_at.astimezone() if window and window.next_recovery_at else None
        presentation = present_countdown(at, now)
        limited = any(item is None for item in (sample.codex_5h, sample.codex_week, sample.glm_5h, sample.glm_week)) or any(item.retained for item in states.values())
        title = f"{'已知' if limited else '最低'} · {'Codex' if provider == Provider.CODEX else 'GLM'} {'5h' if window_name == '5h' else '周'}"
        self._text(p, title_x, 56, title, 9.6, self._provider_color(provider_name), True)
        self._text(p, 103 if left else 95, 87, f"{value:g}%", 13.2, self._quota_color(provider_name, value), True, numeric=True)
        self._paint_countdown(p, f"live-default-{provider_name}-{window_name}", presentation, 147, 87, 9.8)
        if presentation and presentation.status == "awaiting_confirmation":
            line = "待确认 · 等待官方更新"
        elif at:
            verb = "补回" if window and window.recovery_kind == RecoveryKind.ROLLING else "恢复"
            when = f"{at:%H:%M}" if window_name == "5h" else f"{at:%m/%d %H:%M}"
            line = f"{verb} {when} · {self._stamp(state)}"
        else:
            line = f"恢复未提供 · {self._stamp(state)}"
        self._text(p, 95, 107, line, 8.8, MUTED)

    def describe_provider(self, provider: Provider) -> str:
        state = self.runtime.states.get(provider)
        text = [provider.value, self._state_description(state), self._stamp(state)]
        if state and state.snapshot:
            for window in state.snapshot.windows:
                text.append(f"{window.source_bucket_id} / {window.duration_minutes} 分钟：剩余 {window.remaining_percent}%" if window.remaining_percent is not None else "此窗口比例未知")
                if window.next_recovery_at:
                    text.append(f"{'下一次补回' if window.recovery_kind == RecoveryKind.ROLLING else '恢复'} {window.next_recovery_at.astimezone():%Y-%m-%d %H:%M:%S}")
            for balance in state.snapshot.balances:
                text.append(f"{balance.currency} 可用 {balance.total}；赠送 {balance.granted}；充值 {balance.topped_up}")
        if provider in RULES:
            result = self._benefit(provider)
            text.append(f"常态规则 · UTC+8 · {'半耗' if provider == Provider.GLM else '半价'}：{result.status.value}")
            if provider == Provider.GLM:
                text.append("仅计算常态模型积分；不含 MCP 和限时活动")
        return "\n".join(text)

    def event(self, event: QEvent) -> bool:
        if isinstance(event, QHelpEvent) and event.type() == QEvent.Type.ToolTip and self._progress > .95:
            provider = self._provider_at(event.pos().x(), event.pos().y())
            if provider:
                QToolTip.showText(event.globalPos(), self.describe_provider(Provider(provider)), self)
                return True
        return super().event(event)

    def _activate_ball(self, index: int) -> None:
        self._show_ball_tip(index, "快捷文本尚未配置" if index < 3 else "每日提醒尚未配置" if index == 3 else "账户配置使用本机安全入口")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_R:
            self.runtime.refresh_now()
            event.accept()
        elif event.key() in (Qt.Key.Key_M, Qt.Key.Key_Tab, Qt.Key.Key_Backtab, Qt.Key.Key_Space,
                             Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Escape, Qt.Key.Key_Q):
            super().keyPressEvent(event)
        else:
            event.ignore()  # Prototype sample/state shortcuts do not exist in the product.
