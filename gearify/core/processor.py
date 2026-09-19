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
        保留段落、表格、字体、排版格式与 Run 级样式
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
            if new_text == p.text:
                return

            # 合计统计
            for k in total_stats:
                total_stats[k] += s.get(k, 0)

            # 优先尝试 Run 级别的原位精准替换，保留粗体、颜色、字号等独立样式
            if len(p.runs) > 1:
                run_desensitized = []
                for r in p.runs:
                    if r.text:
                        new_r_text, _ = self.desensitizer.desensitize(r.text)
                        run_desensitized.append(new_r_text)
                    else:
                        run_desensitized.append("")

                if "".join(run_desensitized) == new_text:
                    for r, new_r in zip(p.runs, run_desensitized):
                        r.text = new_r
                    return

            # 回退策略：当敏感词跨越 Run 边界时，写回首个 Run 并清空后续 Run
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
        支持公式保护、序号/编号列保护及手机号/身份证长数值识别
        """
        wb = openpyxl.load_workbook(source_path)
        total_stats = {
            "protected_count": 0,
            "entity_count": 0,
            "number_count": 0,
            "total_count": 0,
        }

        seq_headers = {"序号", "编号", "id", "no.", "no", "序列号", "行号"}

        for sheet in wb.worksheets:
            # 扫描首行，标记序号/编号列
            seq_col_indices = set()
            first_row = list(sheet.iter_rows(min_row=1, max_row=1))
            if first_row:
                for col_idx, cell in enumerate(first_row[0]):
                    if cell.value and isinstance(cell.value, str):
                        header_clean = cell.value.strip().lower()
                        if header_clean in seq_headers or any(h in header_clean for h in ["序号", "编号"]):
                            seq_col_indices.add(col_idx)

            for row_idx, row in enumerate(sheet.iter_rows()):
                for col_idx, cell in enumerate(row):
                    val = cell.value
                    if val is None:
                        continue

                    # 1. 字符串单元格处理
                    if isinstance(val, str):
                        # 保护公式：以 '=' 开头的不破坏公式结构
                        if val.startswith("="):
                            continue
                        new_val, s = self.desensitizer.desensitize(val)
                        if new_val != val:
                            cell.value = new_val
                            for k in total_stats:
                                total_stats[k] += s.get(k, 0)

                    # 2. 纯数值单元格处理
                    elif isinstance(val, (int, float)):
                        # 首行表头或者被判定为“序号/编号”列中的整数递增序号予以保护
                        if row_idx > 0 and col_idx in seq_col_indices and isinstance(val, int) and self.desensitizer.config.protect_sequence:
                            total_stats["protected_count"] += 1
                            continue

                        val_str = str(val)
                        # 智能识别存为数值的长敏感实体
                        if isinstance(val, int) and len(val_str) == 11 and val_str.startswith("1") and self.desensitizer.config.mask_phone:
                            cell.value = self.desensitizer.mask_entity_text(val_str)
                            total_stats["entity_count"] += 1
                            total_stats["total_count"] += 1
                        elif isinstance(val, int) and len(val_str) in (15, 18) and self.desensitizer.config.mask_id_card:
                            cell.value = self.desensitizer.mask_entity_text(val_str)
                            total_stats["entity_count"] += 1
                            total_stats["total_count"] += 1
                        elif isinstance(val, int) and 16 <= len(val_str) <= 19 and self.desensitizer.config.mask_bank_card:
                            cell.value = self.desensitizer.mask_entity_text(val_str)
                            total_stats["entity_count"] += 1
                            total_stats["total_count"] += 1
                        elif self.desensitizer.config.mask_numbers:
                            masked_str = self.desensitizer.mask_number_text(val_str)
                            cell.value = masked_str
                            total_stats["number_count"] += 1
                            total_stats["total_count"] += 1

        wb.save(output_path)
        return total_stats
