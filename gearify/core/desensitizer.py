"""核心脱敏引擎
严格执行脱敏规格：
1. 实体（单位、行业、姓名、身份证等）：字符数映射为 ×，最长不超过 3 个 ×
2. 数据（金额、人数、占比等数字、百分比）：映射为 ×，最长不超过 2 个 ××
3. 序号与编号保护：联动 SequenceProtector，绝不误伤任何层级序号
提供高度细粒度的多选项控制。
"""

import re
from typing import Dict, List, Set, Tuple, Any
from .protector import SequenceProtector
from ..config import (
    DEFAULT_MASK_CHAR,
    MAX_ENTITY_MASK_LEN,
    MAX_NUMBER_MASK_LEN,
    DEFAULT_INDUSTRIES,
    ORG_SUFFIXES,
)


class DesensitizerConfig:
    """脱敏配置参数（细粒度全拆分）
    """
    def __init__(
        self,
        mask_char: str = DEFAULT_MASK_CHAR,
        # 序号保护细项
        protect_chinese_seq: bool = True,
        protect_arabic_seq: bool = True,
        protect_special_seq: bool = True,
        # 实体脱敏细项（最长3个×）
        mask_names: bool = True,
        mask_units: bool = True,
        mask_industries: bool = True,
        mask_id_card: bool = True,
        mask_phone: bool = True,
        mask_email: bool = True,
        mask_custom_keywords: bool = True,
        auto_detect_orgs: bool = True,
        auto_detect_industries: bool = True,
        # 数据脱敏细项（最长2个××）
        mask_currency: bool = True,
        mask_percentages: bool = True,
        mask_counts: bool = True,
        mask_dates: bool = False,
        mask_standalone_numbers: bool = True,
        # 词库
        custom_units: List[str] = None,
        custom_names: List[str] = None,
        custom_industries: List[str] = None,
        custom_keywords: List[str] = None,
        whitelist: List[str] = None,
    ):
        self.mask_char = mask_char or DEFAULT_MASK_CHAR

        # 序号保护细项
        self.protect_chinese_seq = protect_chinese_seq
        self.protect_arabic_seq = protect_arabic_seq
        self.protect_special_seq = protect_special_seq

        # 实体类细项
        self.mask_names = mask_names
        self.mask_units = mask_units
        self.mask_industries = mask_industries
        self.mask_id_card = mask_id_card
        self.mask_phone = mask_phone
        self.mask_email = mask_email
        self.mask_custom_keywords = mask_custom_keywords
        self.auto_detect_orgs = auto_detect_orgs
        self.auto_detect_industries = auto_detect_industries

        # 数据类细项
        self.mask_currency = mask_currency
        self.mask_percentages = mask_percentages
        self.mask_counts = mask_counts
        self.mask_dates = mask_dates
        self.mask_standalone_numbers = mask_standalone_numbers

        # 词库
        self.custom_units = [u.strip() for u in (custom_units or []) if u.strip()]
        self.custom_names = [n.strip() for n in (custom_names or []) if n.strip()]
        self.custom_industries = [i.strip() for i in (custom_industries or []) if i.strip()]
        self.custom_keywords = [k.strip() for k in (custom_keywords or []) if k.strip()]
        self.whitelist = [w.strip() for w in (whitelist or []) if w.strip()]

    @property
    def mask_numbers(self) -> bool:
        return (
            self.mask_currency or
            self.mask_percentages or
            self.mask_counts or
            self.mask_standalone_numbers or
            self.mask_dates
        )

    @property
    def mask_entities(self) -> bool:
        return (
            self.mask_names or
            self.mask_units or
            self.mask_industries or
            self.mask_id_card or
            self.mask_phone or
            self.mask_email or
            self.mask_custom_keywords
        )

    @property
    def protect_sequence(self) -> bool:
        return self.protect_chinese_seq or self.protect_arabic_seq or self.protect_special_seq

    @property
    def has_any_protection(self) -> bool:
        return self.protect_sequence or bool(self.whitelist)


