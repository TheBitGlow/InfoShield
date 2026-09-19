"""序号与大纲保护器
在脱敏开始前识别出中英文各级标题、段落序号、大纲标号及白名单内容，
将其临时替换为独立控制占位符，脱敏完成后精准还原，
确保序号结构完整、排版整齐，不发生误伤。
"""

import re
from typing import Dict, List, Tuple


class SequenceProtector:
    """序号与白名单保护器，支持细粒度分类保护控制
    """

    def __init__(
        self,
        whitelist: List[str] = None,
        protect_chinese_seq: bool = True,
        protect_arabic_seq: bool = True,
        protect_special_seq: bool = True,
    ):
        self.whitelist = [w.strip() for w in (whitelist or []) if w.strip()]
        self.protect_chinese_seq = protect_chinese_seq
        self.protect_arabic_seq = protect_arabic_seq
        self.protect_special_seq = protect_special_seq

        self.patterns = []

        # 1. 中文大纲与章节条款
        if self.protect_chinese_seq:
            self.patterns.extend([
                # 章节条款：第一章、第1章、第二节、第3节、第1条、第三款等
                re.compile(r"第[0-9一二三四五六七八九十百千]+[章节部分款项篇回条步阶段页]"),
                # 中文序号带括号： （一）、(一)、【一】、[一]
                re.compile(r"(?:^|(?<=[\r\n\s；。，]))[（(【\[][一二三四五六七八九十]+[）)】\]]"),
                # 中文序号顿号或点号：一、 二、 三、 或 一. 二.
                re.compile(r"(?:^|(?<=[\r\n\s；。，]))[一二三四五六七八九十]+[、.．:：](?=\s|\S)"),
            ])

        # 2. 阿拉伯多级及单级序号
        if self.protect_arabic_seq:
            self.patterns.extend([
                # 阿拉伯多级序号：1.1 业务、1.1.2 技术规范 (排除 IPv4 地址格式，后接空格或标点，不匹配普通小数如 15.5%)
                re.compile(r"(?:^|(?<=[\r\n\s；。，]))(?!(?:\d{1,3}\.){3}\d{1,3}(?![0-9a-zA-Z]))\d+(?:\.\d+)+(?:[、.．\)]|\s+)(?=\S|$)"),
                # 单级数字序号：1. 、1、 、1) （要求点号后不得为数字，杜绝误伤小数）
                re.compile(r"(?:^|(?<=[\r\n\s；。，]))\d+[、．\)](?=\s|\S|$)"),
                re.compile(r"(?:^|(?<=[\r\n\s；。，]))\d+\.(?!\d)(?=\s|\S|$)"),
                # 阿拉伯数字带括号序号：(1)、（1）、【1】、[1]
                re.compile(r"(?:^|(?<=[\r\n\s；。，]))[（(【\[]\d+[）)】\]]"),
            ])

        # 3. 特殊带圈序号、英文字母及罗马数字
        if self.protect_special_seq:
            self.patterns.extend([
                # 特殊带圈数字序号：① ② ③ ④ ⑤ ⑥ ⑦ ⑧ ⑨ ⑩ 等
                re.compile(r"[①-⑳⑴-⒇⒈-⒛]"),
                # 英文序号：A. B. C. 或 a) b) (A)
                re.compile(r"(?:^|(?<=[\r\n\s；。，]))[A-Za-z][、.．\)](?=\s|$)"),
                re.compile(r"(?:^|(?<=[\r\n\s；。，]))[（(][A-Za-z][）)]"),
                # 罗马数字序号：I. II. III. iv. 
                re.compile(r"(?:^|(?<=[\r\n\s；。，]))(?:[IVXLCDM]+|[ivxlcdm]+)[、.．\)](?=\s|$)"),
            ])

    def protect(self, text: str) -> Tuple[str, Dict[str, str], int]:
        """识别并替换受保护的序号和白名单，返回 (受保护文本, 占位符映射字典, 保护次数)
        """
        if not text:
            return text, {}, 0

        token_map: Dict[str, str] = {}
        counter = 0

        # 先处理白名单（最长优先匹配）
        if self.whitelist:
            sorted_whitelist = sorted(self.whitelist, key=lambda x: len(x), reverse=True)
            for item in sorted_whitelist:
                if not item:
                    continue
                escaped = re.escape(item)
                matches = list(re.finditer(escaped, text))
                for m in reversed(matches):
                    counter += 1
                    token = f"\x02__GEARIFY_WL_{counter}__\x03"
                    original = m.group(0)
                    token_map[token] = original
                    text = text[:m.start()] + token + text[m.end():]

        # 保护各类选中的序号
        for pattern in self.patterns:
            matches = list(pattern.finditer(text))
            # 从后向前替换，保持位置索引正确
            for m in reversed(matches):
                counter += 1
                token = f"\x02__GEARIFY_SEQ_{counter}__\x03"
                original = m.group(0)
                token_map[token] = original
                text = text[:m.start()] + token + text[m.end():]

        return text, token_map, counter

    def restore(self, text: str, token_map: Dict[str, str]) -> str:
        """根据占位符字典精准还原受保护内容
        """
        if not text or not token_map:
            return text

        for token, original in token_map.items():
            text = text.replace(token, original)

        return text
