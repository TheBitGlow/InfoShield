"""Gearify - 主窗口图形界面实现（支持中英文双语切换）
"""

import os
import sys
import json
from typing import List, Dict, Any

from PySide6.QtCore import Qt, QThread, Signal, QSize, QSettings
from PySide6.QtGui import QIcon, QFont, QColor, QDragEnterEvent, QDropEvent, QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QTextEdit, QPlainTextEdit, QLineEdit,
    QCheckBox, QProgressBar, QFileDialog, QMessageBox, QFrame,
    QSplitter, QGroupBox, QScrollArea, QComboBox, QMenu
)

from ..config import (
    APP_TITLE, DEFAULT_MASK_CHAR, MAX_ENTITY_MASK_LEN, MAX_NUMBER_MASK_LEN,
    DEFAULT_SUFFIX, SUPPORTED_EXTENSIONS
)
from ..core.desensitizer import Desensitizer, DesensitizerConfig
from ..core.processor import FileProcessor
from ..i18n import I18n, t
from .styles import MODERN_STYLE


class FileTableWidget(QTableWidget):
    """支持键盘 Delete/Backspace 删除选定行的增强表格
    """
    delete_pressed = Signal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.delete_pressed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


class BatchProcessWorker(QThread):
    """文件后台脱敏批处理线程，保证界面交互丝滑无卡顿
    """
    file_started = Signal(int, str)
    file_finished = Signal(int, str, dict)
    file_error = Signal(int, str)
    all_finished = Signal(int, int)
    progress_changed = Signal(int)

    def __init__(self, file_paths: List[str], desensitizer: Desensitizer, suffix: str):
        super().__init__()
        self.file_paths = file_paths
        self.desensitizer = desensitizer
        self.suffix = suffix
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        total = len(self.file_paths)
        if total == 0:
            self.all_finished.emit(0, 0)
            return

        processor = FileProcessor(self.desensitizer, self.suffix)
        success_count = 0
        error_count = 0

        for i, file_path in enumerate(self.file_paths):
            if self._is_cancelled:
                break

            self.file_started.emit(i, file_path)
            try:
                out_path, stats = processor.process_single_file(file_path)
                success_count += 1
                self.file_finished.emit(i, out_path, stats)
            except Exception as e:
                error_count += 1
                self.file_error.emit(i, str(e))

            percent = int(((i + 1) / total) * 100)
            self.progress_changed.emit(percent)

        self.all_finished.emit(success_count, error_count)