class Desensitizer:
    """脱敏核心处理器
    """

    def __init__(self, config: DesensitizerConfig = None):
        self.config = config or DesensitizerConfig()
        self._init_regexes()

    def _init_regexes(self):
        """预编译细分规则正则表达式
        """
        # 1. 身份证号（18位带校验码，或15位）
        self.re_id_card = re.compile(
            r"\b[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b|"
            r"\b[1-9]\d{7}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}\b"
        )

        # 2. 手机号与固定电话
        self.re_mobile = re.compile(r"(?<![0-9a-zA-Z])(?:(?:\+?86[- ]?)?1[3-9]\d{9})(?![0-9a-zA-Z])")
        self.re_landline = re.compile(r"(?<![0-9a-zA-Z])(?:0\d{2,3}-?\d{7,8})(?![0-9a-zA-Z])")

        # 3. 电子邮箱
        self.re_email = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

        # 4. 单位机构后缀识别（2到25字中文接机构后缀）
        suffix_group = "|".join(re.escape(s) for s in ORG_SUFFIXES)
        self.re_org = re.compile(rf"[\u4e00-\u9fa5A-Za-z0-9]{{2,25}}(?:{suffix_group})")

        # 5.1 金额与货币数据：带货币符号或带中文货币单位
        # 符号金额：¥1,500.00, $500
        self.re_currency_sym = re.compile(
            rf"(?:[¥$€￥]|RMB|USD|HKD)\s*(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?"
        )
        # 中文货币金额：1500万元、500元、30.5万元
        self.re_currency_cn = re.compile(
            r"(?<![0-9a-zA-Z_\x02\x03])(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(?:万|亿|千|百|元|角|分|美金|美元|港币|欧)"
        )

        # 5.2 占比与百分比：35.8%、100%、15.6个百分点、5‰
        self.re_percentages = re.compile(
            r"(?<![0-9a-zA-Z_\x02\x03])(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(?:%|‰|个百分点)"
        )

        # 5.3 人数与统计数量量词：150人、5名、80户、3项、5个、10套、20台、30辆、50家、2.5倍等
        count_units = r"(?:人|名|次|户|条|项|个|套|台|辆|家|宗|件|批|吨|千克|kg|m|km|㎡|m³|岁|点|倍)"
        self.re_counts = re.compile(
            rf"(?<![0-9a-zA-Z_\x02\x03])(?:\d{{1,3}}(?:,\d{{3}})+|\d+(?:\.\d+)?)\s*{count_units}"
        )

        # 5.4 日期与年份：2024年、12月、15日
        self.re_dates = re.compile(
            r"(?<![0-9a-zA-Z_\x02\x03])(?:\d{2,4}\s*年|\d{1,2}\s*月|\d{1,2}\s*[日号])"
        )

        # 5.5 独立纯数字或小数（如 100, 3.1415, 12, 5）
        self.re_standalone_number = re.compile(
            r"(?<![0-9a-zA-Z_\x02\x03])\d+(?:,\d{3})*(?:\.\d+)?(?![0-9a-zA-Z_\x02\x03])"
        )

    def mask_entity_text(self, text: str) -> str:
        """实体字符数映射：1字='×', 2字='××', 3字及以上='×××' (最多不超过3个×)
        """
        if not text:
            return ""
        length = len(text)
        count = max(1, min(length, MAX_ENTITY_MASK_LEN))
        return self.config.mask_char * count

    def mask_number_text(self, number_str: str) -> str:
        """数据数值映射：1位数字='×', 2位及以上='××' (最多不超过2个××)
        """
        digits_count = sum(1 for c in number_str if c.isdigit())
        if digits_count <= 1:
            return self.config.mask_char
        return self.config.mask_char * MAX_NUMBER_MASK_LEN

    def desensitize(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """执行完整脱敏流程，返回 (脱敏后文本, 统计数据)
        """
        if not text:
            return text, {
                "protected_count": 0,
                "entity_count": 0,
                "number_count": 0,
                "total_count": 0,
            }

        stats = {
            "protected_count": 0,
            "entity_count": 0,
            "number_count": 0,
            "total_count": 0,
        }

        # 第 1 步：序号与白名单保护
        token_map = {}
        if self.config.has_any_protection:
            protector = SequenceProtector(
                whitelist=self.config.whitelist,
                protect_chinese_seq=self.config.protect_chinese_seq,
                protect_arabic_seq=self.config.protect_arabic_seq,
                protect_special_seq=self.config.protect_special_seq,
            )
            text, token_map, prot_count = protector.protect(text)
            stats["protected_count"] = prot_count

        # 第 2 步：实体类脱敏（最长不超过 3 个 ×）
        # 收集用户激活的各类实体词汇
        active_entities: Set[str] = set()

        if self.config.mask_names and self.config.custom_names:
            active_entities.update(self.config.custom_names)

        if self.config.mask_units and self.config.custom_units:
            active_entities.update(self.config.custom_units)

        if self.config.mask_industries:
            if self.config.custom_industries:
                active_entities.update(self.config.custom_industries)
            if self.config.auto_detect_industries:
                active_entities.update(DEFAULT_INDUSTRIES)

        if self.config.mask_custom_keywords and self.config.custom_keywords:
            active_entities.update(self.config.custom_keywords)

        if active_entities:
            sorted_entities = sorted(active_entities, key=lambda x: len(x), reverse=True)
            for word in sorted_entities:
                if not word:
                    continue
                pattern = re.compile(re.escape(word))
                matches = list(pattern.finditer(text))
                if matches:
                    stats["entity_count"] += len(matches)
                    masked_val = self.mask_entity_text(word)
                    for m in reversed(matches):
                        text = text[:m.start()] + masked_val + text[m.end():]

        # 2.2 身份证号脱敏
        if self.config.mask_id_card:
            matches = list(self.re_id_card.finditer(text))
            if matches:
                stats["entity_count"] += len(matches)
                for m in reversed(matches):
                    masked_val = self.mask_entity_text(m.group(0))
                    text = text[:m.start()] + masked_val + text[m.end():]

        # 2.3 手机号与固定电话
        if self.config.mask_phone:
            for reg in (self.re_mobile, self.re_landline):
                matches = list(reg.finditer(text))
                if matches:
                    stats["entity_count"] += len(matches)
                    for m in reversed(matches):
                        masked_val = self.mask_entity_text(m.group(0))
                        text = text[:m.start()] + masked_val + text[m.end():]

        # 2.4 邮箱
        if self.config.mask_email:
            matches = list(self.re_email.finditer(text))
            if matches:
                stats["entity_count"] += len(matches)
                for m in reversed(matches):
                    masked_val = self.mask_entity_text(m.group(0))
                    text = text[:m.start()] + masked_val + text[m.end():]

        # 2.5 自动机构/单位识别
        if self.config.mask_units and self.config.auto_detect_orgs:
            matches = list(self.re_org.finditer(text))
            if matches:
                for m in reversed(matches):
                    org_str = m.group(0)
                    if "\x02" in org_str or "\x03" in org_str:
                        continue
                    stats["entity_count"] += 1
                    masked_val = self.mask_entity_text(org_str)
                    text = text[:m.start()] + masked_val + text[m.end():]

        # 第 3 步：数据类脱敏（细分项，最长不超过 2 个 ××）
        # 3.1 金额与货币数据
        if self.config.mask_currency:
            # 货币符号类：¥1,500.00
            for m in reversed(list(self.re_currency_sym.finditer(text))):
                val = m.group(0)
                if "\x02" in val or "\x03" in val:
                    continue
                sym_match = re.match(r"^([¥$€￥]|RMB|USD|HKD)\s*", val)
                prefix = sym_match.group(0) if sym_match else ""
                num_part = val[len(prefix):]
                masked_num = self.mask_number_text(num_part)
                text = text[:m.start()] + f"{prefix}{masked_num}" + text[m.end():]
                stats["number_count"] += 1

            # 中文货币单位类：1500万元、500元
            for m in reversed(list(self.re_currency_cn.finditer(text))):
                val = m.group(0)
                if "\x02" in val or "\x03" in val:
                    continue
                num_match = re.match(r"^(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*", val)
                if num_match:
                    num_str = num_match.group(1)
                    unit_str = val[len(num_match.group(0)):]
                    masked_num = self.mask_number_text(num_str)
                    text = text[:m.start()] + f"{masked_num}{unit_str}" + text[m.end():]
                    stats["number_count"] += 1

        # 3.2 占比与百分比数据
        if self.config.mask_percentages:
            for m in reversed(list(self.re_percentages.finditer(text))):
                val = m.group(0)
                if "\x02" in val or "\x03" in val:
                    continue
                num_match = re.match(r"^(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*", val)
                if num_match:
                    num_str = num_match.group(1)
                    unit_str = val[len(num_match.group(0)):]
                    masked_num = self.mask_number_text(num_str)
                    text = text[:m.start()] + f"{masked_num}{unit_str}" + text[m.end():]
                    stats["number_count"] += 1

        # 3.3 人数与统计量词数据
        if self.config.mask_counts:
            for m in reversed(list(self.re_counts.finditer(text))):
                val = m.group(0)
                if "\x02" in val or "\x03" in val:
                    continue
                num_match = re.match(r"^(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*", val)
                if num_match:
                    num_str = num_match.group(1)
                    unit_str = val[len(num_match.group(0)):]
                    masked_num = self.mask_number_text(num_str)
                    text = text[:m.start()] + f"{masked_num}{unit_str}" + text[m.end():]
                    stats["number_count"] += 1

        # 3.4 日期与年份数据
        if self.config.mask_dates:
            for m in reversed(list(self.re_dates.finditer(text))):
                val = m.group(0)
                if "\x02" in val or "\x03" in val:
                    continue
                num_match = re.match(r"^(\d+)\s*", val)
                if num_match:
                    num_str = num_match.group(1)
                    unit_str = val[len(num_match.group(0)):]
                    masked_num = self.mask_number_text(num_str)
                    text = text[:m.start()] + f"{masked_num}{unit_str}" + text[m.end():]
                    stats["number_count"] += 1

        # 3.5 剩余独立纯数字
        if self.config.mask_standalone_numbers:
            for m in reversed(list(self.re_standalone_number.finditer(text))):
                val = m.group(0)
                if "\x02" in val or "\x03" in val:
                    continue
                masked_num = self.mask_number_text(val)
                text = text[:m.start()] + masked_num + text[m.end():]
                stats["number_count"] += 1

        # 第 4 步：精准还原受保护的序号及白名单
        if token_map:
            protector = SequenceProtector(
                whitelist=self.config.whitelist,
                protect_chinese_seq=self.config.protect_chinese_seq,
                protect_arabic_seq=self.config.protect_arabic_seq,
                protect_special_seq=self.config.protect_special_seq,
            )
            text = protector.restore(text, token_map)

        stats["total_count"] = stats["entity_count"] + stats["number_count"]
        return text, stats
