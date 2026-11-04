/**
 * pi-task-notify — notify the user when Pi stops and needs them.
 *
 * Fires system notifications on:
 *   - task complete           (agent_settled, outcome completed)
 *   - task errored            (agent_settled, outcome error, with error excerpt)
 *   - waiting for the user    (ui_prompt_start: confirms, questions, editors)
 *   - long-run heartbeat      (configurable, default every 10 minutes)
 *
 * Deliberately silent for: Esc aborts (you are at the keyboard), single tool
 * failures and provider retries (Pi recovers on its own), and pi-subagents
 * child sessions (the parent session reports; children would be duplicates).
 *
 * Notifications are governed by a single mode, selectable via the /notify
 * command or the config file:
 *   - "always": notify regardless of terminal focus
 *   - "focus":  notify only when the terminal is not in the foreground
 *               (best-effort per platform; fail-open: if focus cannot be
 *               determined, notify anyway). Linux has no reliable focus check
 *               and treats "focus" like "always".
 *   - "off":    no notifications at all, /notify-test included.
 *
 * Platform support:
 *   - Windows: WinRT toast via PowerShell (default sound; errors use the
 *     Reminder sound). Focus check via foreground-window PID ancestry.
 *   - macOS:   osascript display notification. Focus check via frontmost app.
 *   - Linux:   notify-send. No focus check.
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execFile } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

interface NotifyOn {
	complete: boolean;
	error: boolean;
	waiting: boolean;
	heartbeat: boolean;
}

/** Notification mode: always = ignore focus; focus = only when unfocused; off = silent. */
type FocusMode = "always" | "focus" | "off";

interface NotifyConfig {
	enabled: boolean;
	mode: FocusMode;
	/** Minutes between heartbeat notifications while a run is active. 0 disables. */
	heartbeatMinutes: number;
	/** Max characters of the error excerpt shown in the error toast. */
	errorSummaryLength: number;
	notifyOn: NotifyOn;
}

const DEFAULT_CONFIG: NotifyConfig = {
	enabled: true,
	mode: "focus",
	heartbeatMinutes: 10,
	errorSummaryLength: 100,
	notifyOn: { complete: true, error: true, waiting: true, heartbeat: true },
};

const MODE_LABELS: Record<FocusMode, string> = {
	always: "总是通知（不管聚不聚焦）",
	focus: "失焦才通知（切走窗口才提醒）",
	off: "关闭（完全静默）",
};

const CONFIG_PATH = path.join(os.homedir(), ".pi", "agent", "pi-task-notify.json");

/** The mode that actually governs sending: the legacy enabled=false master switch maps to off. */
function effectiveMode(cfg: NotifyConfig): FocusMode {
	return cfg.enabled ? cfg.mode : "off";
}

/**
 * Fresh read on every notification so config changes apply without /reload.
 * Unknown files fall back to defaults; invalid values keep their default.
 * Pre-0.2 fields stay recognized: focusAware:false maps to "always", and
 * enabled:false maps to "off". An explicit "mode" wins over focusAware.
 */
function loadConfig(): NotifyConfig {
	const cfg: NotifyConfig = structuredClone(DEFAULT_CONFIG);
	let raw: unknown;
	try {
		raw = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
	} catch {
		return cfg; // missing or unreadable file -> defaults
	}
	if (typeof raw !== "object" || raw === null) return cfg;
	const obj = raw as Record<string, unknown>;
	if (typeof obj.enabled === "boolean") cfg.enabled = obj.enabled;
	if (obj.mode === "always" || obj.mode === "focus" || obj.mode === "off") {
		cfg.mode = obj.mode;
	} else if (typeof obj.focusAware === "boolean") {
		cfg.mode = obj.focusAware ? "focus" : "always"; // pre-0.2 configs
	}
	if (!cfg.enabled) cfg.mode = "off"; // legacy master switch
	if (typeof obj.heartbeatMinutes === "number" && obj.heartbeatMinutes >= 0) {
		cfg.heartbeatMinutes = Math.min(obj.heartbeatMinutes, 24 * 60);
	}
	if (typeof obj.errorSummaryLength === "number" && obj.errorSummaryLength > 0) {
		cfg.errorSummaryLength = Math.min(Math.floor(obj.errorSummaryLength), 500);
	}
	if (typeof obj.notifyOn === "object" && obj.notifyOn !== null) {
		const on = obj.notifyOn as Record<string, unknown>;
		for (const key of Object.keys(cfg.notifyOn) as Array<keyof NotifyOn>) {
			if (typeof on[key] === "boolean") cfg.notifyOn[key] = on[key] as boolean;
		}
	}
	return cfg;
}

