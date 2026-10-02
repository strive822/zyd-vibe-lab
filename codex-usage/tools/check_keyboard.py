"""Run every prototype focus item through real Qt key events and capture its result."""

from __future__ import annotations

from _paths import EVIDENCE

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from main import BALL_NAMES, FOCUS_PROVIDERS, SAMPLE_TEXT, LeafPrototype


out = Path(EVIDENCE / "m1-r3/keyboard")
out.mkdir(parents=True, exist_ok=True)
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
widget = LeafPrototype(expanded=True, scenario="low", reduced_motion=True)
widget.move(100, 100)
widget.show()
widget._pulse.stop()
widget._tick.stop()
widget._now = lambda: widget._base_now
widget.setFocus()
app.processEvents()

tips: list[tuple[int, str]] = []
widget._show_ball_tip = lambda index, label: tips.append((index, label))
frames: list[Image.Image] = []
action_frames: list[tuple[str, Image.Image]] = []
events: list[dict] = []


def focus(index: int) -> None:
    QTest.keyClick(widget, Qt.Key.Key_Escape)
    widget.setFocus()
    widget.copy_feedback = ""
    widget._feedback_timer.stop()
    widget.acknowledge_reminder_demo()
    widget.trigger_reminder_demo()
    for _ in range(index + 1):
        QTest.keyClick(widget, Qt.Key.Key_Tab)
    QTest.qWait(210)
    assert widget.keyboard_ball == index, (index, widget.keyboard_ball)
    expected_name = FOCUS_PROVIDERS[index] if index < 3 else BALL_NAMES[index - 3]
    assert expected_name in widget.accessibleDescription(), (index, widget.accessibleDescription())
    assert widget.detail == (FOCUS_PROVIDERS[index] if index < 3 else "")
    widget.grab().save(str(out / f"focus-{index:02d}.png"))
    frames.append(Image.open(out / f"focus-{index:02d}.png").convert("RGBA"))


for index in range(8):
    for key, key_name in ((Qt.Key.Key_Return, "Enter"), (Qt.Key.Key_Space, "Space")):
        focus(index)
        action_frames.append((f"{index + 1}/8 focus before {key_name}", Image.open(out / f"focus-{index:02d}.png").convert("RGBA")))
        QApplication.clipboard().clear()
        QTest.qWait(80)  # Let the Windows clipboard release the test's clear operation.
        before_tips = len(tips)
        QTest.keyClick(widget, key)
        app.processEvents()
        expected_name = FOCUS_PROVIDERS[index] if index < 3 else BALL_NAMES[index - 3]
        if index < 3:
            assert widget.detail == FOCUS_PROVIDERS[index]
            assert QApplication.clipboard().text() == "" and widget.unread_reminder
            assert len(tips) == before_tips
        elif index == 3:
            assert QApplication.clipboard().text() == SAMPLE_TEXT, (index, key_name, widget.keyboard_ball, widget.copy_feedback, QApplication.clipboard().text())
            assert widget.copy_feedback.startswith("已复制") and widget.unread_reminder
            assert len(tips) == before_tips
        elif index == 6:
            assert QApplication.clipboard().text() == "" and not widget.unread_reminder
            assert tips[-1] == (3, "演示提醒已查看")
        else:
            assert QApplication.clipboard().text() == "" and widget.unread_reminder
            assert len(tips) == before_tips + 1 and tips[-1][0] == index - 3
            assert BALL_NAMES[index - 3] in tips[-1][1]
        widget.grab().save(str(out / f"result-{index:02d}-{key_name.lower()}.png"))
        action_frames.append((f"{index + 1}/8 after {key_name}", Image.open(out / f"result-{index:02d}-{key_name.lower()}.png").convert("RGBA")))
        events.append({"focus": index, "name": expected_name, "key": key_name,
                       "clipboard_copied": QApplication.clipboard().text() == SAMPLE_TEXT,
                       "reminder_unread": widget.unread_reminder,
                       "copy_feedback": widget.copy_feedback,
                       "tip": tips[-1] if len(tips) > before_tips else None})

# Test the critic's fast sequence while the expansion animation is still running.
QTest.keyClick(widget, Qt.Key.Key_Escape)
widget.setFocus()
widget.copy_feedback = ""
widget._feedback_timer.stop()
widget.trigger_reminder_demo()
QApplication.clipboard().clear()
QTest.qWait(80)
widget.set_expansion_progress(0.0)
for _ in range(4):
    QTest.keyClick(widget, Qt.Key.Key_Tab)
QTest.keyClick(widget, Qt.Key.Key_Return)
assert widget.keyboard_ball == 3 and QApplication.clipboard().text() == SAMPLE_TEXT
assert widget.unread_reminder and widget.copy_feedback.startswith("已复制")
events.append({"sequence": "collapsed/Tab x4/Enter", "focus": widget.keyboard_ball,
               "clipboard_copied": True, "reminder_unread": True})

QTest.keyClick(widget, Qt.Key.Key_Escape)
widget.setFocus()
QTest.keyClick(widget, Qt.Key.Key_Backtab)
assert widget.keyboard_ball == 7 and BALL_NAMES[4] in widget.accessibleDescription()
events.append({"sequence": "Shift+Tab from start", "focus": widget.keyboard_ball,
               "name": BALL_NAMES[4]})

font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
w, h = frames[0].size
sheet = Image.new("RGB", (w * 4, (h + 30) * 2), "#dfe3dc")
draw = ImageDraw.Draw(sheet)
for index, frame in enumerate(frames[::2]):
    x, y = (index % 4) * w, (index // 4) * (h + 30)
    label = FOCUS_PROVIDERS[index] if index < 3 else BALL_NAMES[index - 3]
    draw.text((x + 8, y + 5), f"{index + 1}/8 {label}", fill="#1e2119", font=font)
    sheet.paste(frame, (x, y + 30), frame)
sheet.save(out / "focus-eight.png")

gif_frames = []
for index, frame in enumerate(frames[::2]):
    background = Image.new("RGBA", frame.size, "#dfe3dc")
    background.alpha_composite(frame)
    gif_frames.append(background.convert("RGB"))
gif_frames[0].save(out / "tab-sequence.gif", save_all=True, append_images=gif_frames[1:], duration=550, loop=0)
result_gif_frames = []
for label, frame in action_frames:
    background = Image.new("RGBA", (w, h + 30), "#dfe3dc")
    background.alpha_composite(frame, (0, 30))
    ImageDraw.Draw(background).text((8, 5), label, fill="#1e2119", font=font)
    result_gif_frames.append(background.convert("RGB"))
result_gif_frames[0].save(out / "keyboard-actions.gif", save_all=True,
                          append_images=result_gif_frames[1:], duration=480, loop=0)
(out / "events.json").write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
widget.close()
print(json.dumps({"focus_items": 8, "activation_checks": 16, "rapid_sequence": True,
                  "reverse_wrap": True, "device_pixel_ratio": app.primaryScreen().devicePixelRatio()}, ensure_ascii=True))
