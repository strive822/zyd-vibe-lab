"""Exercise the real Qt widget's press/move/release route across four edges."""

from __future__ import annotations

from _paths import SOURCE as SOURCE

import ctypes
import platform
import sys
from ctypes import wintypes

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from main import SAMPLE_TEXT, WIDTH, HEIGHT, VERTICAL_HEIGHT, LeafPrototype


app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
work = app.primaryScreen().availableGeometry()
right_x = work.right() - WIDTH + 1
bottom_y = work.bottom() - VERTICAL_HEIGHT + 1
widget = LeafPrototype(scenario="low")
widget.move(right_x, work.top() + max(34, (work.height() - HEIGHT) // 3))
widget.show()
widget._pulse.stop()
widget._tick.stop()
app.processEvents()


def drag(local: QPoint, target_window: QPoint) -> None:
    QTest.mousePress(widget, Qt.MouseButton.LeftButton, pos=local)
    assert widget._drag_pending and not widget._drag_started
    delta = target_window - widget._drag_origin_window
    target_pointer = widget._drag_origin_global + delta
    move = QMouseEvent(QEvent.Type.MouseMove, QPointF(local), QPointF(target_pointer),
                       Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    app.sendEvent(widget, move)
    assert widget._drag_started and widget.pos() == target_window, (widget.pos(), target_window)
    release = QMouseEvent(QEvent.Type.MouseButtonRelease, QPointF(local), QPointF(target_pointer),
                          Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
    app.sendEvent(widget, release)
    assert not widget._drag_pending


drag(QPoint(272, 130), QPoint(work.left() + 5, widget.y()))
assert widget.dock_edge == "left" and widget.x() == work.left()
assert widget._progress < .01 and widget.mask().contains(QPoint(20, 130))
assert not widget.mask().contains(QPoint(270, 130))
QTest.mouseClick(widget, Qt.MouseButton.LeftButton, pos=QPoint(20, 130))
assert widget._expansion.endValue() == 1.0
widget.set_expansion_progress(1.0)
widget._expansion.stop()

drag(QPoint(200, 90), QPoint(work.left() + 400, work.top() + 3))
assert widget.dock_edge == "top" and widget.y() == work.top() and widget.height() == VERTICAL_HEIGHT
widget.set_expansion_progress(1.0)
assert all(widget._ball_at(widget._ball_center(i).x(), widget._ball_center(i).y()) == i for i in range(5))
widget.set_expansion_progress(0.0)
assert widget.mask().contains(QPoint(150, 24))
assert not widget.mask().contains(QPoint(150, 130))

drag(QPoint(150, 30), QPoint(widget.x(), bottom_y - 3))
assert widget.dock_edge == "bottom" and widget.y() == bottom_y and widget.height() == VERTICAL_HEIGHT
widget.set_expansion_progress(1.0)
assert all(widget._ball_at(widget._ball_center(i).x(), widget._ball_center(i).y()) == i for i in range(5))
widget.set_expansion_progress(0.0)
assert widget.mask().contains(QPoint(150, VERTICAL_HEIGHT - 24))

drag(QPoint(150, VERTICAL_HEIGHT - 30), QPoint(work.left() + 480, work.top() + 380))
assert widget.dock_edge is None and widget._progress > .99
assert widget._visual_edge() == "bottom" and widget.height() == VERTICAL_HEIGHT
assert widget._ball_center(0).y() < widget._shell_target().boundingRect().top()
widget.collapse()
assert widget._progress > .99  # A free floating leaf stays readable.

QApplication.clipboard().clear()
copy_center = widget._ball_center(0)
QTest.mouseClick(widget, Qt.MouseButton.LeftButton, pos=QPoint(round(copy_center.x()), round(copy_center.y())))
assert QApplication.clipboard().text() == SAMPLE_TEXT
widget.set_dock_edge("right")
widget.set_expansion_progress(0.0)
widget.move(right_x, work.top() + 380)
drag(QPoint(272, 130), QPoint(right_x, work.top() + 3))
assert widget.dock_edge == "top"  # Vertical intent wins at the top-right corner.

native_probes = 0
if platform.system() == "Windows":
    class POINT(ctypes.Structure):
        _fields_ = (("x", ctypes.c_long), ("y", ctypes.c_long))

    class RECT(ctypes.Structure):
        _fields_ = (("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long))

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.WindowFromPoint.argtypes = (POINT,)
    user32.WindowFromPoint.restype = ctypes.c_void_p
    user32.GetWindowRect.argtypes = (ctypes.c_void_p, ctypes.POINTER(RECT))
    user32.GetWindowRect.restype = wintypes.BOOL
    widget.move(work.left() + 350, work.top() + 250)
    owner = int(widget.winId())

    def native_hit(local: QPoint, expected: bool) -> None:
        global native_probes
        rect = RECT()
        assert user32.GetWindowRect(ctypes.c_void_p(owner), ctypes.byref(rect))
        ratio = widget.devicePixelRatioF()
        point = POINT(rect.left + round(local.x() * ratio), rect.top + round(local.y() * ratio))
        hit = user32.WindowFromPoint(point)
        assert (hit == owner) == expected, (widget.dock_edge, local, hit, owner)
        native_probes += 1

    for edge in ("right", "left", "top", "bottom"):
        widget.set_dock_edge(edge)
        widget.set_expansion_progress(1.0)
        app.processEvents()
        native_hit(QPoint(150, 130 if edge != "bottom" else 180), True)
        for index in (0, 4):
            center = widget._ball_center(index)
            native_hit(QPoint(round(center.x()), round(center.y())), True)
        native_hit(QPoint(5, 5), False)
        widget.set_expansion_progress(0.0)
        app.processEvents()
        dock = widget._dock_center()
        native_hit(QPoint(round(dock.x()), round(dock.y())), True)
        native_hit(QPoint(150, 130), False)

print(f"drag checks: four edges, corner intent, free position, click-to-expand, copy and {native_probes} native hit probes passed")
widget.close()