/** Persist a mode choice from /notify, preserving every other config field. */
function saveMode(mode: FocusMode): void {
	let obj: Record<string, unknown> = {};
	try {
		const parsed: unknown = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
		if (typeof parsed === "object" && parsed !== null) {
			obj = { ...(parsed as Record<string, unknown>) };
		}
	} catch {
		obj = {}; // missing or unreadable file -> start fresh
	}
	obj.mode = mode;
	obj.enabled = true; // the mode now owns the off state
	fs.mkdirSync(path.dirname(CONFIG_PATH), { recursive: true });
	fs.writeFileSync(CONFIG_PATH, `${JSON.stringify(obj, null, 2)}\n`);
}

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

/** pi-subagents injects PI_SUBAGENTS_* env vars into child pi processes. */
function isSubagentSession(): boolean {
	return Object.keys(process.env).some((key) => key.startsWith("PI_SUBAGENTS_"));
}

const PROJECT_LABEL = `Pi · ${path.basename(process.cwd())}`;
const TOAST_TAG = "pi-task-notify";

type NotifyKind = "complete" | "error" | "waiting" | "heartbeat";

interface NotifyOptions {
	title: string;
	body: string;
	/** false = always show (e.g. /notify-test). */
	respectFocus: boolean;
	/** Toast replacement tag; defaults to the shared one so same-project toasts replace each other. */
	tag?: string;
	sound: "default" | "reminder";
}

function oneLine(text: string): string {
	return text.replace(/\s+/g, " ").trim();
}

/** Tail excerpt: failure reasons live at the end of error output. */
function tail(text: string, max: number): string {
	const line = oneLine(text);
	if (line.length <= max) return line;
	return `…${line.slice(-max)}`;
}

function formatDuration(ms: number): string {
	const minutes = Math.max(1, Math.round(ms / 60000));
	if (minutes < 60) return `${minutes} 分钟`;
	const hours = Math.floor(minutes / 60);
	const rest = minutes % 60;
	return rest > 0 ? `${hours} 小时 ${rest} 分钟` : `${hours} 小时`;
}

function xmlEscape(text: string): string {
	return text
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&apos;");
}

function runExe(exe: string, args: string[], timeoutMs = 15000): Promise<void> {
	return new Promise((resolve) => {
		try {
			execFile(exe, args, { timeout: timeoutMs, windowsHide: true }, () => resolve());
		} catch {
			resolve(); // notification must never break the session
		}
	});
}

// ---------------------------------------------------------------------------
// Windows backend: one PowerShell invocation does focus check + toast
// ---------------------------------------------------------------------------

const WINDOWS_SCRIPT = `
$ErrorActionPreference = 'Stop'
$showToast = $true
if ($usingFocusCheck -eq '1') {
	try {
		Add-Type -Namespace Native -Name FocusApi -MemberDefinition @'
[DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
'@
		$fg = [Native.FocusApi]::GetForegroundWindow()
		if ($fg -ne [IntPtr]::Zero) {
			$fgPid = 0
			[Native.FocusApi]::GetWindowThreadProcessId($fg, [ref]$fgPid) | Out-Null
			$ancestors = @{}
			$proc = Get-CimInstance Win32_Process -Filter "ProcessId=$PID"
			while ($proc) {
				$ancestors[[string]$proc.ProcessId] = $true
				if (-not $proc.ParentProcessId) { break }
				$proc = Get-CimInstance Win32_Process -Filter "ProcessId=$($proc.ParentProcessId)"
			}
			if ($ancestors[[string]$fgPid]) { $showToast = $false }
		}
	} catch { $showToast = $true } # fail open: notify when focus cannot be determined
}
if ($showToast) {
	[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
	[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null
	$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
	$xml.LoadXml($toastXml)
	$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
	$toast.Tag = $toastTag
	$toast.Group = $toastGroup
	[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appLabel).Show($toast)
}
`;