class DropArea(QFrame):
    """支持拖拽文件或文件夹的投放卡片
    """
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropArea")
        self.setAcceptDrops(True)
        self.setMinimumHeight(110)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.title_label = QLabel(t("drop_title"))
        self.title_label.setObjectName("DropTextTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)

        self.desc_label = QLabel(t("drop_desc"))
        self.desc_label.setObjectName("DropTextDesc")
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setWordWrap(True)

        layout.addWidget(self.title_label)
        layout.addWidget(self.desc_label)

    def retranslate(self):
        self.title_label.setText(t("drop_title"))
        self.desc_label.setText(t("drop_desc"))

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        file_paths = []
        for url in urls:
            path = url.toLocalFile()
            if os.path.isfile(path):
                file_paths.append(path)
            elif os.path.isdir(path):
                # 递归检索文件夹内支持的文件
                for root, _, files in os.walk(path):
                    for f in files:
                        ext = os.path.splitext(f)[1].lower()
                        if ext in SUPPORTED_EXTENSIONS:
                            file_paths.append(os.path.join(root, f))
        if file_paths:
            self.files_dropped.emit(file_paths)


class MainWindow(QMainWindow):
    """Gearify - 脱敏工具 主窗口
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("window_title"))
        self.resize(1240, 840)
        self.setMinimumSize(1020, 680)

        self.file_list: List[str] = []
        self.output_map: Dict[str, str] = {}
        self.last_output_dir = ""
        self.worker: BatchProcessWorker = None
        self.is_processing = False

        self._init_ui()
        self._load_zh_preview()
        self._load_user_settings()

    def _init_ui(self):
        # 整体布局
        central_widget = QWidget(self)
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. 顶部 Header 栏
        header = QFrame()
        header.setObjectName("HeaderCard")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 10, 16, 10)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        self.title_label = QLabel(t("app_title"))
        self.title_label.setObjectName("HeaderTitle")
        self.version_badge = QLabel("v1.0")
        self.version_badge.setObjectName("HeaderVersion")
        title_row.addWidget(self.title_label)
        title_row.addWidget(self.version_badge)
        title_row.addStretch()

        self.sub_title = QLabel(t("app_subtitle"))
        self.sub_title.setObjectName("HeaderSubtitle")

        title_box.addLayout(title_row)
        title_box.addWidget(self.sub_title)

        header_layout.addLayout(title_box, 1)

        # 语言切换选择器
        lang_box = QHBoxLayout()
        lang_box.setSpacing(6)
        self.lbl_lang = QLabel(t("lang_label"))
        self.lbl_lang.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 500;")
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("简体中文", I18n.ZH)
        self.combo_lang.addItem("English", I18n.EN)
        self.combo_lang.currentIndexChanged.connect(self._on_language_changed)
        lang_box.addWidget(self.lbl_lang)
        lang_box.addWidget(self.combo_lang)
        header_layout.addLayout(lang_box)

        main_layout.addWidget(header)

        # 2. 中间主要区域：水平分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 2.1 左侧：文件列表与投放区
        left_card = QFrame()
        left_card.setObjectName("Card")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        # 拖拽区
        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self.add_files)
        left_layout.addWidget(self.drop_area)

        # 按钮条（均分排布）
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(8)
        self.btn_add_files = QPushButton(t("btn_add_files"))
        self.btn_add_files.clicked.connect(self.choose_files)
        self.btn_add_folder = QPushButton(t("btn_add_folder"))
        self.btn_add_folder.clicked.connect(self.choose_folder)
        self.btn_clear_list = QPushButton(t("btn_clear_list"))
        self.btn_clear_list.setObjectName("DangerButton")
        self.btn_clear_list.clicked.connect(self.clear_files)

        btn_bar.addWidget(self.btn_add_files, 1)
        btn_bar.addWidget(self.btn_add_folder, 1)
        btn_bar.addWidget(self.btn_clear_list, 1)
        left_layout.addLayout(btn_bar)

        # 文件列表表格
        self.table = FileTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            t("col_filename"), t("col_format"), t("col_size"), t("col_status")
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.delete_pressed.connect(self.remove_selected_files)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_table_context_menu)
        self.table.cellDoubleClicked.connect(self._on_table_double_clicked)
        left_layout.addWidget(self.table)

        splitter.addWidget(left_card)

        # 2.2 右侧：配置选项与实时预览
        right_card = QFrame()
        right_card.setObjectName("Card")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        self.tab_widget = QTabWidget()

        # Tab 1: 核心规则（细分子项全面展开）
        scroll_rules = QScrollArea()
        scroll_rules.setWidgetResizable(True)
        scroll_rules.setFrameShape(QFrame.NoFrame)
        scroll_rules.setStyleSheet("background: transparent; border: none;")

        tab_rules_content = QWidget()
        tab_rules_content.setStyleSheet("background: transparent;")
        rules_layout = QVBoxLayout(tab_rules_content)
        rules_layout.setContentsMargins(6, 6, 16, 24)
        rules_layout.setSpacing(14)

        # 1. 实体类脱敏细项（最长3个×）
        self.grp_entity = QGroupBox(t("grp_entity"))
        grp_entity_layout = QVBoxLayout(self.grp_entity)
        grp_entity_layout.setSpacing(8)
        grp_entity_layout.setContentsMargins(14, 16, 14, 14)

        self.chk_mask_names = QCheckBox(t("chk_mask_names"))
        self.chk_mask_names.setChecked(True)
        self.chk_auto_names = QCheckBox(t("chk_auto_names"))
        self.chk_auto_names.setChecked(True)
        self.chk_mask_units = QCheckBox(t("chk_mask_units"))
        self.chk_mask_units.setChecked(True)
        self.chk_mask_industries = QCheckBox(t("chk_mask_industries"))
        self.chk_mask_industries.setChecked(True)
        self.chk_mask_id_card = QCheckBox(t("chk_mask_id_card"))
        self.chk_mask_id_card.setChecked(True)
        self.chk_mask_phone = QCheckBox(t("chk_mask_phone"))
        self.chk_mask_phone.setChecked(True)
        self.chk_mask_email = QCheckBox(t("chk_mask_email"))
        self.chk_mask_email.setChecked(True)
        self.chk_mask_ip = QCheckBox(t("chk_mask_ip"))
        self.chk_mask_ip.setChecked(True)
        self.chk_mask_bank_card = QCheckBox(t("chk_mask_bank_card"))
        self.chk_mask_bank_card.setChecked(True)
        self.chk_mask_license_plate = QCheckBox(t("chk_mask_license_plate"))
        self.chk_mask_license_plate.setChecked(True)
        self.chk_auto_orgs = QCheckBox(t("chk_auto_orgs"))
        self.chk_auto_orgs.setChecked(True)
        self.chk_auto_ind = QCheckBox(t("chk_auto_ind"))
        self.chk_auto_ind.setChecked(True)
        self.chk_mask_custom_words = QCheckBox(t("chk_mask_custom_words"))
        self.chk_mask_custom_words.setChecked(True)

        grp_entity_layout.addWidget(self.chk_mask_names)
        grp_entity_layout.addWidget(self.chk_auto_names)
        grp_entity_layout.addWidget(self.chk_mask_units)
        grp_entity_layout.addWidget(self.chk_mask_industries)
        grp_entity_layout.addWidget(self.chk_mask_id_card)
        grp_entity_layout.addWidget(self.chk_mask_phone)
        grp_entity_layout.addWidget(self.chk_mask_email)
        grp_entity_layout.addWidget(self.chk_mask_ip)
        grp_entity_layout.addWidget(self.chk_mask_bank_card)
        grp_entity_layout.addWidget(self.chk_mask_license_plate)
        grp_entity_layout.addWidget(self.chk_auto_orgs)
        grp_entity_layout.addWidget(self.chk_auto_ind)
        grp_entity_layout.addWidget(self.chk_mask_custom_words)
        rules_layout.addWidget(self.grp_entity)

        # 2. 数据类脱敏细项（最长2个××）
        self.grp_data = QGroupBox(t("grp_data"))
        grp_data_layout = QVBoxLayout(self.grp_data)
        grp_data_layout.setSpacing(8)
        grp_data_layout.setContentsMargins(14, 16, 14, 14)

        self.chk_mask_currency = QCheckBox(t("chk_mask_currency"))
        self.chk_mask_currency.setChecked(True)
        self.chk_mask_percentages = QCheckBox(t("chk_mask_percentages"))
        self.chk_mask_percentages.setChecked(True)
        self.chk_mask_counts = QCheckBox(t("chk_mask_counts"))
        self.chk_mask_counts.setChecked(True)
        self.chk_mask_dates = QCheckBox(t("chk_mask_dates"))
        self.chk_mask_dates.setChecked(False)
        self.chk_mask_standalone = QCheckBox(t("chk_mask_standalone"))
        self.chk_mask_standalone.setChecked(True)

        grp_data_layout.addWidget(self.chk_mask_currency)
        grp_data_layout.addWidget(self.chk_mask_percentages)
        grp_data_layout.addWidget(self.chk_mask_counts)
        grp_data_layout.addWidget(self.chk_mask_dates)
        grp_data_layout.addWidget(self.chk_mask_standalone)
        rules_layout.addWidget(self.grp_data)

        # 3. 序号与排版保护细项（结构完整无损）
        self.grp_protect = QGroupBox(t("grp_protect"))
        grp_protect_layout = QVBoxLayout(self.grp_protect)
        grp_protect_layout.setSpacing(8)
        grp_protect_layout.setContentsMargins(14, 16, 14, 14)

        self.chk_prot_chinese = QCheckBox(t("chk_prot_chinese"))
        self.chk_prot_chinese.setChecked(True)
        self.chk_prot_arabic = QCheckBox(t("chk_prot_arabic"))
        self.chk_prot_arabic.setChecked(True)
        self.chk_prot_special = QCheckBox(t("chk_prot_special"))
        self.chk_prot_special.setChecked(True)

        grp_protect_layout.addWidget(self.chk_prot_chinese)
        grp_protect_layout.addWidget(self.chk_prot_arabic)
        grp_protect_layout.addWidget(self.chk_prot_special)
        rules_layout.addWidget(self.grp_protect)

        # 4. 符号与输出设置
        self.grp_params = QGroupBox(t("grp_params"))
        grp_params_layout = QGridLayout(self.grp_params)
        grp_params_layout.setContentsMargins(14, 16, 14, 14)
        self.lbl_mask_char = QLabel(t("lbl_mask_char"))
        grp_params_layout.addWidget(self.lbl_mask_char, 0, 0)
        self.input_mask_char = QLineEdit(DEFAULT_MASK_CHAR)
        self.input_mask_char.setMaximumWidth(80)
        grp_params_layout.addWidget(self.input_mask_char, 0, 1)

        self.lbl_suffix = QLabel(t("lbl_suffix"))
        grp_params_layout.addWidget(self.lbl_suffix, 0, 2)
        self.input_suffix = QLineEdit(DEFAULT_SUFFIX)
        self.input_suffix.setMaximumWidth(120)
        grp_params_layout.addWidget(self.input_suffix, 0, 3)
        rules_layout.addWidget(self.grp_params)

        scroll_rules.setWidget(tab_rules_content)
        self.tab_widget.addTab(scroll_rules, t("tab_rules"))

        # Tab 2: 自定义实体词库
        tab_words = QWidget()
        words_layout = QVBoxLayout(tab_words)
        words_layout.setSpacing(8)

        self.desc_lbl = QLabel(t("dict_desc"))
        self.desc_lbl.setStyleSheet("color: #64748b;")
        words_layout.addWidget(self.desc_lbl)

        grid_words = QGridLayout()
        grid_words.setSpacing(8)

        self.lbl_units = QLabel(t("lbl_units"))
        grid_words.addWidget(self.lbl_units, 0, 0)
        self.txt_units = QPlainTextEdit()
        self.txt_units.setPlaceholderText(t("placeholder_units"))
        grid_words.addWidget(self.txt_units, 1, 0)

        self.lbl_names = QLabel(t("lbl_names"))
        grid_words.addWidget(self.lbl_names, 0, 1)
        self.txt_names = QPlainTextEdit()
        self.txt_names.setPlaceholderText(t("placeholder_names"))
        grid_words.addWidget(self.txt_names, 1, 1)

        self.lbl_industries = QLabel(t("lbl_industries"))
        grid_words.addWidget(self.lbl_industries, 2, 0)
        self.txt_industries = QPlainTextEdit()
        self.txt_industries.setPlaceholderText(t("placeholder_industries"))
        grid_words.addWidget(self.txt_industries, 3, 0)

        self.lbl_whitelist = QLabel(t("lbl_whitelist"))
        grid_words.addWidget(self.lbl_whitelist, 2, 1)
        self.txt_whitelist = QPlainTextEdit()
        self.txt_whitelist.setPlaceholderText(t("placeholder_whitelist"))
        grid_words.addWidget(self.txt_whitelist, 3, 1)

        words_layout.addLayout(grid_words)

        # 词库快捷操作
        dict_btn_bar = QHBoxLayout()
        self.btn_load_sample_dict = QPushButton(t("btn_load_sample_dict"))
        self.btn_load_sample_dict.clicked.connect(self._load_sample_dict)
        self.btn_import_dict = QPushButton(t("btn_import_dict"))
        self.btn_import_dict.clicked.connect(self._import_dict)
        self.btn_export_dict = QPushButton(t("btn_export_dict"))
        self.btn_export_dict.clicked.connect(self._export_dict)
        self.btn_clear_dict = QPushButton(t("btn_clear_dict"))
        self.btn_clear_dict.setObjectName("DangerButton")
        self.btn_clear_dict.clicked.connect(self._clear_dict)

        dict_btn_bar.addWidget(self.btn_load_sample_dict)
        dict_btn_bar.addWidget(self.btn_import_dict)
        dict_btn_bar.addWidget(self.btn_export_dict)
        dict_btn_bar.addStretch()
        dict_btn_bar.addWidget(self.btn_clear_dict)
        words_layout.addLayout(dict_btn_bar)

        self.tab_widget.addTab(tab_words, t("tab_words"))

        # Tab 3: 实时对照预览
        tab_preview = QWidget()
        prev_layout = QVBoxLayout(tab_preview)
        prev_layout.setSpacing(8)

        prev_bar = QHBoxLayout()
        self.btn_load_sample = QPushButton(t("btn_load_sample"))
        self.btn_load_sample.clicked.connect(self._load_current_sample)
        self.btn_refresh_preview = QPushButton(t("btn_refresh_preview"))
        self.btn_refresh_preview.clicked.connect(self._update_preview)
        prev_bar.addWidget(self.btn_load_sample)
        prev_bar.addWidget(self.btn_refresh_preview)
        prev_bar.addStretch()
        prev_layout.addLayout(prev_bar)

        # 左右对比
        box_split = QSplitter(Qt.Horizontal)
        
        left_prev_box = QVBoxLayout()
        self.lbl_src_text = QLabel(t("lbl_src_text"))
        left_prev_box.addWidget(self.lbl_src_text)
        self.txt_preview_src = QTextEdit()
        self.txt_preview_src.textChanged.connect(self._update_preview)
        left_prev_box.addWidget(self.txt_preview_src)
        left_w = QWidget()
        left_w.setLayout(left_prev_box)
        box_split.addWidget(left_w)

        right_prev_box = QVBoxLayout()
        self.lbl_dst_text = QLabel(t("lbl_dst_text"))
        right_prev_box.addWidget(self.lbl_dst_text)
        self.txt_preview_dst = QTextEdit()
        self.txt_preview_dst.setReadOnly(True)
        self.txt_preview_dst.setStyleSheet("background-color: #f8fafc;")
        right_prev_box.addWidget(self.txt_preview_dst)
        right_w = QWidget()
        right_w.setLayout(right_prev_box)
        box_split.addWidget(right_w)

        prev_layout.addWidget(box_split)

        # 预览统计徽章
        self.lbl_stats = QLabel(t("stats_template", 0, 0, 0, 0))
        self.lbl_stats.setStyleSheet("color: #0369a1; background-color: #f0f9ff; border: 1px solid #bae6fd; border-radius: 4px; padding: 6px 12px; font-weight: 500;")
        prev_layout.addWidget(self.lbl_stats)

        self.tab_widget.addTab(tab_preview, t("tab_preview"))

        right_layout.addWidget(self.tab_widget)
        splitter.addWidget(right_card)

        # 初始分割比例
        splitter.setSizes([490, 710])
        main_layout.addWidget(splitter)

        # 3. 底部操作栏
        bottom_card = QFrame()
        bottom_card.setObjectName("Card")
        bottom_layout = QVBoxLayout(bottom_card)
        bottom_layout.setContentsMargins(14, 10, 14, 10)
        bottom_layout.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        bottom_layout.addWidget(self.progress_bar)

        act_layout = QHBoxLayout()
        self.lbl_status = QLabel(t("status_ready"))
        self.lbl_status.setStyleSheet("color: #475569; font-weight: 500;")

        self.btn_open_folder = QPushButton(t("btn_open_folder"))
        self.btn_open_folder.setEnabled(False)
        self.btn_open_folder.clicked.connect(self.open_output_dir)

        self.btn_start = QPushButton(t("btn_start"))
        self.btn_start.setObjectName("PrimaryButton")
        self.btn_start.clicked.connect(self.start_batch_processing)

        act_layout.addWidget(self.lbl_status)
        act_layout.addStretch()
        act_layout.addWidget(self.btn_open_folder)
        act_layout.addWidget(self.btn_start)

        bottom_layout.addLayout(act_layout)
        main_layout.addWidget(bottom_card)

        # 事件监听（细分子项全部绑定实时预览响应）
        all_checkboxes = [
            self.chk_mask_names, self.chk_auto_names, self.chk_mask_units, self.chk_mask_industries,
            self.chk_mask_id_card, self.chk_mask_phone, self.chk_mask_email,
            self.chk_mask_ip, self.chk_mask_bank_card, self.chk_mask_license_plate,
            self.chk_auto_orgs, self.chk_auto_ind, self.chk_mask_custom_words,
            self.chk_mask_currency, self.chk_mask_percentages, self.chk_mask_counts,
            self.chk_mask_dates, self.chk_mask_standalone,
            self.chk_prot_chinese, self.chk_prot_arabic, self.chk_prot_special,
        ]
        for cb in all_checkboxes:
            cb.toggled.connect(self._update_preview)
        self.input_mask_char.textChanged.connect(self._update_preview)

    def _on_language_changed(self, index: int):
        """响应语言下拉框选择变化
        """
        lang = self.combo_lang.itemData(index)
        I18n.set_language(lang)
        self.retranslate_ui()
        if lang == I18n.EN:
            self._load_en_preview()
        else:
            self._load_zh_preview()

    def retranslate_ui(self):
        """动态刷新界面所有语言文本
        """
        self.setWindowTitle(t("window_title"))
        self.title_label.setText(t("app_title"))
        self.sub_title.setText(t("app_subtitle"))
        self.lbl_lang.setText(t("lang_label"))
        self.drop_area.retranslate()

        self.btn_add_files.setText(t("btn_add_files"))
        self.btn_add_folder.setText(t("btn_add_folder"))
        self.btn_clear_list.setText(t("btn_clear_list"))

        self.table.setHorizontalHeaderLabels([
            t("col_filename"), t("col_format"), t("col_size"), t("col_status")
        ])

        self.tab_widget.setTabText(0, t("tab_rules"))
        self.tab_widget.setTabText(1, t("tab_words"))
        self.tab_widget.setTabText(2, t("tab_preview"))

        # Rules tab
        self.grp_entity.setTitle(t("grp_entity"))
        self.chk_mask_names.setText(t("chk_mask_names"))
        self.chk_auto_names.setText(t("chk_auto_names"))
        self.chk_mask_units.setText(t("chk_mask_units"))
        self.chk_mask_industries.setText(t("chk_mask_industries"))
        self.chk_mask_id_card.setText(t("chk_mask_id_card"))
        self.chk_mask_phone.setText(t("chk_mask_phone"))
        self.chk_mask_email.setText(t("chk_mask_email"))
        self.chk_mask_ip.setText(t("chk_mask_ip"))
        self.chk_mask_bank_card.setText(t("chk_mask_bank_card"))
        self.chk_mask_license_plate.setText(t("chk_mask_license_plate"))
        self.chk_auto_orgs.setText(t("chk_auto_orgs"))
        self.chk_auto_ind.setText(t("chk_auto_ind"))
        self.chk_mask_custom_words.setText(t("chk_mask_custom_words"))

        self.grp_data.setTitle(t("grp_data"))
        self.chk_mask_currency.setText(t("chk_mask_currency"))
        self.chk_mask_percentages.setText(t("chk_mask_percentages"))
        self.chk_mask_counts.setText(t("chk_mask_counts"))
        self.chk_mask_dates.setText(t("chk_mask_dates"))
        self.chk_mask_standalone.setText(t("chk_mask_standalone"))

        self.grp_protect.setTitle(t("grp_protect"))
        self.chk_prot_chinese.setText(t("chk_prot_chinese"))
        self.chk_prot_arabic.setText(t("chk_prot_arabic"))
        self.chk_prot_special.setText(t("chk_prot_special"))

        self.grp_params.setTitle(t("grp_params"))
        self.lbl_mask_char.setText(t("lbl_mask_char"))
        self.lbl_suffix.setText(t("lbl_suffix"))

        # Custom Dict tab
        self.desc_lbl.setText(t("dict_desc"))
        self.lbl_units.setText(t("lbl_units"))
        self.txt_units.setPlaceholderText(t("placeholder_units"))
        self.lbl_names.setText(t("lbl_names"))
        self.txt_names.setPlaceholderText(t("placeholder_names"))
        self.lbl_industries.setText(t("lbl_industries"))
        self.txt_industries.setPlaceholderText(t("placeholder_industries"))
        self.lbl_whitelist.setText(t("lbl_whitelist"))
        self.txt_whitelist.setPlaceholderText(t("placeholder_whitelist"))
        self.btn_load_sample_dict.setText(t("btn_load_sample_dict"))
        self.btn_import_dict.setText(t("btn_import_dict"))
        self.btn_export_dict.setText(t("btn_export_dict"))
        self.btn_clear_dict.setText(t("btn_clear_dict"))

        # Live Preview tab
        self.btn_load_sample.setText(t("btn_load_sample"))
        self.btn_refresh_preview.setText(t("btn_refresh_preview"))
        self.lbl_src_text.setText(t("lbl_src_text"))
        self.lbl_dst_text.setText(t("lbl_dst_text"))

        # Bottom Bar
        self.btn_open_folder.setText(t("btn_open_folder"))
        self.btn_start.setText(t("btn_stop") if self.is_processing else t("btn_start"))

        if not self.file_list:
            self.lbl_status.setText(t("status_ready"))
        else:
            self.lbl_status.setText(t("status_loaded", len(self.file_list)))

        self._update_preview()

    def _parse_list(self, text: str) -> List[str]:
        """将文本框输入按逗号、换行或顿号解析为列表
        """
        if not text:
            return []
        tokens = text.replace("\n", ",").replace("、", ",").replace("，", ",").split(",")
        return [t.strip() for t in tokens if t.strip()]

    def get_desensitizer_config(self) -> DesensitizerConfig:
        """从界面控件读取当前细分配置
        """
        mask_char = self.input_mask_char.text().strip() or DEFAULT_MASK_CHAR
        return DesensitizerConfig(
            mask_char=mask_char,
            # 保护项
            protect_chinese_seq=self.chk_prot_chinese.isChecked(),
            protect_arabic_seq=self.chk_prot_arabic.isChecked(),
            protect_special_seq=self.chk_prot_special.isChecked(),
            # 实体类
            mask_names=self.chk_mask_names.isChecked(),
            auto_detect_names=self.chk_auto_names.isChecked(),
            mask_units=self.chk_mask_units.isChecked(),
            mask_industries=self.chk_mask_industries.isChecked(),
            mask_id_card=self.chk_mask_id_card.isChecked(),
            mask_phone=self.chk_mask_phone.isChecked(),
            mask_email=self.chk_mask_email.isChecked(),
            mask_ip=self.chk_mask_ip.isChecked(),
            mask_bank_card=self.chk_mask_bank_card.isChecked(),
            mask_license_plate=self.chk_mask_license_plate.isChecked(),
            mask_custom_keywords=self.chk_mask_custom_words.isChecked(),
            auto_detect_orgs=self.chk_auto_orgs.isChecked(),
            auto_detect_industries=self.chk_auto_ind.isChecked(),
            # 数据类
            mask_currency=self.chk_mask_currency.isChecked(),
            mask_percentages=self.chk_mask_percentages.isChecked(),
            mask_counts=self.chk_mask_counts.isChecked(),
            mask_dates=self.chk_mask_dates.isChecked(),
            mask_standalone_numbers=self.chk_mask_standalone.isChecked(),
            # 词库
            custom_units=self._parse_list(self.txt_units.toPlainText()),
            custom_names=self._parse_list(self.txt_names.toPlainText()),
            custom_industries=self._parse_list(self.txt_industries.toPlainText()),
            whitelist=self._parse_list(self.txt_whitelist.toPlainText()),
        )

    def _update_preview(self):
        """刷新右侧实时预览
        """
        raw_text = self.txt_preview_src.toPlainText()
        if not raw_text:
            self.txt_preview_dst.setPlainText("")
            self.lbl_stats.setText(t("stats_template", 0, 0, 0, 0))
            return

        cfg = self.get_desensitizer_config()
        des = Desensitizer(cfg)
        masked, stats = des.desensitize(raw_text)

        self.txt_preview_dst.setPlainText(masked)
        self.lbl_stats.setText(
            t("stats_template",
              stats['protected_count'],
              stats['entity_count'],
              stats['number_count'],
              stats['total_count'])
        )

    def _load_current_sample(self):
        if I18n.get_language() == I18n.EN:
            self._load_en_preview()
        else:
            self._load_zh_preview()

    def _load_zh_preview(self):
        sample = (
            "一、项目执行概况\n"
            "（一）基本信息\n"
            "1. 负责人为张三，身份证号为420102199001011234，联系电话13812345678。\n"
            "2. 项目由腾讯科技有限责任公司牵头，属于人工智能与互联网金融行业。\n"
            "3. 组建了5人攻坚团队，聘请专家李小明为技术指导顾问。\n"
            "\n"
            "二、经营成果与指标\n"
            "1.1 财务收益\n"
            "① 累计实现营业收入1500万元，净利润达320.50万元。\n"
            "② 销售额同比增长35.8%，覆盖签约客户120户。\n"
            "1.2 考评准则\n"
            "(1) 单笔交易金额达 ¥128,000.00 元以上者记优秀。\n"
            "第一章 第3条 本方案遵循 Gearify安全规范 执行。"
        )
        self.txt_preview_src.setPlainText(sample)
        self.txt_names.setPlainText("张三, 李小明")
        self.txt_units.setPlainText("腾讯科技有限责任公司, 研发中心一部")
        self.txt_industries.setPlainText("人工智能, 互联网金融")
        self.txt_whitelist.setPlainText("Gearify安全规范")
        self._update_preview()

    def _load_en_preview(self):
        sample = (
            "I. Project Executive Summary\n"
            "1. General Information\n"
            "1.1 Contact person: John Smith (ID: 420102199001011234, Tel: 13812345678, Email: john.smith@company.com).\n"
            "1.2 Lead Organization: Google Inc., operating in Artificial Intelligence and FinTech sectors.\n"
            "1.3 Assembled a team of 5 members, advised by Alice Johnson.\n"
            "\n"
            "2. Performance & Financial Metrics\n"
            "2.1 Financial Growth\n"
            "① Total annual revenue reached $15,000,000 with net margin of $3,200,500.\n"
            "② Sales grew by 35.8% year-over-year, acquiring 120 enterprise clients.\n"
            "2.2 Assessment Guidelines\n"
            "(1) Contract values exceeding $128,000.00 qualify for honors.\n"
            "Chapter 1 Section 3 This program complies with Gearify Security Standards."
        )
        self.txt_preview_src.setPlainText(sample)
        self.txt_names.setPlainText("John Smith, Alice Johnson")
        self.txt_units.setPlainText("Google Inc., Microsoft Corporation")
        self.txt_industries.setPlainText("Artificial Intelligence, FinTech")
        self.txt_whitelist.setPlainText("Gearify Security Standards")
        self._update_preview()

    def _load_sample_dict(self):
        if I18n.get_language() == I18n.EN:
            self.txt_units.setPlainText("Google Inc., Apple Corp., Amazon LLC, Research Dept")
            self.txt_names.setPlainText("John Smith, Alice Smith, Bob Johnson, Emily Davis")
            self.txt_industries.setPlainText("Artificial Intelligence, FinTech, E-commerce, Gaming")
            self.txt_whitelist.setPlainText("Gearify Security Standards, ISO9001")
        else:
            self.txt_units.setPlainText("腾讯科技有限责任公司, 百度网络科技, 阿里巴巴集团, 研发中心一部")
            self.txt_names.setPlainText("张三, 李四海, 诸葛孔明, 欧阳雪")
            self.txt_industries.setPlainText("人工智能, 互联网金融, 智能制造, 电子竞技")
            self.txt_whitelist.setPlainText("Gearify安全规范, ISO9001认证")
        self._update_preview()
        QMessageBox.information(self, t("dlg_tip"), t("dlg_load_dict_success"))

    def _clear_dict(self):
        self.txt_units.clear()
        self.txt_names.clear()
        self.txt_industries.clear()
        self.txt_whitelist.clear()
        self._update_preview()

    def _export_dict(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, t("dlg_export_dict_title"), "gearify_dict.json", "JSON (*.json)"
        )
        if not file_path:
            return
        data = {
            "units": self._parse_list(self.txt_units.toPlainText()),
            "names": self._parse_list(self.txt_names.toPlainText()),
            "industries": self._parse_list(self.txt_industries.toPlainText()),
            "whitelist": self._parse_list(self.txt_whitelist.toPlainText()),
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, t("dlg_tip"), t("dlg_export_dict_success"))

    def _import_dict(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, t("dlg_import_dict_title"), "", "JSON (*.json)"
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.txt_units.setPlainText(", ".join(data.get("units", [])))
            self.txt_names.setPlainText(", ".join(data.get("names", [])))
            self.txt_industries.setPlainText(", ".join(data.get("industries", [])))
            self.txt_whitelist.setPlainText(", ".join(data.get("whitelist", [])))
            self._update_preview()
            QMessageBox.information(self, t("dlg_tip"), t("dlg_import_dict_success"))
        except Exception as e:
            QMessageBox.critical(self, t("dlg_error"), t("dlg_import_dict_error", str(e)))

    def choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, t("dlg_select_files"), "", t("file_type_filter")
        )
        if files:
            self.add_files(files)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, t("dlg_select_folder"))
        if folder:
            file_paths = []
            for root, _, files in os.walk(folder):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        file_paths.append(os.path.join(root, f))
            self.add_files(file_paths)

    def add_files(self, paths: List[str]):
        added_count = 0
        for p in paths:
            if p not in self.file_list and os.path.isfile(p):
                self.file_list.append(p)
                row = self.table.rowCount()
                self.table.insertRow(row)

                file_name = os.path.basename(p)
                ext = os.path.splitext(p)[1].upper()
                size_kb = f"{os.path.getsize(p) / 1024:.1f} KB"

                self.table.setItem(row, 0, QTableWidgetItem(file_name))
                self.table.setItem(row, 1, QTableWidgetItem(ext))
                self.table.setItem(row, 2, QTableWidgetItem(size_kb))
                
                status_item = QTableWidgetItem(t("status_waiting"))
                status_item.setForeground(QColor("#0369a1"))
                self.table.setItem(row, 3, status_item)

                added_count += 1

        self.lbl_status.setText(t("status_loaded", len(self.file_list)))

    def clear_files(self):
        self.file_list.clear()
        self.output_map.clear()
        self.table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.lbl_status.setText(t("status_cleared"))

    def remove_selected_files(self):
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        if not selected_rows:
            return
        for r in selected_rows:
            if 0 <= r < len(self.file_list):
                file_path = self.file_list[r]
                self.output_map.pop(file_path, None)
                del self.file_list[r]
            self.table.removeRow(r)
        self.lbl_status.setText(t("status_deleted_items", len(selected_rows)))

    def _show_table_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return
        row = item.row()
        if row < 0 or row >= len(self.file_list):
            return

        file_path = self.file_list[row]
        menu = QMenu(self)

        act_preview = menu.addAction(t("menu_preview"))
        act_open_file = menu.addAction(t("menu_open_file"))
        act_open_dir = menu.addAction(t("menu_open_dir"))
        menu.addSeparator()
        act_remove = menu.addAction(t("menu_remove"))

        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == act_remove:
            self.remove_selected_files()
        elif action == act_open_dir:
            folder = os.path.dirname(file_path)
            if os.path.isdir(folder):
                if sys.platform == "win32":
                    os.startfile(folder)
                else:
                    import subprocess
                    subprocess.Popen(["xdg-open", folder])
        elif action == act_open_file:
            target = self.output_map.get(file_path, file_path)
            if os.path.exists(target):
                if sys.platform == "win32":
                    os.startfile(target)
                else:
                    import subprocess
                    subprocess.Popen(["xdg-open", target])
        elif action == act_preview:
            self._preview_file_content(file_path)

    def _preview_file_content(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        if ext in (".txt", ".md", ".csv", ".json", ".xml"):
            try:
                for enc in ("utf-8-sig", "utf-8", "gbk", "gb18030", "cp936"):
                    try:
                        with open(file_path, "r", encoding=enc) as f:
                            content = f.read(5000)
                        break
                    except (UnicodeDecodeError, LookupError):
                        continue
                else:
                    content = ""
                if content:
                    self.txt_preview_src.setPlainText(content)
                    self.tab_widget.setCurrentIndex(2)
                    self._update_preview()
            except Exception as e:
                QMessageBox.warning(self, t("dlg_error"), str(e))

    def _on_table_double_clicked(self, row: int, col: int):
        if 0 <= row < len(self.file_list):
            file_path = self.file_list[row]
            target = self.output_map.get(file_path, file_path)
            if os.path.exists(target):
                if sys.platform == "win32":
                    os.startfile(target)
                else:
                    import subprocess
                    subprocess.Popen(["xdg-open", target])

    def start_batch_processing(self):
        if self.is_processing:
            # 用户点击停止处理
            self.lbl_status.setText(t("status_cancelling"))
            self.btn_start.setEnabled(False)
            if self.worker:
                self.worker.cancel()
            return

        if not self.file_list:
            QMessageBox.warning(self, t("dlg_tip"), t("dlg_no_files"))
            return

        cfg = self.get_desensitizer_config()
        des = Desensitizer(cfg)
        suffix = self.input_suffix.text().strip() or DEFAULT_SUFFIX

        self.is_processing = True
        self.btn_start.setText(t("btn_stop"))
        self.btn_start.setObjectName("DangerButton")
        self.btn_start.setStyle(self.btn_start.style())
        self.btn_add_files.setEnabled(False)
        self.btn_add_folder.setEnabled(False)
        self.btn_clear_list.setEnabled(False)
        self.progress_bar.setValue(0)
        self.lbl_status.setText(t("status_processing_batch"))

        # 启动工作线程
        self.worker = BatchProcessWorker(self.file_list, des, suffix)
        self.worker.file_started.connect(self._on_file_started)
        self.worker.file_finished.connect(self._on_file_finished)
        self.worker.file_error.connect(self._on_file_error)
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        self.worker.all_finished.connect(self._on_all_finished)
        self.worker.start()

    def _on_file_started(self, index: int, file_path: str):
        item = self.table.item(index, 3)
        if item:
            item.setText(t("status_processing"))
            item.setForeground(QColor("#d97706"))

    def _on_file_finished(self, index: int, output_path: str, stats: dict):
        self.last_output_dir = os.path.dirname(output_path)
        if 0 <= index < len(self.file_list):
            src_file = self.file_list[index]
            self.output_map[src_file] = output_path
        item = self.table.item(index, 3)
        if item:
            item.setText(t("status_completed", stats.get('total_count', 0)))
            item.setForeground(QColor("#15803d"))

    def _on_file_error(self, index: int, err_msg: str):
        item = self.table.item(index, 3)
        if item:
            item.setText(t("status_failed"))
            item.setForeground(QColor("#b91c1c"))

    def _on_all_finished(self, success: int, error: int):
        was_cancelled = self.worker and getattr(self.worker, "_is_cancelled", False)
        self.is_processing = False
        self.btn_start.setText(t("btn_start"))
        self.btn_start.setObjectName("PrimaryButton")
        self.btn_start.setStyle(self.btn_start.style())
        self.btn_start.setEnabled(True)
        self.btn_add_files.setEnabled(True)
        self.btn_add_folder.setEnabled(True)
        self.btn_clear_list.setEnabled(True)
        self.btn_open_folder.setEnabled(bool(self.last_output_dir))

        if was_cancelled:
            self.lbl_status.setText(t("status_cancelled", success, error))
        else:
            self.lbl_status.setText(t("status_finished", success, error))
            QMessageBox.information(
                self,
                t("dlg_batch_complete_title"),
                t("dlg_batch_complete_msg", success, error)
            )

    def open_output_dir(self):
        if self.last_output_dir and os.path.isdir(self.last_output_dir):
            if sys.platform == "win32":
                os.startfile(self.last_output_dir)
            else:
                import subprocess
                subprocess.Popen(["xdg-open", self.last_output_dir])

    def _save_user_settings(self):
        """将用户设置与词库自动持久化到本地系统注册表或配置文件
        """
        settings = QSettings("TheBitGlow", "InfoShield")
        settings.setValue("app/lang", I18n.get_language())
        settings.setValue("window/geometry", self.saveGeometry())

        # Checkboxes
        settings.setValue("rules/mask_names", self.chk_mask_names.isChecked())
        settings.setValue("rules/auto_names", self.chk_auto_names.isChecked())
        settings.setValue("rules/mask_units", self.chk_mask_units.isChecked())
        settings.setValue("rules/mask_industries", self.chk_mask_industries.isChecked())
        settings.setValue("rules/mask_id_card", self.chk_mask_id_card.isChecked())
        settings.setValue("rules/mask_phone", self.chk_mask_phone.isChecked())
        settings.setValue("rules/mask_email", self.chk_mask_email.isChecked())
        settings.setValue("rules/mask_ip", self.chk_mask_ip.isChecked())
        settings.setValue("rules/mask_bank_card", self.chk_mask_bank_card.isChecked())
        settings.setValue("rules/mask_license_plate", self.chk_mask_license_plate.isChecked())
        settings.setValue("rules/auto_orgs", self.chk_auto_orgs.isChecked())
        settings.setValue("rules/auto_ind", self.chk_auto_ind.isChecked())
        settings.setValue("rules/custom_words", self.chk_mask_custom_words.isChecked())

        settings.setValue("rules/currency", self.chk_mask_currency.isChecked())
        settings.setValue("rules/percentages", self.chk_mask_percentages.isChecked())
        settings.setValue("rules/counts", self.chk_mask_counts.isChecked())
        settings.setValue("rules/dates", self.chk_mask_dates.isChecked())
        settings.setValue("rules/standalone", self.chk_mask_standalone.isChecked())

        settings.setValue("rules/prot_chinese", self.chk_prot_chinese.isChecked())
        settings.setValue("rules/prot_arabic", self.chk_prot_arabic.isChecked())
        settings.setValue("rules/prot_special", self.chk_prot_special.isChecked())

        # Parameters
        settings.setValue("params/mask_char", self.input_mask_char.text())
        settings.setValue("params/suffix", self.input_suffix.text())

        # Dictionaries
        settings.setValue("dict/units", self.txt_units.toPlainText())
        settings.setValue("dict/names", self.txt_names.toPlainText())
        settings.setValue("dict/industries", self.txt_industries.toPlainText())
        settings.setValue("dict/whitelist", self.txt_whitelist.toPlainText())

    def _load_user_settings(self):
        """从本地恢复用户上次保存的设置与词库
        """
        settings = QSettings("TheBitGlow", "InfoShield")

        geom = settings.value("window/geometry")
        if geom:
            self.restoreGeometry(geom)

        saved_lang = settings.value("app/lang")
        if saved_lang in (I18n.ZH, I18n.EN):
            idx = 0 if saved_lang == I18n.ZH else 1
            self.combo_lang.setCurrentIndex(idx)

        def _get_bool(key, default):
            v = settings.value(key, default)
            if isinstance(v, str):
                return v.lower() == "true"
            return bool(v)

        self.chk_mask_names.setChecked(_get_bool("rules/mask_names", True))
        self.chk_auto_names.setChecked(_get_bool("rules/auto_names", True))
        self.chk_mask_units.setChecked(_get_bool("rules/mask_units", True))
        self.chk_mask_industries.setChecked(_get_bool("rules/mask_industries", True))
        self.chk_mask_id_card.setChecked(_get_bool("rules/mask_id_card", True))
        self.chk_mask_phone.setChecked(_get_bool("rules/mask_phone", True))
        self.chk_mask_email.setChecked(_get_bool("rules/mask_email", True))
        self.chk_mask_ip.setChecked(_get_bool("rules/mask_ip", True))
        self.chk_mask_bank_card.setChecked(_get_bool("rules/mask_bank_card", True))
        self.chk_mask_license_plate.setChecked(_get_bool("rules/mask_license_plate", True))
        self.chk_auto_orgs.setChecked(_get_bool("rules/auto_orgs", True))
        self.chk_auto_ind.setChecked(_get_bool("rules/auto_ind", True))
        self.chk_mask_custom_words.setChecked(_get_bool("rules/custom_words", True))

        self.chk_mask_currency.setChecked(_get_bool("rules/currency", True))
        self.chk_mask_percentages.setChecked(_get_bool("rules/percentages", True))
        self.chk_mask_counts.setChecked(_get_bool("rules/counts", True))
        self.chk_mask_dates.setChecked(_get_bool("rules/dates", False))
        self.chk_mask_standalone.setChecked(_get_bool("rules/standalone", True))

        self.chk_prot_chinese.setChecked(_get_bool("rules/prot_chinese", True))
        self.chk_prot_arabic.setChecked(_get_bool("rules/prot_arabic", True))
        self.chk_prot_special.setChecked(_get_bool("rules/prot_special", True))

        mask_char = settings.value("params/mask_char")
        if mask_char:
            self.input_mask_char.setText(str(mask_char))

        suffix = settings.value("params/suffix")
        if suffix:
            self.input_suffix.setText(str(suffix))

        units = settings.value("dict/units")
        if units is not None and str(units).strip():
            self.txt_units.setPlainText(str(units))
        names = settings.value("dict/names")
        if names is not None and str(names).strip():
            self.txt_names.setPlainText(str(names))
        industries = settings.value("dict/industries")
        if industries is not None and str(industries).strip():
            self.txt_industries.setPlainText(str(industries))
        whitelist = settings.value("dict/whitelist")
        if whitelist is not None and str(whitelist).strip():
            self.txt_whitelist.setPlainText(str(whitelist))

    def closeEvent(self, event):
        self._save_user_settings()
        event.accept()


def run_app():
    app = QApplication(sys.argv)
    app.setStyleSheet(MODERN_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
