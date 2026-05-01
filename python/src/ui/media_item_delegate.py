from PySide6.QtWidgets import QStyledItemDelegate, QStyle
from PySide6.QtCore import Qt, QSize, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics

# ── Layout constants ──────────────────────────────────────────────────────────
THUMBNAIL_SIZE = 150   # inner image area (matches listWidget.setIconSize)
PADDING        = 12    # space between cell edge and thumbnail on all sides
TEXT_HEIGHT    = 38    # height reserved for the filename label below the image
CORNER_RADIUS  = 8     # rounded corners on the thumbnail background card

CELL_W = THUMBNAIL_SIZE + PADDING * 2
CELL_H = THUMBNAIL_SIZE + PADDING * 2 + TEXT_HEIGHT

# ── Colours (dark-mode friendly, but readable on light too) ──────────────────
_CLR_CARD_BG   = QColor(40,  40,  44,  220)   # subtle dark card background
_CLR_SELECTED  = QColor(80, 130, 210, 180)     # blue tint when selected
_CLR_HOVER     = QColor(60,  60,  68, 160)     # slightly lighter on hover
_CLR_TEXT      = QColor(230, 230, 230)
_CLR_TEXT_SEL  = QColor(255, 255, 255)


class MediaItemDelegate(QStyledItemDelegate):
    """
    Custom delegate for QListWidget in IconMode.

    Renders each media item as a card:
    ┌──────────────────────┐
    │  (padding)           │
    │    ┌────────────┐    │
    │    │  thumbnail │    │
    │    └────────────┘    │
    │  (padding)           │
    │    filename.jpg      │
    └──────────────────────┘
    """

    def sizeHint(self, option, index) -> QSize:
        return QSize(CELL_W, CELL_H)

    def paint(self, painter: QPainter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        rect: QRect = option.rect
        is_selected = bool(option.state & QStyle.State_Selected)
        is_hovered  = bool(option.state & QStyle.State_MouseOver)

        # ── 1. Card background ────────────────────────────────────────────────
        if is_selected:
            bg = _CLR_SELECTED
        elif is_hovered:
            bg = _CLR_HOVER
        else:
            bg = _CLR_CARD_BG

        painter.setBrush(bg)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(
            rect.adjusted(2, 2, -2, -2),   # small outer margin between cells
            CORNER_RADIUS, CORNER_RADIUS
        )

        # ── 2. Thumbnail ──────────────────────────────────────────────────────
        icon = index.data(Qt.DecorationRole)
        if icon and not icon.isNull():
            # Ask for the actual stored pixmap at its natural size
            pixmap = icon.pixmap(THUMBNAIL_SIZE, THUMBNAIL_SIZE)

            # Centre the (possibly non-square) pixmap inside the thumbnail area
            thumb_area = QRect(
                rect.x() + PADDING,
                rect.y() + PADDING,
                THUMBNAIL_SIZE,
                THUMBNAIL_SIZE,
            )
            px = thumb_area.x() + (thumb_area.width()  - pixmap.width())  // 2
            py = thumb_area.y() + (thumb_area.height() - pixmap.height()) // 2
            painter.drawPixmap(QPoint(px, py), pixmap)

        # ── 3. Filename label ─────────────────────────────────────────────────
        text = index.data(Qt.DisplayRole) or ""
        text_rect = QRect(
            rect.x() + 4,
            rect.y() + PADDING + THUMBNAIL_SIZE + 2,
            rect.width() - 8,
            TEXT_HEIGHT - 4,
        )

        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)

        # Elide the text if it's too long to fit on one line
        fm = QFontMetrics(font)
        elided = fm.elidedText(text, Qt.ElideMiddle, text_rect.width())

        text_color = _CLR_TEXT_SEL if is_selected else _CLR_TEXT
        painter.setPen(QPen(text_color))
        painter.drawText(text_rect, Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap, elided)

        painter.restore()