function toastXml(title: string, body: string, sound: "default" | "reminder"): string {
	const audio =
		sound === "reminder"
			? '<audio src="ms-winsoundevent:Notification.Reminder"/>'
			: '<audio src="ms-winsoundevent:Notification.Default"/>';
	return (
		"<toast>" +
		`<visual><binding template="ToastText02"><text id="1">${xmlEscape(title)}</text>` +
		`<text id="2">${xmlEscape(body)}</text></binding></visual>${audio}</toast>`
	);
}

async function notifyWindows(opts: NotifyOptions): Promise<void> {
	// Windows toast Tag and Group are limited to 16 characters each.
	const tag = (opts.tag ?? TOAST_TAG).slice(0, 16);
	const group = path.basename(process.cwd()).slice(0, 16);
	const full =
		`$usingFocusCheck = '${opts.respectFocus ? 1 : 0}'\n` +
		`$toastTag = '${tag}'\n` +
		`$toastGroup = '${group}'\n` +
		`$appLabel = '${PROJECT_LABEL.replace(/'/g, "''")}'\n` +
		`$toastXml = @'\n${toastXml(opts.title, opts.body, opts.sound)}\n'@\n` +
		WINDOWS_SCRIPT;
	await runExe("powershell.exe", ["-NoProfile", "-NonInteractive", "-EncodedCommand", encodePs(full)]);
}

function encodePs(script: string): string {
	return Buffer.from(script, "utf16le").toString("base64");
}

// ---------------------------------------------------------------------------
// macOS backend: focus check + osascript in one shell invocation
// ---------------------------------------------------------------------------

async function notifyMac(opts: NotifyOptions): Promise<void> {
	const soundPart = opts.sound === "reminder" ? "sound name \"Sosumi\"" : "";
	const appleScript =
		`on run argv\ndisplay notification (item 2 of argv) with title (item 1 of argv) subtitle (item 3 of argv) ${soundPart}\nend run`;
	const checkFocus = opts.respectFocus;
	const script = [
		`TITLE=${shellQuote(opts.title)}`,
		`BODY=${shellQuote(opts.body)}`,
		`SUB=${shellQuote(PROJECT_LABEL)}`,
		`AS=${shellQuote(appleScript)}`,
		`if [ "${checkFocus ? "1" : ""}" = "1" ]; then`,
		`  FRONT=$(osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true' 2>/dev/null || true)`,
		`  if [ -n "$FRONT" ]; then`,
		`    P=$$; OURS=""`,
		`    while [ "$P" != "1" ] && [ -n "$P" ]; do`,
		`      NM=$(ps -o comm= -p "$P" 2>/dev/null); [ -z "$NM" ] && break`,
		`      OURS="$OURS $(basename "$NM")"; P=$(ps -o ppid= -p "$P" | tr -d ' ')`,
		`    done`,
		`    case " $OURS " in *" $FRONT "*) exit 0;; esac`,
		`  fi`,
		`fi`,
		`osascript -e "$AS" "$TITLE" "$BODY" "$SUB" >/dev/null 2>&1 || true`,
	].join("\n");
	await runExe("/bin/sh", ["-c", script]);
}

