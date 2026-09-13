"""文件批处理器
支持对 TXT、DOCX、XLSX、CSV、MD、JSON 等多格式文档进行脱敏，
替换后新文件自动存放在源文件的同级目录，并增加脱敏标记（如 _脱敏.docx）。
"""

import os
from typing import Dict, Any, Tuple, Callable, Optional
from .desensitizer import Desensitizer
from ..config import DEFAULT_SUFFIX, SUPPORTED_EXTENSIONS

try:
    import docx
except ImportError:
    docx = None

try:
    import openpyxl
except ImportError:
    openpyxl = None


def get_output_path(source_path: str, suffix: str = DEFAULT_SUFFIX) -> str:
    """在源文件同级目录下生成带有脱敏标记的新文件路径
    例如：C:/docs/report.docx -> C:/docs/report_脱敏.docx
    若存在同名文件，自动追加序号避免覆盖：C:/docs/report_脱敏(1).docx
    """
    dir_name, base_name = os.path.split(source_path)
    name, ext = os.path.splitext(base_name)
    
    target_name = f"{name}{suffix}{ext}"
    target_path = os.path.join(dir_name, target_name)
    
    # 避免冲突检测
    counter = 1
    while os.path.exists(target_path):
        target_name = f"{name}{suffix}({counter}){ext}"
        target_path = os.path.join(dir_name, target_name)
        counter += 1

    return target_path


class FileProcessor:
    """文档脱敏执行器
    """

    def __init__(self, desensitizer: Desensitizer, suffix: str = DEFAULT_SUFFIX):
        self.desensitizer = desensitizer
        self.suffix = suffix or DEFAULT_SUFFIX

    def process_single_file(
        self,
        source_path: str,
        progress_cb: Optional[Callable[[int, str], None]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """处理单个文件
        """
        if not os.path.isfile(source_path):
            raise FileNotFoundError(f"文件不存在: {source_path}")

        ext = os.path.splitext(source_path)[1].lower()
        output_path = get_output_path(source_path, self.suffix)

        if ext in (".txt", ".md", ".csv", ".json", ".xml"):
            stats = self._process_text_file(source_path, output_path)
        elif ext == ".docx":
            if docx is None:
                raise RuntimeError("未检测到 python-docx 模块，无法处理 Word 文档")
            stats = self._process_docx(source_path, output_path)
        elif ext == ".xlsx":
            if openpyxl is None:
                raise RuntimeError("未检测到 openpyxl 模块，无法处理 Excel 文档")
            stats = self._process_xlsx(source_path, output_path)
        else:
            # 默认作为纯文本尝试处理
            stats = self._process_text_file(source_path, output_path)

        return output_path, stats

    def _process_text_file(self, source_path: str, output_path: str) -> Dict[str, Any]:
        """处理纯文本文档（TXT / MD / CSV / JSON / XML）
        """
        encodings = ["utf-8-sig", "utf-8", "gb18030", "gbk", "cp936", "latin-1"]
        content = ""
        used_enc = "utf-8"

        # 尝试不同编码读取
        with open(source_path, "rb") as f:
            raw_bytes = f.read()

        for enc in encodings:
            try:
                content = raw_bytes.decode(enc)
                used_enc = enc
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            content = raw_bytes.decode("utf-8", errors="ignore")

        # 执行脱敏
        masked_content, stats = self.desensitizer.desensitize(content)

        # 写入新文件（统一以带 BOM 的 UTF-8 保存，确保 Windows 记事本和 Excel 打开中文不乱码）
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            f.write(masked_content)

        return stats

    def _process_docx(self, source_path: str, output_path: str) -> Dict[str, Any]:
        """处理 Word 文档 (.docx)
        保留段落、表格、字体、排版格式
        """
        doc = docx.Document(source_path)
        total_stats = {
            "protected_count": 0,
            "entity_count": 0,
            "number_count": 0,
            "total_count": 0,
        }

        def desensitize_paragraph(p):
            if not p.text:
                return
            new_text, s = self.desensitizer.desensitize(p.text)
            if new_text != p.text:
                # 合计统计
                for k in total_stats:
                    total_stats[k] += s.get(k, 0)
                # 保持样式写回
                if p.runs:
                    p.runs[0].text = new_text
                    for r in p.runs[1:]:
                        r.text = ""
                else:
                    p.text = new_text

        # 1. 主体段落
        for p in doc.paragraphs:
            desensitize_paragraph(p)

        # 2. 表格
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        desensitize_paragraph(p)

        # 3. 页眉和页脚
        for section in doc.sections:
            for p in section.header.paragraphs:
                desensitize_paragraph(p)
            for p in section.footer.paragraphs:
                desensitize_paragraph(p)

        doc.save(output_path)
        return total_stats

    def _process_xlsx(self, source_path: str, output_path: str) -> Dict[str, Any]:
        """处理 Excel 工作簿 (.xlsx)
        """
        wb = openpyxl.load_workbook(source_path)
        total_stats = {
            "protected_count": 0,
            "entity_count": 0,
            "number_count": 0,
            "total_count": 0,
        }

        for sheet in wb.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    val = cell.value
                    if val is None:
                        continue
                    if isinstance(val, str):
                        new_val, s = self.desensitizer.desensitize(val)
                        if new_val != val:
                            cell.value = new_val
                            for k in total_stats:
                                total_stats[k] += s.get(k, 0)
                    elif isinstance(val, (int, float)) and self.desensitizer.config.mask_numbers:
                        # 单元格为纯数字
                        val_str = str(val)
                        masked_str = self.desensitizer.mask_number_text(val_str)
                        cell.value = masked_str
                        total_stats["number_count"] += 1
                        total_stats["total_count"] += 1

        wb.save(output_path)
        return total_stats
