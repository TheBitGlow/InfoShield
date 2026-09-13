"""现代化 Fluent / Flat 扁平卡片风格 QSS 样式表
"""

import os

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets").replace("\\", "/")
CHECK_ICON_PATH = f"{ASSETS_DIR}/check.svg"

MODERN_STYLE = f"""
/* 全局基础设置：统一字体与前景色，主背景限定在顶层容器 */
QMainWindow, QDialog, QWidget#CentralWidget {{
    background-color: #f8fafc;
    font-family: "Microsoft YaHei UI", "PingFang SC", "Segoe UI", sans-serif;
    font-size: 13px;
    color: #1e293b;
}}

/* 确保所有 QLabel 默认透明背景，杜绝白色色块残留 */
QLabel {{
    background: transparent;
    background-color: transparent;
    font-family: "Microsoft YaHei UI", "PingFang SC", "Segoe UI", sans-serif;
}}

/* 主卡片容器 */
QFrame#Card, QWidget#Card {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}}

/* 顶部标题栏背景：优雅极简的白底卡片 */
QFrame#HeaderCard {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 14px;
}}

QFrame#HeaderCard QLabel {{
    background: transparent;
    background-color: transparent;
}}

QLabel#HeaderTitle {{
    color: #0f172a;
    font-size: 18px;
    font-weight: bold;
}}

QLabel#HeaderVersion {{
    color: #64748b;
    font-size: 12px;
    font-weight: 600;
    background-color: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 2px 6px;
    margin-left: 6px;
}}

QLabel#HeaderSubtitle {{
    color: #64748b;
    font-size: 12px;
}}

/* 按钮基础样式 */
QPushButton {{
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 5px 10px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: #f1f5f9;
    border-color: #94a3b8;
    color: #0f172a;
}}

QPushButton:pressed {{
    background-color: #e2e8f0;
}}

QPushButton:disabled {{
    background-color: #f8fafc;
    border-color: #e2e8f0;
    color: #94a3b8;
}}

/* 主要操作高亮按钮 */
QPushButton#PrimaryButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2563eb, stop:1 #1d4ed8);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 14px;
    font-weight: bold;
    min-width: 120px;
}}

QPushButton#PrimaryButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3b82f6, stop:1 #2563eb);
}}

QPushButton#PrimaryButton:pressed {{
    background-color: #1e40af;
}}

QPushButton#PrimaryButton:disabled {{
    background-color: #93c5fd;
    color: #eff6ff;
}}

/* 危险/清理按钮 */
QPushButton#DangerButton {{
    background-color: #fff1f2;
    color: #e11d48;
    border: 1px solid #fecdd3;
}}

QPushButton#DangerButton:hover {{
    background-color: #ffe4e6;
    border-color: #fda4af;
}}

/* 拖拽投放区域 */
QFrame#DropArea {{
    background-color: #f8fafc;
    border: 2px dashed #94a3b8;
    border-radius: 10px;
}}

QFrame#DropArea:hover {{
    background-color: #eff6ff;
    border-color: #3b82f6;
}}

QLabel#DropTextTitle {{
    font-size: 14px;
    font-weight: bold;
    color: #334155;
    background: transparent;
}}

QLabel#DropTextDesc {{
    font-size: 12px;
    color: #64748b;
    background: transparent;
}}

/* 标签页 TabWidget */
QTabWidget::pane {{
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background-color: #ffffff;
    top: -1px;
}}

QTabBar::tab {{
    background-color: #f1f5f9;
    color: #64748b;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    margin-right: 4px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background-color: #ffffff;
    color: #2563eb;
    border-color: #e2e8f0;
    border-bottom: 2px solid #2563eb;
    font-weight: bold;
}}

QTabBar::tab:hover:!selected {{
    background-color: #e2e8f0;
    color: #1e293b;
}}

/* 表格控件 */
QTableWidget {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    gridline-color: #f1f5f9;
    selection-background-color: #eff6ff;
    selection-color: #1e293b;
}}

QHeaderView::section {{
    background-color: #f8fafc;
    color: #475569;
    font-weight: 600;
    padding: 6px 8px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
}}

/* 输入框与文本域 */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    color: #1e293b;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: #3b82f6;
    outline: none;
}}

/* 分组框 QGroupBox */
QGroupBox {{
    font-weight: bold;
    color: #334155;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
    background-color: #ffffff;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    background: transparent;
}}

/* 复选框 CheckBox */
QCheckBox {{
    spacing: 8px;
    color: #334155;
    font-weight: 500;
    background: transparent;
}}

QCheckBox::indicator {{
    width: 17px;
    height: 17px;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    background-color: #ffffff;
}}

QCheckBox::indicator:hover {{
    border-color: #3b82f6;
}}

QCheckBox::indicator:checked {{
    background-color: #2563eb;
    border-color: #2563eb;
    image: url({CHECK_ICON_PATH});
}}

/* 进度条 ProgressBar */
QProgressBar {{
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    text-align: center;
    background-color: #f1f5f9;
    color: #334155;
    font-weight: bold;
    height: 16px;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #10b981);
    border-radius: 5px;
}}

/* 滚动条 */
QScrollBar:vertical {{
    border: none;
    background: #f8fafc;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: #cbd5e1;
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: #94a3b8;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* 下拉选择框 QComboBox */
QComboBox {{
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 10px;
    color: #334155;
    font-weight: 500;
    min-height: 22px;
}}

QComboBox:hover {{
    border-color: #3b82f6;
    background-color: #f8fafc;
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border: none;
}}

QComboBox QAbstractItemView {{
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    selection-background-color: #eff6ff;
    selection-color: #1e293b;
    padding: 4px;
}}
"""
