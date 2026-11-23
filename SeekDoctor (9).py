import sys
import os
import re
import html
import hmac
import sqlite3
import hashlib
import secrets
import shutil
import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLineEdit, QPushButton, QLabel, QStackedWidget, QScrollArea,
    QFileDialog, QMessageBox, QSizePolicy, QCheckBox, QListWidget, QListWidgetItem,
    QGraphicsDropShadowEffect, QDialog
)
from PyQt5.QtGui import QPixmap, QFont, QPainter, QPainterPath, QIcon, QColor, QPen
from PyQt5.QtCore import Qt, QRectF, QByteArray, QPoint, QSize

try:
    from PyQt5.QtSvg import QSvgRenderer  # used to draw the SeekDoctor logo
except ImportError:  # the app still works, with a simpler logo
    QSvgRenderer = None

# =============================================================================
#  THEME  -  change the look of the whole app here
# =============================================================================
APP_NAME = "SeekDoctor"
APP_TAGLINE = "Find the right doctor, faster"
APP_VERSION = "1.7"
SCHOOL_NAME = "Cavite State University – Bacoor City Campus"
FONT_FAMILY = "Segoe UI"

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "seekdoctor.db")
IMAGES_DIR = os.path.join(APP_DIR, "doctor_images")

# Core brand palette (teal, navy, `magenta, gold)
NAVY = "#081c48"
NAVY_HOVER = "#16306b"
NAVY_PRESSED = "#050f2a"
TEAL = "#25a59f"
TEAL_DARK = "#1b7f7a"
TEAL_LIGHT = "#dff3f1"
MAGENTA = "#9a3558"
MAGENTA_HOVER = "#7d2a47"
MAGENTA_PRESSED = "#63203a"
GOLD = "#eebf2d"

THEMES = {
    "light": {
        "bg": "#eef6f5",
        "card": "#ffffff",
        "card_tint": "#f7fbfb",
        "input_bg": "#ffffff",
        "input_error_bg": "#fff8fa",
        "border": "#cfe3e1",
        "text": "#1f2a37",
        "heading": NAVY,
        "muted": "#5b6b7a",
        "pill_bg": TEAL_LIGHT,
        "pill_fg": TEAL_DARK,
        "chip_bg": TEAL_LIGHT,
        "chip_fg": TEAL_DARK,
        "outline_bg": "#ffffff",
        "outline_hover": TEAL_LIGHT,
        "outline_pressed": "#c9e8e5",
        "outline_fg": NAVY,
        "scroll_handle": "#b7d3d0",
        "error_bg": "#fde8ee",
        "ok_bg": "#e3f6ec",
        "ok_fg": "#1b6b43",
        "shadow_alpha": 22,
    },
    "dark": {
        "bg": "#061126",
        "card": "#0d1d3d",
        "card_tint": "#12264f",
        "input_bg": "#0a1733",
        "input_error_bg": "#2b1222",
        "border": "#1e3d6b",
        "text": "#e6f1f5",
        "heading": "#7de3de",
        "muted": "#9cb3c9",
        "pill_bg": "#123842",
        "pill_fg": "#7de3de",
        "chip_bg": "#123842",
        "chip_fg": "#8beae5",
        "outline_bg": "#0d1d3d",
        "outline_hover": "#16305c",
        "outline_pressed": "#1c3d75",
        "outline_fg": "#e6f1f5",
        "scroll_handle": "#254c7a",
        "error_bg": "#47192c",
        "ok_bg": "#113b2d",
        "ok_fg": "#6ee7b7",
        "shadow_alpha": 70,
    },
}

CURRENT_THEME = "light"


def palette():
    return THEMES[CURRENT_THEME]


def set_theme_mode(mode):
    global CURRENT_THEME
    if mode in THEMES:
        CURRENT_THEME = mode


# =============================================================================
#  LOGO / APPLICATION ICON
# =============================================================================
ICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#2fc0b8"/>
      <stop offset="1" stop-color="#081c48"/>
    </linearGradient>
  </defs>
  <rect width="128" height="128" rx="28" ry="28" fill="url(#bg)"/>
  <line x1="82" y1="82" x2="108" y2="108" stroke="#eebf2d" stroke-width="13" stroke-linecap="round"/>
  <circle cx="55" cy="55" r="33" fill="#ffffff" stroke="#eebf2d" stroke-width="9"/>
  <rect x="49" y="36" width="12" height="38" rx="3" fill="#9a3558"/>
  <rect x="36" y="49" width="38" height="12" rx="3" fill="#9a3558"/>
