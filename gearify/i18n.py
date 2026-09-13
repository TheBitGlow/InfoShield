"""多语言国际化 (i18n) 模块
支持中英文双语无缝动态切换
"""

from typing import Dict, Any


class I18n:
    """语言文本管理中心
    """

    ZH = "zh_CN"
    EN = "en_US"

    _current_lang = ZH

    TRANSLATIONS: Dict[str, Dict[str, str]] = {
        ZH: {
            "app_title": "InfoShield",
            "window_title": "InfoShield",
            "app_subtitle": "轻量化离线敏感信息脱敏系统 | 纯本地运行 · 精准遮蔽 · 结构无损",
            "lang_label": "语言 / Language:",
            # 投放区
            "drop_title": "📂 拖拽文件或文件夹到此处",
            "drop_desc": "支持 DOCX、XLSX、TXT、MD、CSV、JSON 等主流文档格式",
            # 文件操作
            "btn_add_files": "＋ 添加文件",
            "btn_add_folder": "📁 添加文件夹",
            "btn_clear_list": "清空列表",
            "col_filename": "文件名",
            "col_format": "格式",
            "col_size": "大小",
            "col_status": "状态",
            "status_waiting": "等待脱敏",
            "status_processing": "处理中...",
            "status_completed": "已完成 (遮蔽{0}处)",
            "status_failed": "失败",
            # 标签页
            "tab_rules": "⚙️ 核心规则",
            "tab_words": "📝 自定义词库",
            "tab_preview": "🔍 实时对照预览",
            # 规则 Group 1: 实体
            "grp_entity": "1. 实体类脱敏细项（按字长替换，最长不超过 3 个 ×）",
            "chk_mask_names": "人员姓名（如：张三 ➔ ××，李小明 ➔ ×××）",
            "chk_mask_units": "单位/机构/企业（如：腾讯 ➔ ××，研发中心 ➔ ×××）",
            "chk_mask_industries": "行业分类（如：金融 ➔ ××，智能制造 ➔ ×××）",
            "chk_mask_id_card": "身份证号（18位/15位二代居民身份证 ➔ ×××）",
            "chk_mask_phone": "手机与电话（11位手机号、固定座机 ➔ ×××）",
            "chk_mask_email": "电子邮箱（如：user@email.com ➔ ×××）",
            "chk_auto_orgs": "智能感知单位机构后缀（有限公司、研究院、局等）",
            "chk_auto_ind": "智能感知预设行业领域（互联网、新能源、医药等预设词库）",
            "chk_mask_custom_words": "启用自定义实体词库（在“自定义词库”页录入的特定对象）",
            # 规则 Group 2: 数据
            "grp_data": "2. 数据类脱敏细项（按数值替换，最长不超过 2 个 ××）",
            "chk_mask_currency": "金额与财务数据（如：¥128,000 ➔ ¥××，1500万元 ➔ ××万元，500元 ➔ ××元）",
            "chk_mask_percentages": "占比与百分比（如：35.8% ➔ ××%，5% ➔ ×%）",
            "chk_mask_counts": "人数与统计量词（如：120人 ➔ ××人，5人 ➔ ×人，80户 ➔ ××户，3项 ➔ ××项）",
            "chk_mask_dates": "日期与年份数字（如：2024年 ➔ ××年，3月 ➔ ×月，默认关闭按需开启）",
            "chk_mask_standalone": "其余独立纯数字与小数（1位 ➔ ×，2位及以上 ➔ ××）",
            # 规则 Group 3: 序号保护
            "grp_protect": "3. 序号与大纲保护细项（严密保护排版结构，绝不误伤）",
            "chk_prot_chinese": "保护中文章节与大纲序号（如：第一章、第1条、一、 、（一）、【一】）",
            "chk_prot_arabic": "保护多级与单级阿拉伯标号（如：1. 、1、 、1.1 、1.1.2 、(1) 、（1））",
            "chk_prot_special": "保护特殊带圈序号与西文字母（如：①、②、A. 、(a) 、I.）",
            # 规则 Group 4: 设置
            "grp_params": "4. 符号与输出设置",
            "lbl_mask_char": "遮蔽符号:",
            "lbl_suffix": "文件名后缀标记:",
            # 词库页
            "dict_desc": "可在此录入需要脱敏的专有对象，支持使用逗号、顿号或换行分隔：",
            "lbl_units": "自定义单位 / 机构 / 企业名:",
            "placeholder_units": "例如：百度科技, 字节跳动, 研发中心, 采购部",
            "lbl_names": "自定义人员姓名:",
            "placeholder_names": "例如：张三, 李四海, 诸葛孔明",
            "lbl_industries": "自定义行业 / 业务词:",
            "placeholder_industries": "例如：智能制造, 跨境电商, 游戏电竞",
            "lbl_whitelist": "白名单豁免词（严禁脱敏）:",
            "placeholder_whitelist": "例如：Gearify标准, 中华人民共和国, ISO9001",
            "btn_load_sample_dict": "载入示例词库",
            "btn_import_dict": "导入词库 (JSON)",
            "btn_export_dict": "导出词库 (JSON)",
            "btn_clear_dict": "清空词库",
            # 预览页
            "btn_load_sample": "载入样例文本",
            "btn_refresh_preview": "刷新脱敏效果",
            "lbl_src_text": "原文输入:",
            "lbl_dst_text": "脱敏效果 (即时呈现):",
            "stats_template": "已保护序号: {0} 处  |  实体脱敏: {1} 处  |  数据脱敏: {2} 处  |  累计遮蔽: {3} 处",
            # 底部栏
            "status_ready": "状态：就绪，请添加需要脱敏的文件",
            "status_loaded": "状态：已载入 {0} 个文件",
            "status_cleared": "状态：列表已清空",
            "status_processing_batch": "正在执行脱敏批处理...",
            "status_finished": "脱敏任务完成！成功: {0} 个，失败: {1} 个",
            "btn_open_folder": "📂 打开所在文件夹",
            "btn_start": "🚀 开始批量脱敏",
            # 对话框
            "dlg_tip": "提示",
            "dlg_error": "错误",
            "dlg_load_dict_success": "已载入示例词库！",
            "dlg_export_dict_title": "导出词库",
            "dlg_export_dict_success": "词库导出成功！",
            "dlg_import_dict_title": "导入词库",
            "dlg_import_dict_success": "词库导入成功！",
            "dlg_import_dict_error": "词库导入失败: {0}",
            "dlg_no_files": "请先添加待脱敏的文件！",
            "dlg_batch_complete_title": "批处理完成",
            "dlg_batch_complete_msg": "所有任务处理完毕！\n成功生成：{0} 个脱敏文档\n失败：{1} 个\n新文档均已保存在源文件同级目录下。",
            "dlg_select_files": "选择待脱敏文件",
            "dlg_select_folder": "选择包含文档的文件夹",
            "file_type_filter": "支持的文档 (*.txt *.docx *.xlsx *.csv *.md *.json *.xml);;所有文件 (*.*)",
        },
        EN: {
            "app_title": "InfoShield",
            "window_title": "InfoShield",
            "app_subtitle": "Lightweight Offline Data Masking Tool | 100% Local · Precise · Layout Preserved",
            "lang_label": "Language:",
            # Drop Area
            "drop_title": "📂 Drag and Drop Files or Folders Here",
            "drop_desc": "Supports DOCX, XLSX, TXT, MD, CSV, JSON and more formats",
            # File Actions
            "btn_add_files": "＋ Add Files",
            "btn_add_folder": "📁 Add Folder",
            "btn_clear_list": "Clear List",
            "col_filename": "File Name",
            "col_format": "Format",
            "col_size": "Size",
            "col_status": "Status",
            "status_waiting": "Pending",
            "status_processing": "Processing...",
            "status_completed": "Completed ({0} masked)",
            "status_failed": "Failed",
            # Tabs
            "tab_rules": "⚙️ Core Rules",
            "tab_words": "📝 Custom Dict",
            "tab_preview": "🔍 Live Preview",
            # Group 1: Entities
            "grp_entity": "1. Entity Masking Sub-rules (Length-based, Max 3 ×)",
            "chk_mask_names": "Personal Names (e.g. John ➔ ×××, Smith ➔ ×××)",
            "chk_mask_units": "Organizations and Companies (e.g. Google ➔ ×××, Dept ➔ ×××)",
            "chk_mask_industries": "Industry Sectors (e.g. Finance ➔ ×××, AI ➔ ××)",
            "chk_mask_id_card": "ID Card Numbers (18-digit IDs ➔ ×××)",
            "chk_mask_phone": "Phone Numbers (Mobile and Landline ➔ ×××)",
            "chk_mask_email": "Email Addresses (e.g. user@email.com ➔ ×××)",
            "chk_auto_orgs": "Auto-detect Company Suffixes (Inc., Ltd., LLC, Dept, etc.)",
            "chk_auto_ind": "Auto-detect Common Industries (Tech, Energy, Healthcare, etc.)",
            "chk_mask_custom_words": "Enable Custom Dictionary (Items configured in Custom Dict tab)",
            # Group 2: Data
            "grp_data": "2. Numerical Data Masking Sub-rules (Max 2 ××)",
            "chk_mask_currency": "Currency and Financial Amounts (e.g. $128,000 ➔ $××, ¥1500 ➔ ¥××)",
            "chk_mask_percentages": "Percentages and Proportions (e.g. 35.8% ➔ ××%, 5% ➔ ×%)",
            "chk_mask_counts": "Headcounts and Quantities (e.g. 120 people ➔ ×× people, 5 items ➔ × items)",
            "chk_mask_dates": "Dates and Years (e.g. 2024 ➔ ××, March ➔ ×, disabled by default)",
            "chk_mask_standalone": "Standalone Numbers and Decimals (1 digit ➔ ×, 2+ digits ➔ ××)",
            # Group 3: Protection
            "grp_protect": "3. Sequence and Outline Protection (Preserve layout structure)",
            "chk_prot_chinese": "Protect Chinese Chapter and Outline Numbers (第一章, 第1条, 一、, (一), etc.)",
            "chk_prot_arabic": "Protect Multi-level Arabic Outlines (1., 1.1, 1.1.2, (1), etc.)",
            "chk_prot_special": "Protect Circled Numbers and Letter Sequences (①, ②, A., (a), I., etc.)",
            # Group 4: Settings
            "grp_params": "4. Symbol and Output Settings",
            "lbl_mask_char": "Mask Symbol:",
            "lbl_suffix": "Filename Suffix:",
            # Custom Dict
            "dict_desc": "Enter custom entities to mask, separated by commas or newlines:",
            "lbl_units": "Custom Organizations / Companies:",
            "placeholder_units": "e.g. Google, Apple, Microsoft, Research Dept",
            "lbl_names": "Custom Personal Names:",
            "placeholder_names": "e.g. John Doe, Alice Smith, Bob Johnson",
            "lbl_industries": "Custom Industries / Keywords:",
            "placeholder_industries": "e.g. Artificial Intelligence, FinTech, E-commerce",
            "lbl_whitelist": "Whitelist Exclusions (Do Not Mask):",
            "placeholder_whitelist": "e.g. Gearify Standard, United Nations, ISO9001",
            "btn_load_sample_dict": "Load Sample Dict",
            "btn_import_dict": "Import (JSON)",
            "btn_export_dict": "Export (JSON)",
            "btn_clear_dict": "Clear Dict",
            # Preview
            "btn_load_sample": "Load Sample Text",
            "btn_refresh_preview": "Refresh Preview",
            "lbl_src_text": "Original Text:",
            "lbl_dst_text": "Masked Output (Live):",
            "stats_template": "Protected Sequences: {0}  |  Entities Masked: {1}  |  Numbers Masked: {2}  |  Total Masked: {3}",
            # Bottom Bar
            "status_ready": "Status: Ready, please add files to mask",
            "status_loaded": "Status: Loaded {0} file(s)",
            "status_cleared": "Status: List cleared",
            "status_processing_batch": "Processing batch masking...",
            "status_finished": "Batch complete! Succeeded: {0}, Failed: {1}",
            "btn_open_folder": "📂 Open Folder",
            "btn_start": "🚀 Start Masking",
            # Dialogs
            "dlg_tip": "Notice",
            "dlg_error": "Error",
            "dlg_load_dict_success": "Sample dictionary loaded successfully!",
            "dlg_export_dict_title": "Export Dictionary",
            "dlg_export_dict_success": "Dictionary exported successfully!",
            "dlg_import_dict_title": "Import Dictionary",
            "dlg_import_dict_success": "Dictionary imported successfully!",
            "dlg_import_dict_error": "Failed to import dictionary: {0}",
            "dlg_no_files": "Please add files to mask first!",
            "dlg_batch_complete_title": "Batch Completed",
            "dlg_batch_complete_msg": "All tasks finished!\nSuccessfully generated: {0} masked file(s)\nFailed: {1}\nNew files saved in the same directory as source files.",
            "dlg_select_files": "Select Files to Mask",
            "dlg_select_folder": "Select Folder Containing Documents",
            "file_type_filter": "Supported Documents (*.txt *.docx *.xlsx *.csv *.md *.json *.xml);;All Files (*.*)",
        }
    }

    @classmethod
    def set_language(cls, lang: str):
        if lang in cls.TRANSLATIONS:
            cls._current_lang = lang

    @classmethod
    def get_language(cls) -> str:
        return cls._current_lang

    @classmethod
    def t(cls, key: str, *args) -> str:
        text = cls.TRANSLATIONS.get(cls._current_lang, {}).get(key, key)
        if args:
            try:
                return text.format(*args)
            except Exception:
                return text
        return text


t = I18n.t