function shellQuote(text: string): string {
	return `'${text.replace(/'/g, `'\\''`)}'`;
}

// ---------------------------------------------------------------------------
// Linux backend: notify-send, always notify (no reliable focus check)
// ---------------------------------------------------------------------------

async function notifyLinux(opts: NotifyOptions): Promise<void> {
	const urgency = opts.sound === "reminder" ? "critical" : "normal";
	await runExe("notify-send", ["-a", PROJECT_LABEL, "-u", urgency, `${opts.title}`, opts.body]);
}

// ---------------------------------------------------------------------------
// Dispatch
// ---------------------------------------------------------------------------

function sendNotification(opts: NotifyOptions): void {
	const cfg = loadConfig();
	if (effectiveMode(cfg) === "off") return;
	// "focus" mode gates on foreground state; "always" disables the gate.
	const respectFocus = opts.respectFocus && cfg.mode === "focus";
	switch (process.platform) {
		case "win32":
			void notifyWindows({ ...opts, respectFocus });
			break;
		case "darwin":
			void notifyMac({ ...opts, respectFocus });
			break;
		case "linux":
			void notifyLinux(opts);
			break;
		default:
			break; // unsupported platform: stay silent
	}
}

// ---------------------------------------------------------------------------
// Extension wiring
// ---------------------------------------------------------------------------

export default function (pi: ExtensionAPI) {
	let runStartedAt: number | null = null;
	let heartbeatStage = 0;
	let lastErrorText: string | undefined;
	let lastOutcome: "completed" | "aborted" | "error" | undefined;
	let heartbeatTimer: ReturnType<typeof setInterval> | null = null;
	// True while /notify's own select dialog is open: the user typed that command,
	// so they are by definition at the keyboard and "waiting" would be noise.
	let selfPromptActive = false;

	function notifyKind(kind: NotifyKind, opts?: { respectFocus?: boolean; tag?: string; bodyOverride?: string; titleOverride?: string }): void {
		const titles = {
			complete: "✅ 任务完成",
			error: "❌ 任务出错",
			waiting: "❓ 等你确认",
			heartbeat: "⏳ 还在跑",
		} satisfies Record<NotifyKind, string>;
		const sounds = {
			complete: "default",
			error: "reminder",
			waiting: "default",
			heartbeat: "default",
		} satisfies Record<NotifyKind, "default" | "reminder">;
		const duration = runStartedAt ? formatDuration(Date.now() - runStartedAt) : null;
		let body: string;
		switch (kind) {
			case "complete":
				body = `运行了 ${duration ?? "一会儿"}，等你下一步指示`;
				break;
			case "error":
				body = opts?.bodyOverride ?? lastErrorText ?? "运行中遇到错误（详情见终端）";
				break;
			case "waiting":
				body = "Pi 正在等待你的确认或回答";
				break;
			case "heartbeat":
				body = `已运行 ${duration ?? "一会儿"}`;
				break;
			default: {
				const exhaustive: never = kind;
				void exhaustive;
				body = "Pi 通知";
			}
		}
		sendNotification({
			title: opts?.titleOverride ?? titles[kind],
			body: oneLine(body).slice(0, 220),
			respectFocus: opts?.respectFocus ?? true,
			tag: opts?.tag,
			sound: sounds[kind],
		});
	}

	pi.on("session_start", () => {
		runStartedAt = null;
		heartbeatStage = 0;
		lastErrorText = undefined;
		lastOutcome = undefined;
		if (heartbeatTimer) clearInterval(heartbeatTimer);
		heartbeatTimer = setInterval(() => {
			const cfg = loadConfig();
			if (!cfg.enabled || !cfg.notifyOn.heartbeat || cfg.heartbeatMinutes <= 0) return;
			if (runStartedAt === null) return;
			const elapsedMinutes = (Date.now() - runStartedAt) / 60000;
			if (elapsedMinutes >= (heartbeatStage + 1) * cfg.heartbeatMinutes) {
				heartbeatStage += 1;
				if (isSubagentSession()) return;
				notifyKind("heartbeat");
			}
		}, 20_000);
	});

	pi.on("session_shutdown", () => {
		if (heartbeatTimer) {
			clearInterval(heartbeatTimer);
			heartbeatTimer = null;
		}
	});

	pi.on("agent_start", () => {
		runStartedAt = Date.now();
		heartbeatStage = 0;
		lastErrorText = undefined;
		lastOutcome = undefined;
	});

	pi.on("tool_result", (event) => {
		if (!event.isError) return;
		const text = event.content
			.flatMap((item) => (item.type === "text" ? [item.text] : []))
			.join(" ");
		if (text.trim()) lastErrorText = text;
	});

	pi.on("turn_end", (event) => {
		lastOutcome = event.outcome;
	});

	pi.on("agent_before_settle", (event) => {
		lastOutcome = event.outcome;
	});

	pi.on("agent_settled", () => {
		const startedAt = runStartedAt;
		runStartedAt = null;
		if (isSubagentSession()) return;
		const cfg = loadConfig();
		if (!cfg.enabled) return;
		if (lastOutcome === "error") {
			if (cfg.notifyOn.error) {
				notifyKind("error", {
					bodyOverride: lastErrorText ? tail(lastErrorText, cfg.errorSummaryLength) : undefined,
				});
			}
			return;
		}
		if (lastOutcome === "aborted") return; // Esc abort: the user is at the keyboard
		if (cfg.notifyOn.complete) {
			runStartedAt = startedAt; // restore for duration formatting
			notifyKind("complete");
			runStartedAt = null;
		}
	});

	pi.on("ui_prompt_start", (event) => {
		if (selfPromptActive) return; // our own /notify dialog
		if (isSubagentSession()) return;
		const cfg = loadConfig();
		if (!cfg.enabled || !cfg.notifyOn.waiting) return;
		const kindText = {
			select: "等你选择",
			confirm: "等你确认",
			input: "等你输入",
			editor: "等你编辑",
			custom: "等你处理",
		} satisfies Record<"select" | "confirm" | "input" | "editor" | "custom", string>;
		notifyKind("waiting", {
			bodyOverride: event.title
				? `Pi ${kindText[event.kind] ?? "在等你"}：${tail(event.title, 60)}`
				: `Pi ${kindText[event.kind] ?? "在等你"}`,
		});
	});

	pi.registerCommand("notify", {
		description: "Pick a notification mode: always / only when unfocused / off",
		handler: async (_args, ctx) => {
			if (!ctx.hasUI) return;
			const current = effectiveMode(loadConfig());
			const order: FocusMode[] = ["always", "focus", "off"];
			const options = order.map((mode) =>
				mode === current ? `${MODE_LABELS[mode]}（当前）` : MODE_LABELS[mode],
			);
			const choice = await (async () => {
				selfPromptActive = true;
				try {
					return await ctx.ui.select("通知模式", options);
				} finally {
					selfPromptActive = false;
				}
			})();
			if (!choice) return;
			const picked = order[options.indexOf(choice)];
			if (picked === current) {
				ctx.ui.notify(`通知模式未变：${MODE_LABELS[picked]}`, "info");
				return;
			}
			try {
				saveMode(picked);
			} catch (error) {
				ctx.ui.notify(
					`写入配置失败：${error instanceof Error ? error.message : String(error)}`,
					"error",
				);
				return;
			}
			ctx.ui.notify(`通知模式已改为：${MODE_LABELS[picked]}（立即生效，无需重启）`, "info");
		},
	});

	pi.registerCommand("notify-test", {
		description: "Send sample notifications (complete / error / waiting / heartbeat) to verify pi-task-notify",
		handler: async (_args, ctx) => {
			const cfg = loadConfig();
			if (effectiveMode(cfg) === "off") {
				ctx.ui.notify("通知已关闭。运行 /notify 重新选择通知模式。", "warning");
				return;
			}
			ctx.ui.notify("正在发送 4 条样例通知（约每秒 1 条，切到别的窗口观察）…", "info");
			const startedAt = runStartedAt;
			runStartedAt = Date.now() - 6 * 60_000; // sample durations
			const samples: Array<NotifyKind> = ["complete", "error", "waiting", "heartbeat"];
			const shortKind = {
				complete: "done",
				error: "err",
				waiting: "ask",
				heartbeat: "beat",
			} satisfies Record<NotifyKind, string>;
			for (const kind of samples) {
				notifyKind(kind, {
					respectFocus: false, // explicit user action: always show
					tag: `t-${shortKind[kind]}`, // <=16 chars, distinct: all four sample toasts stay visible
				});
				await new Promise((resolve) => setTimeout(resolve, 1000));
			}
			runStartedAt = startedAt;
			ctx.ui.notify("已发送完成。如果没看到，请检查系统通知权限/免打扰设置。", "info");
		},
	});
}