</svg>
"""


def _fallback_logo_pixmap(size):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    tile = QPainterPath()
    tile.addRoundedRect(QRectF(0, 0, size, size), size * 0.22, size * 0.22)
    painter.fillPath(tile, QColor(TEAL_DARK))
    cross = QPainterPath()
    arm, thick = size * 0.56, size * 0.16
    cross.addRoundedRect(QRectF((size - thick) / 2, (size - arm) / 2, thick, arm), thick / 4, thick / 4)
    cross.addRoundedRect(QRectF((size - arm) / 2, (size - thick) / 2, arm, thick), thick / 4, thick / 4)
    painter.fillPath(cross, QColor("#ffffff"))
    painter.end()
    return pixmap


def make_logo_pixmap(size):
    if QSvgRenderer is None:
        return _fallback_logo_pixmap(size)
    renderer = QSvgRenderer(QByteArray(ICON_SVG.encode("utf-8")))
    if not renderer.isValid():
        return _fallback_logo_pixmap(size)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return pixmap


def make_app_icon():
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(make_logo_pixmap(size))
    return icon


def circular_pixmap(image_path, size):
    source = QPixmap(image_path)
    if source.isNull():
        return None
    scaled = source.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    clip = QPainterPath()
    clip.addEllipse(QRectF(0, 0, size, size))
    painter.setClipPath(clip)
    painter.drawPixmap(-(scaled.width() - size) // 2, -(scaled.height() - size) // 2, scaled)
    painter.end()
    return result


def store_doctor_image(source_path):
    if not source_path:
        return ""
    try:
        source = os.path.abspath(source_path)
        if not os.path.isfile(source):
            return source_path
        images_dir = os.path.abspath(IMAGES_DIR)
        if os.path.dirname(source) == images_dir:
            return source
        os.makedirs(images_dir, exist_ok=True)
        extension = os.path.splitext(source)[1].lower() or ".png"
        destination = os.path.join(images_dir, f"doctor_{secrets.token_hex(6)}{extension}")
        shutil.copy2(source, destination)
        return destination
    except (OSError, shutil.Error) as error:
        print(f"Could not copy the image: {error}")
        return source_path


# --- Database Manager Class ---
class DatabaseManager:
    def __init__(self, db_name=None):
        self.db_name = db_name or DB_PATH
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_table()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            raise RuntimeError(f"Could not open the database file:\n{self.db_name}\n\n{e}")

    def _create_table(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS doctors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    specialty TEXT,
                    hospital TEXT,
                    schedule TEXT,
                    contact TEXT,
                    image_path TEXT
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"The database could not be prepared:\n{self.db_name}\n\n{e}")

    @staticmethod
    def _hash_password(password, salt_hex):
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 200_000
        ).hex()

    def create_user(self, full_name, email, password):
        email = email.strip().lower()
        salt_hex = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt_hex)
        try:
            self.cursor.execute(
                "INSERT INTO users (full_name, email, password_hash, salt) VALUES (?, ?, ?, ?)",
                (full_name.strip(), email, password_hash, salt_hex)
            )
            self.conn.commit()
            return True, "Account created successfully."
        except sqlite3.IntegrityError:
            return False, "An account with this email already exists."
        except sqlite3.Error:
            return False, "Could not create the account. Please try again."

    def verify_user(self, email, password):
        email = email.strip().lower()
        try:
            self.cursor.execute(
                "SELECT id, full_name, email, password_hash, salt FROM users WHERE email = ?",
                (email,)
            )
            row = self.cursor.fetchone()
        except sqlite3.Error:
            return None
        if not row:
            return None
        expected_hash = self._hash_password(password, row[4])
        if hmac.compare_digest(expected_hash, row[3]):
            return {"id": row[0], "full_name": row[1], "email": row[2]}
        return None

    def add_doctor(self, name, specialty, hospital, schedule, contact, image_path):
        try:
            self.cursor.execute("""
                INSERT INTO doctors (name, specialty, hospital, schedule, contact, image_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, specialty, hospital, schedule, contact, image_path))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def get_doctor_by_id(self, doctor_id):
        try:
            self.cursor.execute(
                "SELECT id, name, specialty, hospital, schedule, contact, image_path FROM doctors WHERE id = ?",
                (doctor_id,)
            )
            row = self.cursor.fetchone()
            if row:
                return {
                    "id": row[0], "name": row[1], "specialty": row[2],
                    "hospital": row[3], "schedule": row[4], "contact": row[5],
                    "image_path": row[6]
                }
            return None
        except sqlite3.Error:
            return None

    def get_recent_doctors(self, limit=4):
        try:
            self.cursor.execute(
                "SELECT id, name, specialty, hospital, schedule, contact, image_path "
                "FROM doctors ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            rows = self.cursor.fetchall()
            return [
                {
                    "id": r[0], "name": r[1], "specialty": r[2],
                    "hospital": r[3], "schedule": r[4], "contact": r[5],
                    "image_path": r[6]
                }
                for r in rows
            ]
        except sqlite3.Error:
            return []

    def update_doctor(self, doctor_id, name, specialty, hospital, schedule, contact, image_path):
        try:
            self.cursor.execute("""
                UPDATE doctors SET name = ?, specialty = ?, hospital = ?, schedule = ?, contact = ?, image_path = ?
                WHERE id = ?
            """, (name, specialty, hospital, schedule, contact, image_path, doctor_id))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def delete_doctor(self, doctor_id):
        try:
            self.cursor.execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error:
            return False

    @staticmethod
    def _like_escape(text):
        return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    @classmethod
    def _word_match(cls, column, text, params):
        safe = cls._like_escape(text.strip())
        condition = f"{column} LIKE ? ESCAPE '\\' OR {column} LIKE ? ESCAPE '\\'"
        params.extend([f"{safe}%", f"% {safe}%"])
        if len(safe) >= 3:
            condition += f" OR {column} LIKE ? ESCAPE '\\'"
            params.append(f"%{safe}%")
        return f"({condition})"

    def search_doctors(self, specialty="", hospital=""):
        query = "SELECT id, name, specialty, hospital, schedule, contact, image_path FROM doctors WHERE 1=1"
        params = []
        if specialty:
            query += " AND " + self._word_match("specialty", specialty, params)
        if hospital:
            query += " AND " + self._word_match("hospital", hospital, params)
        query += " ORDER BY name COLLATE NOCASE"
        try:
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return [
                {
                    "id": r[0], "name": r[1], "specialty": r[2],
                    "hospital": r[3], "schedule": r[4], "contact": r[5],
                    "image_path": r[6]
                }
                for r in rows
            ]
        except sqlite3.Error:
            return []

    def count_doctors(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM doctors")
            return self.cursor.fetchone()[0]
        except sqlite3.Error:
            return 0

    def get_distinct_counts(self, column):
        if column not in ("specialty", "hospital"):
            raise ValueError("column must be 'specialty' or 'hospital'")
        try:
            self.cursor.execute(
                f"SELECT TRIM({column}), COUNT(*) FROM doctors "
                f"WHERE {column} IS NOT NULL AND TRIM({column}) != '' "
                f"GROUP BY LOWER(TRIM({column})) ORDER BY LOWER(TRIM({column}))"
            )
            return [(value, count) for value, count in self.cursor.fetchall()]
        except sqlite3.Error:
            return []

    def doctor_exists(self, name, hospital, exclude_id=None):
        sql = ("SELECT 1 FROM doctors WHERE LOWER(TRIM(name)) = ? "
               "AND LOWER(TRIM(COALESCE(hospital, ''))) = ?")
        params = [name.strip().lower(), hospital.strip().lower()]
        if exclude_id is not None:
            sql += " AND id != ?"
            params.append(exclude_id)
        try:
            self.cursor.execute(sql + " LIMIT 1", params)
            return self.cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    def close(self):
        if self.conn:
            self.conn.close()


# =============================================================================
#  STYLE HELPERS (THEME-AWARE)
# =============================================================================
def app_stylesheet():
    p = palette()
    return f"""
        QMainWindow {{ background-color: {p["bg"]}; }}
        QDialog {{ background-color: {p["bg"]}; }}
        QToolTip {{
            background-color: {NAVY};
            color: #ffffff;
            border: 1px solid {GOLD};
            border-radius: 6px;
            padding: 5px 10px;
        }}
        QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px 2px; }}
        QScrollBar::handle:vertical {{ background: {p["scroll_handle"]}; border-radius: 5px; min-height: 32px; }}
        QScrollBar::handle:vertical:hover {{ background: {TEAL}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
    """


def input_qss():
    p = palette()
    return f"""
        QLineEdit {{
            background-color: {p["input_bg"]};
            color: {p["text"]};
            border: 2px solid {p["border"]};
            border-radius: 10px;
            padding: 4px 12px;
            selection-background-color: {TEAL};
        }}
        QLineEdit:focus {{
            border: 2px solid {TEAL};
            background-color: {p["card_tint"]};
        }}
    """


def input_error_qss():
    p = palette()
    return input_qss() + f"""
        QLineEdit {{ border: 2px solid {MAGENTA}; background-color: {p["input_error_bg"]}; }}
        QLineEdit:focus {{ border: 2px solid {MAGENTA}; }}
    """


def card_qss():
    p = palette()
    return f"""
        QFrame#card {{
            background-color: {p["card"]};
            border: 2px solid {p["border"]};
            border-radius: 18px;
        }}
    """


def stat_card_qss():
    p = palette()
    return f"""
        QFrame#statCard {{
            background-color: {p["card"]};
            border: 2px solid {p["border"]};
            border-radius: 14px;
        }}
        QFrame#statCard:hover {{
            border: 2px solid {TEAL};
            background-color: {p["card_tint"]};
        }}
    """


def doctor_card_qss():
    p = palette()
    return f"""
        QFrame#doctorCard {{
            background-color: {p["card"]};
            border: 2px solid {p["border"]};
            border-radius: 14px;
        }}
        QFrame#doctorCard:hover {{
            border: 2px solid {TEAL};
            background-color: {p["card_tint"]};
        }}
    """


def recent_row_qss():
    p = palette()
    return f"""
        QFrame#recentRow {{
            background-color: {p["card_tint"]};
            border: 1px solid {p["border"]};
            border-radius: 12px;
        }}
        QFrame#recentRow:hover {{
            border: 1px solid {TEAL};
            background-color: {p["pill_bg"]};
        }}
    """


def pill_qss():
    p = palette()
    return f"""
        background-color: {p["pill_bg"]};
        color: {p["pill_fg"]};
        border-radius: 10px;
        padding: 2px 9px;
    """


def header_qss():
    return f"""
        QFrame#headerBar {{
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {NAVY}, stop:1 {TEAL_DARK});
            border-bottom: 3px solid {GOLD};
        }}
        QLabel#brandTitle {{ color: #ffffff; background: transparent; }}
        QLabel#brandTagline {{ color: #bfe8e4; background: transparent; }}
        QLabel#userChip {{
            color: #ffffff;
            background-color: rgba(255, 255, 255, 38);
            border: 1px solid rgba(255, 255, 255, 80);
            border-radius: 15px;
            padding: 2px 14px;
        }}
        QPushButton#navBtn {{
            color: #ffffff;
            background-color: transparent;
            border: 2px solid rgba(255, 255, 255, 120);
            border-radius: 15px;
            padding: 2px 14px;
            outline: none;
        }}
        QPushButton#navBtn:hover {{ background-color: rgba(255, 255, 255, 40); }}
        QPushButton#navBtn:pressed {{ background-color: rgba(255, 255, 255, 70); }}
        QPushButton#navBtn[active="true"] {{
            background-color: {GOLD};
            color: {NAVY};
            border: 2px solid {GOLD};
        }}
        QPushButton#navBtn:focus {{ border: 2px solid {GOLD}; }}
    """


def footer_qss():
    return f"""
        QFrame#footerBar {{
            background-color: {NAVY};
            border-top: 3px solid {TEAL};
        }}
        QFrame#footerBar QLabel {{ color: #b8c7e0; background: transparent; }}
    """


def options_popup_qss():
    p = palette()
    return f"""
        QFrame#optionsPopup {{
            background-color: {p["card"]};
            border: 2px solid {TEAL};
            border-radius: 10px;
        }}
        QLabel#optionsTitle {{ color: {p["muted"]}; background: transparent; padding: 2px 4px; }}
        QLabel#optionsEmpty {{ color: {p["muted"]}; background: transparent; padding: 6px 4px; }}
        QListWidget {{ background: transparent; border: none; outline: 0; }}
        QListWidget::item {{ padding-left: 12px; border-radius: 8px; color: {p["text"]}; }}
        QListWidget::item:hover {{ background-color: {p["pill_bg"]}; color: {p["heading"]}; }}
        QListWidget::item:selected {{ background-color: {p["pill_bg"]}; color: {p["heading"]}; }}
    """


def apply_card_shadow(widget, blur=18, y_offset=4, alpha=None):
    p = palette()
    eff_alpha = p["shadow_alpha"] if alpha is None else alpha
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, y_offset)
    shadow.setColor(QColor(4, 14, 36, eff_alpha))
    widget.setGraphicsEffect(shadow)


def _button_qss(bg, hover, pressed, fg="#ffffff", border="transparent", focus_border=GOLD):
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {fg};
            border: 2px solid {border};
            border-radius: 10px;
            padding: 4px 16px;
            outline: none;
        }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {pressed}; }}
        QPushButton:focus {{ border: 2px solid {focus_border}; }}
    """


def button_styles():
    p = palette()
    return {
        "primary": _button_qss(NAVY, NAVY_HOVER, NAVY_PRESSED, fg="#ffffff", border=TEAL if CURRENT_THEME == "dark" else "transparent"),
        "accent": _button_qss(MAGENTA, MAGENTA_HOVER, MAGENTA_PRESSED),
        "teal": _button_qss(TEAL_DARK, "#16696a", "#115150"),
        "outline": _button_qss(
            p["outline_bg"], p["outline_hover"], p["outline_pressed"],
            fg=p["outline_fg"], border=TEAL, focus_border=GOLD
        ),
    }


def style_button(button, kind="primary"):
    button.setProperty("btnKind", kind)
    button.setStyleSheet(button_styles()[kind])


def make_label(text, size=10, bold=False, color=None, center=False):
    p = palette()
    resolved_color = p["text"] if color is None else color
    label = QLabel(text)
    label.setTextFormat(Qt.PlainText)
    label.setFont(QFont(FONT_FAMILY, size, QFont.Bold if bold else QFont.Normal))
    label.setStyleSheet(f"color: {resolved_color}; background: transparent;")
    if center:
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
    return label


def _reset_invalid(field):
    if field.property("invalid"):
        field.setProperty("invalid", False)
        field.setStyleSheet(input_qss())


def flag_invalid(field):
    field.setProperty("invalid", True)
    field.setStyleSheet(input_error_qss())
    field.setFocus()


def make_input(placeholder, password=False):
    line_edit = QLineEdit()
    line_edit.setPlaceholderText(placeholder)
    line_edit.setFixedHeight(42)
    line_edit.setFont(QFont(FONT_FAMILY, 11))
    if password:
        line_edit.setEchoMode(QLineEdit.Password)
    line_edit.setStyleSheet(input_qss())
    line_edit.textChanged.connect(lambda _text, f=line_edit: _reset_invalid(f))
    return line_edit


def add_field(layout, caption, placeholder="", required=False, password=False):
    group = QVBoxLayout()
    group.setSpacing(4)
    lbl = make_label(caption + (" *" if required else ""), 9, True, palette()["heading"])
    lbl.setProperty("role", "fieldCaption")
    group.addWidget(lbl)
    field = make_input(placeholder, password)
    group.addWidget(field)
    layout.addLayout(group)
    return field


def make_show_password_checkbox(*fields):
    box = QCheckBox("Show password")
    box.setCursor(Qt.PointingHandCursor)
    box.setFocusPolicy(Qt.TabFocus)
    box.setFont(QFont(FONT_FAMILY, 9))
    box.setStyleSheet(f"QCheckBox {{ color: {palette()['muted']}; background: transparent; spacing: 6px; }}")

    def toggle(checked):
        mode = QLineEdit.Normal if checked else QLineEdit.Password
        for field in fields:
            field.setEchoMode(mode)

    box.toggled.connect(toggle)
    return box


def make_arrow_icon():
    size = 20
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor("#7de3de" if CURRENT_THEME == "dark" else TEAL_DARK))
    pen.setWidthF(2.4)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.drawLine(5, 8, 10, 13)
    painter.drawLine(10, 13, 15, 8)
    painter.end()
    return QIcon(pixmap)


class OptionsPopup(QFrame):
    ROW_HEIGHT = 40
    MAX_ROWS = 6

    def __init__(self, line_edit):
        super().__init__(line_edit, Qt.Popup)
        self.line_edit = line_edit
        self.options = []
        self.noun = "options"
        self.setObjectName("optionsPopup")
        self.apply_theme()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.title_label = QLabel()
        self.title_label.setObjectName("optionsTitle")
        self.title_label.setFont(QFont(FONT_FAMILY, 9, QFont.Bold))
        layout.addWidget(self.title_label)

        self.empty_label = QLabel()
        self.empty_label.setObjectName("optionsEmpty")
        self.empty_label.setFont(QFont(FONT_FAMILY, 10))
        self.empty_label.setWordWrap(True)
        layout.addWidget(self.empty_label)

        self.list = QListWidget()
        self.list.setFont(QFont(FONT_FAMILY, 11))
        self.list.setFrameShape(QFrame.NoFrame)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.setMouseTracking(True)
        self.list.setCursor(Qt.PointingHandCursor)
        self.list.itemClicked.connect(self._picked)
        layout.addWidget(self.list)

    def apply_theme(self):
        self.setStyleSheet(options_popup_qss())

    def set_options(self, options, noun):
        self.options = list(options)
        self.noun = noun

    def open_list(self):
        self.apply_theme()
        typed = self.line_edit.text().strip().lower()
        self.list.clear()
        for value, count in self.options:
            item = QListWidgetItem(f"{value}   \u2014   {count} doctor{'s' if count != 1 else ''}")
            item.setData(Qt.UserRole, value)
            item.setSizeHint(QSize(0, self.ROW_HEIGHT))
            self.list.addItem(item)
            if typed and value.lower() == typed:
                self.list.setCurrentItem(item)

        has_options = bool(self.options)
        if has_options:
            self.title_label.setText(f"Saved {self.noun} ({len(self.options)}) - click one to use it")
        else:
            self.title_label.setText(f"Saved {self.noun}")
            self.empty_label.setText(f"No {self.noun} saved yet. Add a doctor first, or just type your own.")
        self.empty_label.setVisible(not has_options)
        self.list.setVisible(has_options)
        self.list.setFixedHeight(min(len(self.options), self.MAX_ROWS) * self.ROW_HEIGHT + 4)

        self.setFixedWidth(max(self.line_edit.width(), 280))
        self.adjustSize()

        position = self.line_edit.mapToGlobal(QPoint(0, self.line_edit.height() + 4))
        screen = QApplication.primaryScreen()
        if screen is not None and position.y() + self.height() > screen.availableGeometry().bottom():
            position = self.line_edit.mapToGlobal(QPoint(0, -self.height() - 4))
        self.move(position)
        self.show()

    def _picked(self, item):
        self.line_edit.setText(item.data(Qt.UserRole))
        self.hide()
        self.line_edit.setFocus()


def set_options(line_edit, options, noun):
    popup = line_edit.__dict__.get("options_popup")
    if popup is None:
        popup = OptionsPopup(line_edit)
        line_edit.options_popup = popup
        arrow = line_edit.addAction(make_arrow_icon(), QLineEdit.TrailingPosition)
        arrow.setToolTip(f"Show the saved {noun}")
        arrow.triggered.connect(lambda checked=False, p=popup: p.open_list())
    else:
        popup.apply_theme()
    popup.set_options(options, noun)


def make_button(text, kind="primary", width=None, height=42, size=11):
    button = QPushButton(text)
    button.setCursor(Qt.PointingHandCursor)
    button.setFocusPolicy(Qt.TabFocus)
    button.setFont(QFont(FONT_FAMILY, size, QFont.Bold))
    button.setFixedHeight(height)
    if width:
        button.setFixedWidth(width)
    style_button(button, kind)
    return button


def make_link_button(text):
    button = QPushButton(text)
    button.setFlat(True)
    button.setCursor(Qt.PointingHandCursor)
    button.setFocusPolicy(Qt.TabFocus)
    button.setFont(QFont(FONT_FAMILY, 10, QFont.Bold))
    button.setProperty("btnKind", "link")
    link_color = "#7de3de" if CURRENT_THEME == "dark" else TEAL_DARK
    button.setStyleSheet(f"""
        QPushButton {{ color: {link_color}; border: none; text-decoration: underline; background: transparent; outline: none; }}
        QPushButton:hover {{ color: {GOLD}; }}
    """)
    return button


def make_link_row(prompt, link_text, slot):
    row = QHBoxLayout()
    row.setSpacing(6)
    row.addStretch(1)
    lbl = make_label(prompt, 10, False, palette()["muted"])
    lbl.setProperty("role", "muted")
    row.addWidget(lbl)
    link = make_link_button(link_text)
    link.clicked.connect(slot)
    row.addWidget(link)
    row.addStretch(1)
    return row


def make_card(width, shadow=True):
    card = QFrame()
    card.setObjectName("card")
    card.setFixedWidth(width)
    card.setStyleSheet(card_qss())
    if shadow:
        apply_card_shadow(card)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(32, 26, 32, 26)
    layout.setSpacing(12)
    return card, layout


def place_card(page, card):
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setStyleSheet(
        "QScrollArea { border: none; background: transparent; }"
        "QWidget#pageInner { background: transparent; }"
    )
    inner = QWidget()
    inner.setObjectName("pageInner")
    inner_layout = QVBoxLayout(inner)
    inner_layout.setContentsMargins(24, 18, 24, 18)
    inner_layout.addStretch(1)
    inner_layout.addWidget(card, alignment=Qt.AlignHCenter)
    inner_layout.addStretch(1)
    scroll.setWidget(inner)

    outer = QVBoxLayout(page)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.addWidget(scroll)


class StatusLabel(QLabel):
    def __init__(self):
        super().__init__("")
        self.setTextFormat(Qt.PlainText)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont(FONT_FAMILY, 10, QFont.Bold))
        self.setVisible(False)
        self._kind = None
        self._message = ""

    def _apply_style(self):
        p = palette()
        if self._kind == "error":
            self.setStyleSheet(
                f"background-color: {p['error_bg']}; color: {'#ff9eb8' if CURRENT_THEME == 'dark' else MAGENTA}; "
                f"border-radius: 8px; padding: 8px 12px;"
            )
        elif self._kind == "success":
            self.setStyleSheet(
                f"background-color: {p['ok_bg']}; color: {p['ok_fg']}; "
                f"border-radius: 8px; padding: 8px 12px;"
            )

    def refresh_theme(self):
        if self.isVisible() and self._kind:
            self._apply_style()

    def show_error(self, message):
        self._message = message
        self._kind = "error"
        self.setText(message)
        self._apply_style()
        self.setVisible(True)

    def show_success(self, message):
        self._message = message
        self._kind = "success"
        self.setText(message)
        self._apply_style()
        self.setVisible(True)

    def clear_status(self):
        self._message = ""
        self._kind = None
        self.setText("")
        self.setVisible(False)


# =============================================================================
#  CLICK-TO-VIEW DOCTOR DETAILS DIALOG
# =============================================================================
class DoctorDetailsDialog(QDialog):
    AVATAR_SIZE = 92

    def __init__(self, doctor, main_window, parent=None):
        super().__init__(parent)
        self.doctor = doctor
        self.main_window = main_window
        self.setWindowTitle(f"{APP_NAME} - {doctor.get('name') or 'Doctor Details'}")
        self.setMinimumWidth(440)
        self.setMaximumWidth(540)
        self.init_ui()

    def _make_avatar(self):
        size = self.AVATAR_SIZE
        avatar = QLabel()
        avatar.setFixedSize(size, size)
        avatar.setAlignment(Qt.AlignCenter)

        photo = None
        image_path = self.doctor.get("image_path")
        if image_path and os.path.exists(image_path):
            photo = circular_pixmap(image_path, size)

        if photo is not None:
            avatar.setPixmap(photo)
        else:
            words = [w for w in (self.doctor.get("name") or "").replace("Dr.", "").split() if w]
            initials = "".join(w[0] for w in words[:2]).upper() or "?"
            avatar.setText(initials)
            avatar.setFont(QFont(FONT_FAMILY, 26, QFont.Bold))
            avatar.setStyleSheet(
                f"background-color: {TEAL}; color: #ffffff; border-radius: {size // 2}px;"
            )
        return avatar

    def init_ui(self):
        p = palette()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)

        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(card_qss())
        apply_card_shadow(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(14)

        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        top_row.addWidget(self._make_avatar(), alignment=Qt.AlignTop)

        title_col = QVBoxLayout()
        title_col.setSpacing(6)
        name_lbl = make_label(self.doctor.get("name") or "N/A", 18, True, p["heading"])
        name_lbl.setWordWrap(True)
        title_col.addWidget(name_lbl)

        specialty = self.doctor.get("specialty")
        if specialty:
            pill = QLabel(specialty)
            pill.setTextFormat(Qt.PlainText)
            pill.setFont(QFont(FONT_FAMILY, 9, QFont.Bold))
            pill.setStyleSheet(pill_qss())
            pill.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            title_col.addWidget(pill)

        title_col.addStretch(1)
        top_row.addLayout(title_col, 1)
        layout.addLayout(top_row)

        info_box = QFrame()
        info_box.setStyleSheet(
            f"QFrame {{ background-color: {p['card_tint']}; border: 1px solid {p['border']}; border-radius: 12px; }}"
        )
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(14, 12, 14, 12)
        info_layout.setSpacing(8)

        for caption, key in (("Hospital", "hospital"), ("Schedule", "schedule"), ("Contact", "contact")):
            value = self.doctor.get(key) or "N/A"
            row_lbl = QLabel(f"<b>{caption}:</b> {html.escape(str(value))}")
            row_lbl.setTextFormat(Qt.RichText)
            row_lbl.setFont(QFont(FONT_FAMILY, 10))
            row_lbl.setStyleSheet(f"color: {p['text']}; background: transparent;")
            row_lbl.setWordWrap(True)
            row_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            info_layout.addWidget(row_lbl)

        layout.addWidget(info_box)

        self.status = StatusLabel()
        layout.addWidget(self.status)

        util_row = QHBoxLayout()
        util_row.setSpacing(10)

        copy_btn = make_button("Copy Contact", "teal", height=38, size=10)
        copy_btn.setToolTip("Copy contact details to clipboard")
        copy_btn.clicked.connect(self._copy_contact)
        util_row.addWidget(copy_btn)

        close_btn = make_button("Close", "outline", width=110, height=38, size=10)
        close_btn.clicked.connect(self.accept)
        util_row.addWidget(close_btn)
        layout.addLayout(util_row)

        manage_row = QHBoxLayout()
        manage_row.setSpacing(10)

        edit_btn = make_button("Edit Doctor", "primary", height=40, size=10)
        edit_btn.clicked.connect(self._handle_edit)
        manage_row.addWidget(edit_btn)

        delete_btn = make_button("Delete", "accent", width=110, height=40, size=10)
        delete_btn.clicked.connect(self._handle_delete)
        manage_row.addWidget(delete_btn)
        layout.addLayout(manage_row)

        outer.addWidget(card)

    def _copy_contact(self):
        contact = (self.doctor.get("contact") or "").strip()
        if not contact:
            self.status.show_error("No contact details available to copy.")
            return
        QApplication.clipboard().setText(contact)
        self.status.show_success("Contact details copied to clipboard.")

    def _handle_edit(self):
        doc_id = self.doctor.get("id")
        self.accept()
        if doc_id is not None:
            self.main_window.edit_doctor(doc_id)

    def _handle_delete(self):
        doc_id = self.doctor.get("id")
        self.accept()
        if doc_id is not None:
            self.main_window.delete_doctor(doc_id)


# =============================================================================
#  HEADER AND FOOTER
# =============================================================================
class HeaderBar(QFrame):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("headerBar")
        self.setFixedHeight(76)
        self.setStyleSheet(header_qss())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(10)

        logo = QLabel()
        logo.setPixmap(make_logo_pixmap(48))
        logo.setFixedSize(48, 48)
        layout.addWidget(logo, 0, Qt.AlignVCenter)

        title = QLabel(APP_NAME)
        title.setObjectName("brandTitle")
        title.setFont(QFont(FONT_FAMILY, 18, QFont.Bold))
        title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        tagline = QLabel(APP_TAGLINE)
        tagline.setObjectName("brandTagline")
        tagline.setFont(QFont(FONT_FAMILY, 9))
        tagline.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        text_column = QVBoxLayout()
        text_column.setSpacing(0)
        text_column.addStretch(1)
        text_column.addWidget(title)
        text_column.addWidget(tagline)
        text_column.addStretch(1)
        layout.addLayout(text_column)

        layout.addStretch(1)

        self.user_chip = QLabel("")
        self.user_chip.setObjectName("userChip")
        self.user_chip.setFont(QFont(FONT_FAMILY, 10, QFont.Bold))
        self.user_chip.setFixedHeight(30)
        layout.addWidget(self.user_chip, 0, Qt.AlignVCenter)

        self.theme_button = QPushButton()
        self.theme_button.setObjectName("navBtn")
        self.theme_button.setCursor(Qt.PointingHandCursor)
        self.theme_button.setFocusPolicy(Qt.TabFocus)
        self.theme_button.setFont(QFont(FONT_FAMILY, 9, QFont.Bold))
        self.theme_button.setFixedHeight(32)
        self.theme_button.setToolTip("Switch between Light and Dark theme")
        self.theme_button.clicked.connect(self.main_window.toggle_theme)
        layout.addWidget(self.theme_button, 0, Qt.AlignVCenter)
        self.update_theme_button_label()

        self.home_button = QPushButton("Home")
        self.home_button.setObjectName("navBtn")
        self.home_button.setCursor(Qt.PointingHandCursor)
        self.home_button.setFocusPolicy(Qt.TabFocus)
        self.home_button.setFont(QFont(FONT_FAMILY, 10, QFont.Bold))
        self.home_button.setFixedHeight(32)
        self.home_button.setToolTip("Go to the home page")
        self.home_button.clicked.connect(self.main_window.show_home_page)
        layout.addWidget(self.home_button, 0, Qt.AlignVCenter)

        self.logout_button = QPushButton("Log out")
        self.logout_button.setObjectName("navBtn")
        self.logout_button.setCursor(Qt.PointingHandCursor)
        self.logout_button.setFocusPolicy(Qt.TabFocus)
        self.logout_button.setFont(QFont(FONT_FAMILY, 10, QFont.Bold))
        self.logout_button.setFixedHeight(32)
        self.logout_button.setToolTip("Sign out of your account")
        self.logout_button.clicked.connect(self.main_window.logout)
        layout.addWidget(self.logout_button, 0, Qt.AlignVCenter)

        self.set_user(None)

    def update_theme_button_label(self):
        if CURRENT_THEME == "dark":
            self.theme_button.setText("Light Mode")
        else:
            self.theme_button.setText("Dark Mode")

    def apply_theme(self):
        self.setStyleSheet(header_qss())
        self.update_theme_button_label()

    def set_user(self, user):
        logged_in = user is not None
        if logged_in:
            self.user_chip.setText(user["full_name"])
            self.user_chip.setToolTip(user["email"])
        self.user_chip.setVisible(logged_in)
        self.home_button.setVisible(logged_in)
        self.logout_button.setVisible(logged_in)
        if not logged_in:
            self.set_home_active(False)

    def set_home_active(self, active):
        self.home_button.setProperty("active", bool(active))
        self.home_button.style().unpolish(self.home_button)
        self.home_button.style().polish(self.home_button)


class FooterBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("footerBar")
        self.setFixedHeight(38)
        self.setStyleSheet(footer_qss())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(8)

        mini_logo = QLabel()
        mini_logo.setPixmap(make_logo_pixmap(18))
        mini_logo.setFixedSize(18, 18)
        layout.addWidget(mini_logo)

        copyright_label = QLabel(f"© {datetime.date.today().year} {APP_NAME}")
        copyright_label.setFont(QFont(FONT_FAMILY, 9, QFont.Bold))
        layout.addWidget(copyright_label)

        layout.addStretch(1)
        school_label = QLabel(SCHOOL_NAME)
        school_label.setFont(QFont(FONT_FAMILY, 9))
        layout.addWidget(school_label)
        layout.addStretch(1)

        version_label = QLabel(f"v{APP_VERSION}  ·  Python · PyQt5 · SQLite")
        version_label.setFont(QFont(FONT_FAMILY, 9))
        layout.addWidget(version_label)

    def apply_theme(self):
        self.setStyleSheet(footer_qss())


# =============================================================================
#  PAGES
# =============================================================================
class HomePage(QWidget):
    DEFAULT_GREETING = "Welcome to SeekDoctor"
    DEFAULT_SUBTITLE = "Find trusted doctors by specialty or hospital, or manage your directory."

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()

    def init_ui(self):
        p = palette()
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QWidget#homeInner { background: transparent; }"
        )

        inner = QWidget()
        inner.setObjectName("homeInner")
        outer = QVBoxLayout(inner)
        outer.setContentsMargins(28, 22, 28, 24)
        outer.setSpacing(16)

        container = QWidget()
        container.setMaximumWidth(780)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.hero_card = QFrame()
        self.hero_card.setObjectName("card")
        self.hero_card.setStyleSheet(card_qss())
        apply_card_shadow(self.hero_card)
        hero_layout = QVBoxLayout(self.hero_card)
        hero_layout.setContentsMargins(32, 26, 32, 26)
        hero_layout.setSpacing(10)

        badge_row = QHBoxLayout()
        badge_row.addStretch(1)
        hero_logo = QLabel()
        hero_logo.setPixmap(make_logo_pixmap(64))
        hero_logo.setFixedSize(64, 64)
        badge_row.addWidget(hero_logo)
        badge_row.addStretch(1)
        hero_layout.addLayout(badge_row)

        self.greeting_label = make_label(self.DEFAULT_GREETING, 22, True, p["heading"], center=True)
        self.subtitle_label = make_label(self.DEFAULT_SUBTITLE, 10, False, p["muted"], center=True)
        hero_layout.addWidget(self.greeting_label)
        hero_layout.addWidget(self.subtitle_label)
        hero_layout.addSpacing(6)

        cta_row = QHBoxLayout()
        cta_row.setSpacing(12)

        find_btn = make_button("Find a Doctor", "primary", height=46, size=12)
        find_btn.setToolTip("Search doctors by specialty or hospital")
        find_btn.clicked.connect(self.main_window.show_landing_page)
        cta_row.addWidget(find_btn)

        add_btn = make_button("Add Doctor", "accent", height=46, size=12)
        add_btn.setToolTip("Add a new doctor record")
        add_btn.clicked.connect(self.main_window.show_add_doctor_page)
        cta_row.addWidget(add_btn)

        all_btn = make_button("All Doctors", "outline", height=46, size=12)
        all_btn.setToolTip("View every doctor in the directory")
        all_btn.clicked.connect(lambda: self.main_window.perform_search("", ""))
        cta_row.addWidget(all_btn)

        hero_layout.addLayout(cta_row)
        layout.addWidget(self.hero_card)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)

        doc_color = "#5eead4" if CURRENT_THEME == "dark" else TEAL_DARK
        spec_color = "#93c5fd" if CURRENT_THEME == "dark" else NAVY
        hosp_color = "#f472b6" if CURRENT_THEME == "dark" else MAGENTA

        self.doctors_stat_value, self.doctors_card = self._make_stat_card("0", "Doctors in Directory", doc_color)
        self.specialties_stat_value, self.specialties_card = self._make_stat_card("0", "Specialties", spec_color)
        self.hospitals_stat_value, self.hospitals_card = self._make_stat_card("0", "Hospitals", hosp_color)

        stats_row.addWidget(self.doctors_card)
        stats_row.addWidget(self.specialties_card)
        stats_row.addWidget(self.hospitals_card)
        layout.addLayout(stats_row)

        self.shortcuts_card = QFrame()
        self.shortcuts_card.setObjectName("card")
        self.shortcuts_card.setStyleSheet(card_qss())
        apply_card_shadow(self.shortcuts_card)
        shortcuts_layout = QVBoxLayout(self.shortcuts_card)
        shortcuts_layout.setContentsMargins(24, 18, 24, 20)
        shortcuts_layout.setSpacing(8)

        self.shortcuts_title = make_label("Quick Specialty Search", 13, True, p["heading"])
        self.shortcuts_sub = make_label("Click a saved specialty below to view matching doctors immediately.", 9, False, p["muted"])
        shortcuts_layout.addWidget(self.shortcuts_title)
        shortcuts_layout.addWidget(self.shortcuts_sub)

        self.shortcuts_grid = QGridLayout()
        self.shortcuts_grid.setContentsMargins(0, 4, 0, 0)
        self.shortcuts_grid.setHorizontalSpacing(8)
        self.shortcuts_grid.setVerticalSpacing(8)
        shortcuts_layout.addLayout(self.shortcuts_grid)

        layout.addWidget(self.shortcuts_card)

        self.recent_card = QFrame()
        self.recent_card.setObjectName("card")
        self.recent_card.setStyleSheet(card_qss())
        apply_card_shadow(self.recent_card)
        recent_layout = QVBoxLayout(self.recent_card)
        recent_layout.setContentsMargins(24, 18, 24, 20)
        recent_layout.setSpacing(8)

        recent_header = QHBoxLayout()
        self.recent_title = make_label("Recently Added Doctors", 13, True, p["heading"])
        recent_header.addWidget(self.recent_title)
        recent_header.addStretch(1)
        self.view_all_link = make_link_button("View all")
        self.view_all_link.clicked.connect(lambda: self.main_window.perform_search("", ""))
        recent_header.addWidget(self.view_all_link)
        recent_layout.addLayout(recent_header)

        self.recent_container = QWidget()
        self.recent_layout = QVBoxLayout(self.recent_container)
        self.recent_layout.setContentsMargins(0, 2, 0, 0)
        self.recent_layout.setSpacing(8)
        recent_layout.addWidget(self.recent_container)

        layout.addWidget(self.recent_card)

        centered_holder = QHBoxLayout()
        centered_holder.addStretch(1)
        centered_holder.addWidget(container, 1)
        centered_holder.addStretch(1)
        outer.addLayout(centered_holder)
        outer.addStretch(1)

        scroll.setWidget(inner)
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

    @staticmethod
    def _make_stat_card(value_text, caption_text, value_color):
        p = palette()
        card = QFrame()
        card.setObjectName("statCard")
        card.setStyleSheet(stat_card_qss())
        apply_card_shadow(card, blur=14, y_offset=3, alpha=p["shadow_alpha"])
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(4)

        value_label = make_label(value_text, 22, True, value_color, center=True)
        caption_label = make_label(caption_text, 9, True, p["muted"], center=True)
        card_layout.addWidget(value_label)
        card_layout.addWidget(caption_label)
        return value_label, card

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget:
                widget.setParent(None)
                widget.deleteLater()

    def _make_recent_row(self, doctor):
        p = palette()
        row = QFrame()
        row.setObjectName("recentRow")
        row.setStyleSheet(recent_row_qss())
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(14, 10, 14, 10)
        row_layout.setSpacing(12)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        name_lbl = make_label(doctor.get("name") or "N/A", 11, True, p["heading"])
        hospital = doctor.get("hospital") or "Hospital not specified"
        specialty = doctor.get("specialty") or "General"
        sub_lbl = make_label(f"{specialty}  ·  {hospital}", 9, False, p["muted"])
        info_col.addWidget(name_lbl)
        info_col.addWidget(sub_lbl)
        row_layout.addLayout(info_col, 1)

        edit_btn = make_button("Edit", "outline", width=72, height=30, size=9)
        edit_btn.clicked.connect(lambda checked=False, d_id=doctor["id"]: self.main_window.edit_doctor(d_id))
        row_layout.addWidget(edit_btn)
        return row

    def apply_theme(self):
        p = palette()
        for c in (self.hero_card, self.shortcuts_card, self.recent_card):
            c.setStyleSheet(card_qss())
            apply_card_shadow(c)
        for c in (self.doctors_card, self.specialties_card, self.hospitals_card):
            c.setStyleSheet(stat_card_qss())
            apply_card_shadow(c, blur=14, y_offset=3, alpha=p["shadow_alpha"])

        doc_color = "#5eead4" if CURRENT_THEME == "dark" else TEAL_DARK
        spec_color = "#93c5fd" if CURRENT_THEME == "dark" else NAVY
        hosp_color = "#f472b6" if CURRENT_THEME == "dark" else MAGENTA
        self.doctors_stat_value.setStyleSheet(f"color: {doc_color}; background: transparent;")
        self.specialties_stat_value.setStyleSheet(f"color: {spec_color}; background: transparent;")
        self.hospitals_stat_value.setStyleSheet(f"color: {hosp_color}; background: transparent;")

        for lbl in (self.greeting_label, self.shortcuts_title, self.recent_title):
            lbl.setStyleSheet(f"color: {p['heading']}; background: transparent;")
        for lbl in (self.subtitle_label, self.shortcuts_sub):
            lbl.setStyleSheet(f"color: {p['muted']}; background: transparent;")

        for btn in self.findChildren(QPushButton):
            kind = btn.property("btnKind")
            if kind in button_styles():
                style_button(btn, kind)

        self.refresh()

    def set_user(self, user):
        if user and user.get("full_name", "").strip():
            first_name = user["full_name"].split()[0]
            self.greeting_label.setText(f"Hi, {first_name}!")
            self.subtitle_label.setText(f"{APP_TAGLINE} — manage doctors or jump straight into search.")
        else:
            self.greeting_label.setText(self.DEFAULT_GREETING)
            self.subtitle_label.setText(self.DEFAULT_SUBTITLE)

    def refresh(self):
        p = palette()
        db = self.main_window.db_manager
        total_doctors = db.count_doctors()
        specialties = db.get_distinct_counts("specialty")
        hospitals = db.get_distinct_counts("hospital")

        self.doctors_stat_value.setText(str(total_doctors))
        self.specialties_stat_value.setText(str(len(specialties)))
        self.hospitals_stat_value.setText(str(len(hospitals)))

        self._clear_layout(self.shortcuts_grid)
        if not specialties:
            self.shortcuts_grid.addWidget(
                make_label("No specialties saved yet. Add a doctor to create quick shortcuts.", 9, False, p["muted"]),
                0, 0
            )
        else:
            cols = 3
            for idx, (spec_name, count) in enumerate(specialties[:6]):
                btn = QPushButton(f"{spec_name} ({count})")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setFocusPolicy(Qt.TabFocus)
                btn.setFont(QFont(FONT_FAMILY, 9, QFont.Bold))
                btn.setFixedHeight(32)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {p["chip_bg"]};
                        color: {p["chip_fg"]};
                        border: 1px solid {p["border"]};
                        border-radius: 14px;
                        padding: 0 12px;
                        outline: none;
                    }}
                    QPushButton:hover {{
                        background-color: {TEAL};
                        color: #ffffff;
                    }}
                    QPushButton:focus {{
                        border: 2px solid {GOLD};
                    }}
                """)
                btn.clicked.connect(lambda checked=False, s=spec_name: self.main_window.perform_search(s, ""))
                self.shortcuts_grid.addWidget(btn, idx // cols, idx % cols)

        self._clear_layout(self.recent_layout)
        recent = db.get_recent_doctors(limit=4)
        if not recent:
            self.recent_layout.addWidget(
                make_label("No doctors added yet. Click \"Add Doctor\" above to save your first entry.", 9, False, p["muted"])
            )
        else:
            for doc in recent:
                self.recent_layout.addWidget(self._make_recent_row(doc))


# --- Landing/Search Page ---
class LandingPage(QWidget):
    DEFAULT_SUBTITLE = "Search by medical specialty, hospital, or both."

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()

    def init_ui(self):
        p = palette()
        self.card, layout = make_card(440)
        self.title_lbl = make_label("Find a Doctor", 22, True, p["heading"], center=True)
        layout.addWidget(self.title_lbl)
        self.subtitle_label = make_label(self.DEFAULT_SUBTITLE, 10, False, p["muted"], center=True)
        layout.addWidget(self.subtitle_label)
        layout.addSpacing(6)

        self.specialty_input = add_field(layout, "Specialty", "Type, or click the arrow to pick one")
        self.hospital_input = add_field(layout, "Hospital", "Type, or click the arrow to pick one")
        self.specialty_input.returnPressed.connect(self.search_doctors)
        self.hospital_input.returnPressed.connect(self.search_doctors)

        search_button = make_button("Search", "primary", height=46, size=13)
        search_button.setToolTip("Find doctors that match the boxes above")
        search_button.clicked.connect(self.search_doctors)
        layout.addWidget(search_button)

        show_all_button = make_button("Show all doctors", "outline", height=42, size=11)
        show_all_button.setToolTip("List every doctor in the directory")
        show_all_button.clicked.connect(self.show_all_doctors)
        layout.addWidget(show_all_button)

        add_doctor_button = make_button("Add doctor", "accent", height=46, size=13)
        add_doctor_button.setToolTip("Save a new doctor in the directory")
        add_doctor_button.clicked.connect(self.navigate_to_add_doctor)
        layout.addWidget(add_doctor_button)

        self.stats_label = make_label("", 9, False, p["muted"], center=True)
        layout.addWidget(self.stats_label)

        place_card(self, self.card)

    def apply_theme(self):
        p = palette()
        self.card.setStyleSheet(card_qss())
        apply_card_shadow(self.card)
        self.title_lbl.setStyleSheet(f"color: {p['heading']}; background: transparent;")
        self.subtitle_label.setStyleSheet(f"color: {p['muted']}; background: transparent;")
        self.stats_label.setStyleSheet(f"color: {p['muted']}; background: transparent;")
        for lbl in self.findChildren(QLabel):
            if lbl.property("role") == "fieldCaption":
                lbl.setStyleSheet(f"color: {p['heading']}; background: transparent;")
        for field in (self.specialty_input, self.hospital_input):
            field.setStyleSheet(input_error_qss() if field.property("invalid") else input_qss())
        for btn in self.findChildren(QPushButton):
            kind = btn.property("btnKind")
            if kind in button_styles():
                style_button(btn, kind)
        self.refresh()

    def set_user(self, user):
        if user and user.get("full_name", "").strip():
            first_name = user["full_name"].split()[0]
            self.subtitle_label.setText(f"Hi, {first_name}! Search by specialty, hospital, or both.")
        else:
            self.subtitle_label.setText(self.DEFAULT_SUBTITLE)

    def refresh(self):
        db = self.main_window.db_manager
        set_options(self.specialty_input, db.get_distinct_counts("specialty"), "specialties")
        set_options(self.hospital_input, db.get_distinct_counts("hospital"), "hospitals")
        total = db.count_doctors()
        if total == 0:
            self.stats_label.setText("No doctors saved yet. Use \"Add doctor\" to add the first one.")
        else:
            self.stats_label.setText(f"{total} doctor{'s' if total != 1 else ''} in the directory.")

    def search_doctors(self):
        specialty = self.specialty_input.text().strip()
        hospital = self.hospital_input.text().strip()
        self.main_window.perform_search(specialty, hospital)

    def show_all_doctors(self):
        self.specialty_input.clear()
        self.hospital_input.clear()
        self.main_window.perform_search("", "")

    def navigate_to_add_doctor(self):
        self.main_window.show_add_doctor_page()


# --- Search Results Page (Responsive Grid + Quick-Filter Chips + Live Filter + Details Modal) ---
class SearchResultsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self._all_doctors = []
        self._filtered_doctors = []
        self._active_chip = "ALL"
        self._keyword = ""
        self._last_cols = 0
        self.init_ui()

    def init_ui(self):
        p = palette()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 18, 28, 14)
        main_layout.setSpacing(10)

        top_row = QHBoxLayout()
        self.page_title = make_label("Search Results", 20, True, p["heading"])
        top_row.addWidget(self.page_title)
        top_row.addSpacing(12)
        self.count_label = make_label("", 10, False, p["muted"])
        top_row.addWidget(self.count_label)
        top_row.addStretch(1)

        add_btn = make_button("+ Add Doctor", "accent", width=136, height=36, size=10)
        add_btn.clicked.connect(self.main_window.show_add_doctor_page)
        top_row.addWidget(add_btn)

        back_button = make_button("Back to search", "outline", width=150, height=36, size=10)
        back_button.clicked.connect(self.main_window.show_landing_page)
        top_row.addWidget(back_button)
        main_layout.addLayout(top_row)

        # Summary + Live Keyword Filter row
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(12)
        self.summary_label = make_label("", 10, False, p["muted"])
        filter_bar.addWidget(self.summary_label, 1)

        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("Filter displayed results by doctor name or hospital...")
        self.keyword_input.setClearButtonEnabled(True)
        self.keyword_input.setFixedWidth(320)
        self.keyword_input.setFixedHeight(34)
        self.keyword_input.setFont(QFont(FONT_FAMILY, 10))
        self.keyword_input.setStyleSheet(input_qss())
        self.keyword_input.textChanged.connect(self._on_keyword_changed)
        filter_bar.addWidget(self.keyword_input)
        main_layout.addLayout(filter_bar)

        self.chips_frame = QFrame()
        self.chips_frame.setStyleSheet(
            f"QFrame {{ background-color: {p['card']}; border: 1px solid {p['border']}; border-radius: 12px; }}"
        )
        chips_outer = QHBoxLayout(self.chips_frame)
        chips_outer.setContentsMargins(12, 8, 12, 8)
        chips_outer.setSpacing(8)
        self.filter_lbl = make_label("Quick Filter:", 9, True, p["heading"])
        chips_outer.addWidget(self.filter_lbl)

        self.chips_grid = QGridLayout()
        self.chips_grid.setContentsMargins(0, 0, 0, 0)
        self.chips_grid.setHorizontalSpacing(6)
        self.chips_grid.setVerticalSpacing(6)
        chips_outer.addLayout(self.chips_grid, 1)

        self.reset_filter_btn = make_link_button("Reset")
        self.reset_filter_btn.setVisible(False)
        self.reset_filter_btn.clicked.connect(self._reset_all_filters)
        chips_outer.addWidget(self.reset_filter_btn)

        self.chips_frame.setVisible(False)
        main_layout.addWidget(self.chips_frame)

        self.status = StatusLabel()
        main_layout.addWidget(self.status)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )
        self.results_container = QWidget()
        self.results_grid = QGridLayout(self.results_container)
        self.results_grid.setContentsMargins(0, 2, 6, 8)
        self.results_grid.setHorizontalSpacing(14)
        self.results_grid.setVerticalSpacing(14)
        self.scroll_area.setWidget(self.results_container)
        main_layout.addWidget(self.scroll_area, 1)

    def apply_theme(self):
        p = palette()
        self.page_title.setStyleSheet(f"color: {p['heading']}; background: transparent;")
        self.count_label.setStyleSheet(f"color: {p['muted']}; background: transparent;")
        self.summary_label.setStyleSheet(f"color: {p['muted']}; background: transparent;")
        self.filter_lbl.setStyleSheet(f"color: {p['heading']}; background: transparent;")
        self.keyword_input.setStyleSheet(input_qss())
        self.chips_frame.setStyleSheet(
            f"QFrame {{ background-color: {p['card']}; border: 1px solid {p['border']}; border-radius: 12px; }}"
        )
        self.status.refresh_theme()
        for btn in self.findChildren(QPushButton):
            kind = btn.property("btnKind")
            if kind in button_styles():
                style_button(btn, kind)
        self._rebuild_chips()
        self._render_grid(self._filtered_doctors, self._compute_columns())

    @staticmethod
    def describe_search(specialty, hospital):
        parts = []
        if specialty:
            parts.append(f'Specialty: "{specialty}"')
        if hospital:
            parts.append(f'Hospital: "{hospital}"')
        return "  ·  ".join(parts) if parts else "Showing all doctors"

    def open_doctor_details(self, doctor):
        latest = self.main_window.db_manager.get_doctor_by_id(doctor.get("id")) or doctor
        dialog = DoctorDetailsDialog(latest, self.main_window, self)
        dialog.exec_()

    def _compute_columns(self):
        viewport_w = self.scroll_area.viewport().width() if self.scroll_area else self.width()
        if viewport_w >= 1120:
            return 3
        if viewport_w >= 720:
            return 2
        return 1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cols = self._compute_columns()
        if cols != self._last_cols and self._filtered_doctors:
            self._render_grid(self._filtered_doctors, cols)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget:
                widget.setParent(None)
                widget.deleteLater()

    def _rebuild_chips(self):
        p = palette()
        self._clear_layout(self.chips_grid)
        if len(self._all_doctors) <= 1:
            self.chips_frame.setVisible(False)
            return

        seen = {}
        for doc in self._all_doctors:
            spec = (doc.get("specialty") or "").strip()
            if spec:
                key = spec.lower()
                if key not in seen:
                    seen[key] = [spec, 0]
                seen[key][1] += 1

        if len(seen) <= 1:
            self.chips_frame.setVisible(False)
            return

        self.chips_frame.setVisible(True)
        chip_specs = [("ALL", f"All ({len(self._all_doctors)})")] + [
            (key, f"{label} ({cnt})") for key, (label, cnt) in seen.items()
        ]

        max_per_row = 5
        for idx, (chip_key, text) in enumerate(chip_specs):
            is_selected = (self._active_chip == chip_key)
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFocusPolicy(Qt.TabFocus)
            btn.setFont(QFont(FONT_FAMILY, 9, QFont.Bold))
            btn.setFixedHeight(28)
            if is_selected:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {GOLD};
                        color: {NAVY};
                        border: 1px solid {GOLD};
                        border-radius: 12px;
                        padding: 0 12px;
                        outline: none;
                    }}
                    QPushButton:focus {{ border: 2px solid {TEAL}; }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {p["chip_bg"]};
                        color: {p["chip_fg"]};
                        border: 1px solid {p["border"]};
                        border-radius: 12px;
                        padding: 0 12px;
                        outline: none;
                    }}
                    QPushButton:hover {{
                        background-color: {TEAL};
                        color: #ffffff;
                    }}
                    QPushButton:focus {{ border: 2px solid {GOLD}; }}
                """)
            btn.clicked.connect(lambda checked=False, k=chip_key: self._apply_chip_filter(k))
            self.chips_grid.addWidget(btn, idx // max_per_row, idx % max_per_row)

        has_any_subfilter = (self._active_chip != "ALL") or bool(self._keyword)
        self.reset_filter_btn.setVisible(has_any_subfilter)

    def _matches_keyword(self, doctor, kw_lower):
        if not kw_lower:
            return True
        name = (doctor.get("name") or "").lower()
        hospital = (doctor.get("hospital") or "").lower()
        return (kw_lower in name) or (kw_lower in hospital)

    def _apply_filters(self):
        kw = self._keyword.strip().lower()
        result = []
        for d in self._all_doctors:
            if self._active_chip != "ALL":
                if (d.get("specialty") or "").strip().lower() != self._active_chip:
                    continue
            if not self._matches_keyword(d, kw):
                continue
            result.append(d)
        self._filtered_doctors = result
        self._rebuild_chips()
        self._render_grid(self._filtered_doctors, self._compute_columns())

    def _apply_chip_filter(self, chip_key):
        self._active_chip = chip_key
        self._apply_filters()

    def _on_keyword_changed(self, text):
        self._keyword = text or ""
        self._apply_filters()

    def _reset_all_filters(self):
        self._active_chip = "ALL"
        self._keyword = ""
        self.keyword_input.blockSignals(True)
        self.keyword_input.clear()
        self.keyword_input.blockSignals(False)
        self._apply_filters()

    def display_results(self, doctors, specialty="", hospital=""):
        self.status.clear_status()
        self.summary_label.setText(self.describe_search(specialty, hospital))
        self._all_doctors = list(doctors)
        self._active_chip = "ALL"
        self._keyword = ""
        self.keyword_input.blockSignals(True)
        self.keyword_input.clear()
        self.keyword_input.blockSignals(False)
        self.keyword_input.setEnabled(bool(self._all_doctors))

        self._apply_filters()

    def _render_grid(self, doctors, cols):
        self._last_cols = cols
        self._clear_layout(self.results_grid)

        if not doctors:
            self.count_label.setText("No results")
            has_subfilter = (self._active_chip != "ALL") or bool(self._keyword.strip())
            has_filters = bool(self.summary_label.text() != "Showing all doctors" or has_subfilter)
            self.results_grid.addWidget(self._create_empty_state(has_filters), 0, 0)
            return

        total = len(doctors)
        has_subfilter = (self._active_chip != "ALL") or bool(self._keyword.strip())
        suffix = f" (filtered from {len(self._all_doctors)})" if has_subfilter else ""
        self.count_label.setText(f"{total} doctor{'s' if total != 1 else ''} found{suffix}")

        for c in range(3):
            self.results_grid.setColumnStretch(c, 1 if c < cols else 0)

        for idx, doctor in enumerate(doctors):
            r = idx // cols
            c = idx % cols
            self.results_grid.addWidget(self.create_doctor_card(doctor), r, c)

        last_row = (len(doctors) - 1) // cols + 1
        self.results_grid.setRowStretch(last_row, 1)

    def _create_empty_state(self, has_filters):
        p = palette()
        card, layout = make_card(480)
        layout.setContentsMargins(32, 32, 32, 32)
        if has_filters:
            title = "No doctors found"
            message = ("Nothing matches your current search or filter. Try resetting filters "
                       "or searching with a shorter keyword.")
        else:
            title = "No doctors yet"
            message = "The directory is empty. Add the first doctor to get started."
        layout.addWidget(make_label(title, 16, True, p["heading"], center=True))
        layout.addWidget(make_label(message, 10, False, p["muted"], center=True))
        layout.addSpacing(6)

        has_subfilter = (self._active_chip != "ALL") or bool(self._keyword.strip())
        if has_subfilter:
            reset_btn = make_button("Reset filters", "teal", height=40)
            reset_btn.clicked.connect(self._reset_all_filters)
            layout.addWidget(reset_btn)

        add_button = make_button("Add a doctor", "accent", height=42)
        add_button.clicked.connect(self.main_window.show_add_doctor_page)
        layout.addWidget(add_button)

        back_button = make_button("Back to search", "outline", height=42)
        back_button.clicked.connect(self.main_window.show_landing_page)
        layout.addWidget(back_button)

        holder = QWidget()
        holder_layout = QHBoxLayout(holder)
        holder_layout.setContentsMargins(0, 24, 0, 0)
        holder_layout.addStretch(1)
        holder_layout.addWidget(card)
        holder_layout.addStretch(1)
        return holder

    def _make_avatar(self, doctor, size=64):
        avatar = QLabel()
        avatar.setFixedSize(size, size)
        avatar.setAlignment(Qt.AlignCenter)

        photo = None
        image_path = doctor.get("image_path")
        if image_path and os.path.exists(image_path):
            photo = circular_pixmap(image_path, size)

        if photo is not None:
            avatar.setPixmap(photo)
        else:
            words = [w for w in (doctor.get("name") or "").replace("Dr.", "").split() if w]
            initials = "".join(w[0] for w in words[:2]).upper() or "?"
            avatar.setText(initials)
            avatar.setFont(QFont(FONT_FAMILY, 18, QFont.Bold))
            avatar.setStyleSheet(f"background-color: {TEAL}; color: #ffffff; border-radius: {size // 2}px;")
        return avatar

    def create_doctor_card(self, doctor):
        p = palette()
        card_widget = QFrame()
        card_widget.setObjectName("doctorCard")
        card_widget.setStyleSheet(doctor_card_qss())
        card_widget.setCursor(Qt.PointingHandCursor)
        card_widget.setToolTip("Click card to view full doctor details")
        apply_card_shadow(card_widget, blur=14, y_offset=3, alpha=p["shadow_alpha"])
        card_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        original_mouse_press = card_widget.mousePressEvent

        def on_card_press(event, doc=doctor, orig=original_mouse_press):
            if event.button() == Qt.LeftButton and card_widget.childAt(event.pos()) is not None:
                child = card_widget.childAt(event.pos())
                if not isinstance(child, QPushButton):
                    self.open_doctor_details(doc)
                    return
            orig(event)

        card_widget.mousePressEvent = on_card_press

        outer = QVBoxLayout(card_widget)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(10)

        top_section = QHBoxLayout()
        top_section.setSpacing(12)
        top_section.addWidget(self._make_avatar(doctor, size=64), alignment=Qt.AlignTop)

        header_col = QVBoxLayout()
        header_col.setSpacing(4)
        name_lbl = make_label(doctor.get("name") or "N/A", 13, True, p["heading"])
        name_lbl.setWordWrap(True)
        header_col.addWidget(name_lbl)

        specialty = doctor.get("specialty")
        if specialty:
            pill = QLabel(specialty)
            pill.setTextFormat(Qt.PlainText)
            pill.setFont(QFont(FONT_FAMILY, 8, QFont.Bold))
            pill.setStyleSheet(pill_qss())
            pill.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            header_col.addWidget(pill)
        header_col.addStretch(1)
        top_section.addLayout(header_col, 1)
        outer.addLayout(top_section)

        for caption, key in (("Hospital", "hospital"), ("Schedule", "schedule"), ("Contact", "contact")):
            value = doctor.get(key) or "N/A"
            line = QLabel(f"<b>{caption}:</b> {html.escape(str(value))}")
            line.setTextFormat(Qt.RichText)
            line.setFont(QFont(FONT_FAMILY, 9))
            line.setStyleSheet(f"color: {p['text']}; background: transparent;")
            line.setWordWrap(True)
            line.setTextInteractionFlags(Qt.TextSelectableByMouse)
            outer.addWidget(line)

        outer.addStretch(1)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(8)

        details_button = make_button("Details", "teal", width=76, height=32, size=9)
        details_button.setToolTip("Open full profile dialog")
        details_button.clicked.connect(lambda checked=False, d=doctor: self.open_doctor_details(d))
        actions_row.addWidget(details_button)

        actions_row.addStretch(1)

        edit_button = make_button("Edit", "outline", width=68, height=32, size=9)
        edit_button.setToolTip("Change this doctor's details")
        edit_button.clicked.connect(lambda checked=False, d=doctor["id"]: self.main_window.edit_doctor(d))
        actions_row.addWidget(edit_button)

        delete_button = make_button("Delete", "accent", width=72, height=32, size=9)
        delete_button.setToolTip("Remove this doctor from the directory")
        delete_button.clicked.connect(lambda checked=False, d=doctor["id"]: self.main_window.delete_doctor(d))
        actions_row.addWidget(delete_button)

        outer.addLayout(actions_row)
        return card_widget


# --- Add Doctor Page ---
class AddDoctorPage(QWidget):
    PREVIEW_SIZE = 56

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.image_path = ""
        self.current_doctor_id = None
        self.init_ui()

    def init_ui(self):
        p = palette()
        self.card, layout = make_card(480)
        layout.setSpacing(10)

        self.title_label = make_label("Add Doctor", 22, True, p["heading"], center=True)
        self.subtitle_label = make_label("Fill in the details below. Fields marked * are required.",
                                         10, False, p["muted"], center=True)
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addSpacing(4)

        self.name_input = add_field(layout, "Doctor's name", "e.g. Dr. Maria Santos", required=True)
        self.specialty_input = add_field(layout, "Specialty", "e.g. Cardiologist", required=True)
        self.hospital_input = add_field(layout, "Hospital", "e.g. City General Hospital", required=True)
        self.schedule_input = add_field(layout, "Schedule", "e.g. Mon - Fri, 9 AM - 3 PM")
        self.contact_input = add_field(layout, "Contact details", "Phone number or email")
        self.form_fields = (self.name_input, self.specialty_input, self.hospital_input,
                            self.schedule_input, self.contact_input)
        for current, following in zip(self.form_fields, self.form_fields[1:]):
            current.returnPressed.connect(following.setFocus)
        self.form_fields[-1].returnPressed.connect(self.handle_add_update_doctor)

        self.photo_caption = make_label("Photo (optional)", 9, True, p["heading"])
        layout.addWidget(self.photo_caption)
        image_row = QHBoxLayout()
        image_row.setSpacing(12)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(self.PREVIEW_SIZE, self.PREVIEW_SIZE)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFont(QFont(FONT_FAMILY, 8, QFont.Bold))
        image_row.addWidget(self.preview_label)

        image_info = QVBoxLayout()
        image_info.setSpacing(0)
        self.image_path_label = QLabel("No image selected.")
        self.image_path_label.setTextFormat(Qt.PlainText)
        self.image_path_label.setFont(QFont(FONT_FAMILY, 9))
        self.image_path_label.setStyleSheet(f"color: {p['muted']}; background: transparent;")
        self.remove_image_button = make_link_button("Remove photo")
        self.remove_image_button.clicked.connect(self.remove_image)
        image_info.addStretch(1)
        image_info.addWidget(self.image_path_label)
        image_info.addWidget(self.remove_image_button, 0, Qt.AlignLeft)
        image_info.addStretch(1)
        image_row.addLayout(image_info, 1)

        upload_image_button = make_button("Upload Image here", "teal", width=210, height=40, size=10)
        upload_image_button.clicked.connect(self.select_image)
        image_row.addWidget(upload_image_button)
        layout.addLayout(image_row)

        self.status = StatusLabel()
        layout.addWidget(self.status)

        self.action_button = make_button("Add doctor", "accent", height=46, size=13)
        self.action_button.clicked.connect(self.handle_add_update_doctor)
        layout.addWidget(self.action_button)

        self.cancel_button = make_button("Back to home", "outline", height=40, size=11)
        self.cancel_button.clicked.connect(self.main_window.leave_form)
        layout.addWidget(self.cancel_button)

        self._update_image_label()
        place_card(self, self.card)

    def apply_theme(self):
        p = palette()
        self.card.setStyleSheet(card_qss())
        apply_card_shadow(self.card)
        self.title_label.setStyleSheet(f"color: {p['heading']}; background: transparent;")
        self.subtitle_label.setStyleSheet(f"color: {p['muted']}; background: transparent;")
        self.photo_caption.setStyleSheet(f"color: {p['heading']}; background: transparent;")
        self.image_path_label.setStyleSheet(f"color: {p['muted']}; background: transparent;")
        for lbl in self.findChildren(QLabel):
            if lbl.property("role") == "fieldCaption":
                lbl.setStyleSheet(f"color: {p['heading']}; background: transparent;")
        for field in self.form_fields:
            field.setStyleSheet(input_error_qss() if field.property("invalid") else input_qss())
        self.status.refresh_theme()
        for btn in self.findChildren(QPushButton):
            kind = btn.property("btnKind")
            if kind in button_styles():
                style_button(btn, kind)
        self._update_image_label()
        self.refresh_suggestions()

    def refresh_suggestions(self):
        db = self.main_window.db_manager
        set_options(self.specialty_input, db.get_distinct_counts("specialty"), "specialties")
        set_options(self.hospital_input, db.get_distinct_counts("hospital"), "hospitals")

    def _update_image_label(self):
        p = palette()
        photo = None
        if self.image_path and os.path.exists(self.image_path):
            photo = circular_pixmap(self.image_path, self.PREVIEW_SIZE)

        self.preview_label.clear()
        if photo is not None:
            self.preview_label.setStyleSheet("background: transparent;")
            self.preview_label.setPixmap(photo)
        else:
            self.preview_label.setStyleSheet(
                f"background-color: {p['pill_bg']}; color: {p['pill_fg']}; border-radius: {self.PREVIEW_SIZE // 2}px;"
            )
            self.preview_label.setText("Photo")

        if self.image_path:
            name = os.path.basename(self.image_path)
            self.image_path_label.setText(name if len(name) <= 20 else name[:17] + "...")
            self.image_path_label.setToolTip(self.image_path)
        else:
            self.image_path_label.setText("No image selected.")
            self.image_path_label.setToolTip("")
        self.remove_image_button.setVisible(bool(self.image_path))

    def select_image(self):
        path, _selected_filter = QFileDialog.getOpenFileName(
            self, "Select Doctor Image", "", "Images (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if not path:
            return
        if QPixmap(path).isNull():
            self.status.show_error("That file could not be opened as a picture. Please choose a PNG, JPG or GIF image.")
            return
        self.image_path = path
        self.status.clear_status()
        self._update_image_label()

    def remove_image(self):
        self.image_path = ""
        self._update_image_label()

    def set_mode(self, mode, doctor_data=None):
        self.current_doctor_id = None
        self.clear_form()
        self.status.clear_status()
        self.refresh_suggestions()

        if mode == 'add':
            self.title_label.setText("Add Doctor")
            self.subtitle_label.setText("Fill in the details below. Fields marked * are required.")
            self.action_button.setText("Add doctor")
            self.cancel_button.setText("Back to home")
        elif mode == 'edit' and doctor_data:
            self.title_label.setText("Edit Doctor")
            self.subtitle_label.setText("Change the details below, then press Update doctor.")
            self.action_button.setText("Update doctor")
            self.cancel_button.setText("Cancel")
            self.current_doctor_id = doctor_data.get('id')
            self.load_doctor_data(doctor_data)

    def load_doctor_data(self, doctor_data):
        self.name_input.setText(doctor_data.get('name') or '')
        self.specialty_input.setText(doctor_data.get('specialty') or '')
        self.hospital_input.setText(doctor_data.get('hospital') or '')
        self.schedule_input.setText(doctor_data.get('schedule') or '')
        self.contact_input.setText(doctor_data.get('contact') or '')
        self.image_path = doctor_data.get('image_path') or ''
        self._update_image_label()

    def handle_add_update_doctor(self):
        self.status.clear_status()
        name = self.name_input.text().strip()
        specialty = self.specialty_input.text().strip()
        hospital = self.hospital_input.text().strip()
        schedule = self.schedule_input.text().strip()
        contact = self.contact_input.text().strip()

        missing = [field for field, value in ((self.name_input, name),
                                              (self.specialty_input, specialty),
                                              (self.hospital_input, hospital)) if not value]
        if missing:
            for field in reversed(missing):
                flag_invalid(field)
            self.status.show_error("Please fill in the highlighted fields.")
            return

        db = self.main_window.db_manager
        if db.doctor_exists(name, hospital, self.current_doctor_id):
            flag_invalid(self.name_input)
            self.status.show_error(f"{name} at {hospital} is already in the directory.")
            return

        stored_image = store_doctor_image(self.image_path)

        if self.current_doctor_id is None:
            success = db.add_doctor(name, specialty, hospital, schedule, contact, stored_image)
            if success:
                self.clear_form()
                self.refresh_suggestions()
                self.status.show_success(f"{name} was added. You can add another doctor, or go back.")
                self.name_input.setFocus()
        else:
            success = db.update_doctor(
                self.current_doctor_id, name, specialty, hospital, schedule, contact, stored_image
            )
            if success:
                self.main_window.after_edit_saved(name)

        if not success:
            self.status.show_error("Something went wrong and the doctor was not saved. Please try again.")

    def clear_form(self):
        for field in self.form_fields:
            field.clear()
            _reset_invalid(field)
        self.image_path = ""
        self._update_image_label()
        self.current_doctor_id = None


# --- Login Page ---
class LoginPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()

    def init_ui(self):
        p = palette()
        self.card, layout = make_card(420)
        self.title_lbl = make_label("Welcome back", 22, True, p["heading"], center=True)
        self.sub_lbl = make_label("Log in to find and manage doctors.", 10, False, p["muted"], center=True)
        layout.addWidget(self.title_lbl)
        layout.addWidget(self.sub_lbl)
        layout.addSpacing(6)

        self.email_input = add_field(layout, "Email", "you@example.com")
        self.password_input = add_field(layout, "Password", "Enter your password", password=True)
        self.show_password = make_show_password_checkbox(self.password_input)
        layout.addWidget(self.show_password)

        self.email_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.handle_login)

        self.status = StatusLabel()
        layout.addWidget(self.status)

        login_button = make_button("Log in", "primary", height=46, size=13)
        login_button.clicked.connect(self.handle_login)
        layout.addWidget(login_button)

        layout.addLayout(make_link_row("Don't have an account?", "Register", self.main_window.show_register_page))

        place_card(self, self.card)

    def apply_theme(self):
        p = palette()
        self.card.setStyleSheet(card_qss())
        apply_card_shadow(self.card)
        self.title_lbl.setStyleSheet(f"color: {p['heading']}; background: transparent;")
        self.sub_lbl.setStyleSheet(f"color: {p['muted']}; background: transparent;")
        self.show_password.setStyleSheet(f"QCheckBox {{ color: {p['muted']}; background: transparent; spacing: 6px; }}")
        for lbl in self.findChildren(QLabel):
            if lbl.property("role") in ("fieldCaption", "muted"):
                role_color = p["muted"] if lbl.property("role") == "muted" else p["heading"]
                lbl.setStyleSheet(f"color: {role_color}; background: transparent;")
        for field in (self.email_input, self.password_input):
            field.setStyleSheet(input_error_qss() if field.property("invalid") else input_qss())
        self.status.refresh_theme()
        for btn in self.findChildren(QPushButton):
            kind = btn.property("btnKind")
            if kind in button_styles():
                style_button(btn, kind)

    def clear_form(self):
        self.email_input.clear()
        self.password_input.clear()
        self.show_password.setChecked(False)
        self.status.clear_status()
        for field in (self.email_input, self.password_input):
            _reset_invalid(field)

    def prefill(self, email, message):
        self.clear_form()
        self.email_input.setText(email)
        self.status.show_success(message)

    def on_show(self):
        target = self.password_input if self.email_input.text() else self.email_input
        target.setFocus()

    def handle_login(self):
        self.status.clear_status()
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            if not password:
                flag_invalid(self.password_input)
            if not email:
                flag_invalid(self.email_input)
            self.status.show_error("Please enter your email and password.")
            return

        user = self.main_window.db_manager.verify_user(email, password)
        if user is None:
            self.status.show_error("Incorrect email or password. Please try again.")
            self.password_input.clear()
            self.password_input.setFocus()
            return

        self.clear_form()
        self.main_window.login_success(user)


# --- Register Page ---
class RegisterPage(QWidget):
    MIN_PASSWORD_LENGTH = 8
    EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()

    def init_ui(self):
        p = palette()
        self.card, layout = make_card(420)
        self.title_lbl = make_label("Create your account", 22, True, p["heading"], center=True)
        self.sub_lbl = make_label("It only takes a moment.", 10, False, p["muted"], center=True)
        layout.addWidget(self.title_lbl)
        layout.addWidget(self.sub_lbl)
        layout.addSpacing(6)

        self.name_input = add_field(layout, "Full name", "Your full name")
        self.email_input = add_field(layout, "Email", "you@example.com")
        self.password_input = add_field(
            layout, f"Password (at least {self.MIN_PASSWORD_LENGTH} characters)",
            "Choose a password", password=True)
        self.confirm_input = add_field(layout, "Confirm password", "Type the password again", password=True)
        self.show_password = make_show_password_checkbox(self.password_input, self.confirm_input)
        layout.addWidget(self.show_password)

        self.fields = (self.name_input, self.email_input, self.password_input, self.confirm_input)
        for current, following in zip(self.fields, self.fields[1:]):
            current.returnPressed.connect(following.setFocus)
        self.confirm_input.returnPressed.connect(self.handle_register)

        self.status = StatusLabel()
        layout.addWidget(self.status)

        register_button = make_button("Create account", "accent", height=46, size=13)
        register_button.clicked.connect(self.handle_register)
        layout.addWidget(register_button)

        layout.addLayout(make_link_row("Already have an account?", "Back to log in", self.main_window.show_login_page))

        place_card(self, self.card)

    def apply_theme(self):
        p = palette()
        self.card.setStyleSheet(card_qss())
        apply_card_shadow(self.card)
        self.title_lbl.setStyleSheet(f"color: {p['heading']}; background: transparent;")
        self.sub_lbl.setStyleSheet(f"color: {p['muted']}; background: transparent;")
        self.show_password.setStyleSheet(f"QCheckBox {{ color: {p['muted']}; background: transparent; spacing: 6px; }}")
        for lbl in self.findChildren(QLabel):
            if lbl.property("role") in ("fieldCaption", "muted"):
                role_color = p["muted"] if lbl.property("role") == "muted" else p["heading"]
                lbl.setStyleSheet(f"color: {role_color}; background: transparent;")
        for field in self.fields:
            field.setStyleSheet(input_error_qss() if field.property("invalid") else input_qss())
        self.status.refresh_theme()
        for btn in self.findChildren(QPushButton):
            kind = btn.property("btnKind")
            if kind in button_styles():
                style_button(btn, kind)

    def clear_form(self):
        for field in self.fields:
            field.clear()
            _reset_invalid(field)
        self.show_password.setChecked(False)
        self.status.clear_status()

    def on_show(self):
        self.name_input.setFocus()

    def handle_register(self):
        self.status.clear_status()
        full_name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        empty = [field for field, value in ((self.name_input, full_name), (self.email_input, email),
                                            (self.password_input, password), (self.confirm_input, confirm))
                 if not value]
        if empty:
            for field in reversed(empty):
                flag_invalid(field)
            self.status.show_error("Please fill in all fields.")
            return
        if not self.EMAIL_PATTERN.match(email):
            flag_invalid(self.email_input)
            self.status.show_error("Please enter a valid email address, like name@example.com.")
            return
        if len(password) < self.MIN_PASSWORD_LENGTH:
            flag_invalid(self.password_input)
            self.status.show_error(f"Your password needs at least {self.MIN_PASSWORD_LENGTH} characters.")
            return
        if password != confirm:
            flag_invalid(self.confirm_input)
            self.confirm_input.clear()
            self.status.show_error("The two passwords do not match. Please type them again.")
            return

        success, message = self.main_window.db_manager.create_user(full_name, email, password)
        if success:
            self.clear_form()
            self.main_window.registration_done(email)
        else:
            flag_invalid(self.email_input)
            self.status.show_error(message)


# =============================================================================
#  MAIN APPLICATION WINDOW
# =============================================================================
class SeekDoctorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.current_user = None
        self.last_search = None
        self.init_ui()
        self.setStyleSheet(app_stylesheet())

    def init_ui(self):
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(make_app_icon())

        width, height = 1040, 740
        screen = QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            width = min(width, available.width() - 40)
            height = min(height, available.height() - 60)
        self.resize(width, height)
        self.setMinimumSize(820, 560)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.header = HeaderBar(self)
        self.stacked_widget = QStackedWidget()
        self.footer = FooterBar()
        self.main_layout.addWidget(self.header)
        self.main_layout.addWidget(self.stacked_widget, 1)
        self.main_layout.addWidget(self.footer)

        self.landing_page = LandingPage(self)
        self.search_results_page = SearchResultsPage(self)
        self.add_doctor_page = AddDoctorPage(self)
        self.login_page = LoginPage(self)
        self.register_page = RegisterPage(self)
        self.home_page = HomePage(self)

        self.stacked_widget.addWidget(self.landing_page)        # 0
        self.stacked_widget.addWidget(self.search_results_page) # 1
        self.stacked_widget.addWidget(self.add_doctor_page)     # 2
        self.stacked_widget.addWidget(self.login_page)          # 3
        self.stacked_widget.addWidget(self.register_page)       # 4
        self.stacked_widget.addWidget(self.home_page)           # 5

        self.show_login_page()

    def toggle_theme(self):
        next_mode = "dark" if CURRENT_THEME == "light" else "light"
        set_theme_mode(next_mode)
        self.setStyleSheet(app_stylesheet())
        self.header.apply_theme()
        self.footer.apply_theme()
        for page in (
            self.home_page,
            self.landing_page,
            self.search_results_page,
            self.add_doctor_page,
            self.login_page,
            self.register_page,
        ):
            page.apply_theme()

    def _set_page(self, index, title, home_active=False):
        self.stacked_widget.setCurrentIndex(index)
        self.setWindowTitle(f"{APP_NAME} - {title}")
        self.header.set_home_active(home_active)

    def show_login_page(self):
        self._set_page(3, "Log in", home_active=False)
        self.login_page.on_show()

    def show_register_page(self):
        self.register_page.clear_form()
        self._set_page(4, "Register", home_active=False)
        self.register_page.on_show()

    def registration_done(self, email):
        self.login_page.prefill(email, "Account created! Enter your password to log in.")
        self.show_login_page()

    def login_success(self, user):
        self.current_user = user
        self.header.set_user(user)
        self.home_page.set_user(user)
        self.landing_page.set_user(user)
        self.show_home_page()

    def logout(self):
        self.current_user = None
        self.last_search = None
        self.header.set_user(None)
        self.home_page.set_user(None)
        self.landing_page.set_user(None)
        self.landing_page.specialty_input.clear()
        self.landing_page.hospital_input.clear()
        self.search_results_page.display_results([])
        self.login_page.clear_form()
        self.show_login_page()

    def show_home_page(self):
        if self.current_user is None:
            self.show_login_page()
            return
        self.home_page.refresh()
        self._set_page(5, "Home", home_active=True)

    def show_landing_page(self):
        if self.current_user is None:
            self.show_login_page()
            return
        self.landing_page.refresh()
        self._set_page(0, "Find a Doctor", home_active=False)
        self.landing_page.specialty_input.setFocus()

    def perform_search(self, specialty, hospital):
        if self.current_user is None:
            self.show_login_page()
            return
        self.last_search = (specialty, hospital)
        doctors = self.db_manager.search_doctors(specialty, hospital)
        self.search_results_page.display_results(doctors, specialty, hospital)
        self._set_page(1, "Search Results", home_active=False)

    def show_add_doctor_page(self):
        if self.current_user is None:
            self.show_login_page()
            return
        self.add_doctor_page.set_mode('add')
        self._set_page(2, "Add Doctor", home_active=False)
        self.add_doctor_page.name_input.setFocus()

    def edit_doctor(self, doctor_id):
        doctor_data = self.db_manager.get_doctor_by_id(doctor_id)
        if doctor_data:
            self.add_doctor_page.set_mode('edit', doctor_data)
            self._set_page(2, f"Edit Doctor: {doctor_data.get('name', '')}", home_active=False)
            self.add_doctor_page.name_input.setFocus()
        else:
            QMessageBox.warning(self, "Error", "Doctor not found for editing.")

    def leave_form(self):
        editing = self.add_doctor_page.current_doctor_id is not None
        if editing and self.last_search is not None:
            self.perform_search(*self.last_search)
        else:
            self.show_home_page()

    def after_edit_saved(self, doctor_name):
        if self.last_search is not None:
            self.perform_search(*self.last_search)
            self.search_results_page.status.show_success(f"{doctor_name} was updated.")
        else:
            self.show_home_page()

    def _confirm_delete(self, doctor_name):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Delete doctor")
        box.setTextFormat(Qt.PlainText)
        box.setText(f"Delete {doctor_name} from the directory?\n\nThis cannot be undone.")
        delete_button = box.addButton("Delete", QMessageBox.DestructiveRole)
        cancel_button = box.addButton("Cancel", QMessageBox.RejectRole)
        box.setDefaultButton(cancel_button)
        box.exec_()
        return box.clickedButton() is delete_button

    def delete_doctor(self, doctor_id):
        doctor = self.db_manager.get_doctor_by_id(doctor_id)
        if doctor is None:
            if self.last_search is not None:
                self.perform_search(*self.last_search)
                self.search_results_page.status.show_error("That doctor was already removed.")
            return

        name = doctor.get("name") or "this doctor"
        if not self._confirm_delete(name):
            return

        if self.db_manager.delete_doctor(doctor_id):
            if self.last_search is not None:
                self.perform_search(*self.last_search)
                self.search_results_page.status.show_success(f"{name} was deleted.")
            else:
                self.show_home_page()
        else:
            QMessageBox.critical(self, "Error", "Failed to delete the doctor. Please try again.")

    def closeEvent(self, event):
        self.db_manager.close()
        event.accept()


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("cvsu.seekdoctor.app")
        except Exception:
            pass

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setFont(QFont(FONT_FAMILY, 10))
    app.setWindowIcon(make_app_icon())
    try:
        window = SeekDoctorApp()
    except RuntimeError as error:
        QMessageBox.critical(None, APP_NAME, f"SeekDoctor could not start.\n\n{error}")
        sys.exit(1)
    window.show()
    sys.exit(app.exec_())