"""Built-in glyphs share the frozen leaf's 1.6 DIP stroke and optical centre."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


def paint_snippet_icon(painter: QPainter, kind: str, color: QColor) -> None:
    pen = QPen(color, 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if kind == "copy":
        painter.drawRoundedRect(QRectF(-8, -6, 11, 13), 2, 2)
        painter.drawRoundedRect(QRectF(-3, -9, 11, 13), 2, 2)
    elif kind == "text":
        for y, end in ((-6, 7), (-1, 5), (4, 2)):
            painter.drawLine(QPointF(-8, y), QPointF(end, y))
        painter.drawLine(QPointF(4, 5), QPointF(7, 8))
    elif kind == "code":
        for start, middle, end_point in (((-3, -6), (-8, 0), (-3, 6)), ((3, -6), (8, 0), (3, 6))):
            painter.drawLine(QPointF(*start), QPointF(*middle))
            painter.drawLine(QPointF(*middle), QPointF(*end_point))
        painter.drawLine(QPointF(2, -8), QPointF(-2, 8))
    elif kind == "check":
        painter.drawLine(QPointF(-7, 0), QPointF(-2, 5))
        painter.drawLine(QPointF(-2, 5), QPointF(8, -6))
    else:
        painter.drawRect(QRectF(-7, -9, 14, 18))
        for y in (-4, 1, 6):
            painter.drawLine(QPointF(-3, y), QPointF(3, y))


def icon_for(kind: str) -> QIcon:
    icon = QIcon()
    for size in (24, 36, 48):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(size / 24, size / 24)
        painter.translate(12, 12)
        paint_snippet_icon(painter, kind, QColor("#58623d"))
        painter.end()
        icon.addPixmap(pixmap)
    return icon
