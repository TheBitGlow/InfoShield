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
    STRONG_ORG_SUFFIXES,
    WEAK_ORG_SUFFIXES,
    COMMON_SURNAMES,
    NAME_TITLE_PREFIXES,
    NAME_EXCLUDE_WORDS,
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
        auto_detect_names: bool = True,
        mask_units: bool = True,
        mask_industries: bool = True,
        mask_id_card: bool = True,
        mask_phone: bool = True,
        mask_email: bool = True,
        mask_ip: bool = True,
        mask_bank_card: bool = True,
        mask_license_plate: bool = True,
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
        self.auto_detect_names = auto_detect_names
        self.mask_units = mask_units
        self.mask_industries = mask_industries
        self.mask_id_card = mask_id_card
        self.mask_phone = mask_phone
        self.mask_email = mask_email
        self.mask_ip = mask_ip
        self.mask_bank_card = mask_bank_card
        self.mask_license_plate = mask_license_plate
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
            self.mask_ip or
            self.mask_bank_card or
            self.mask_license_plate or
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

        # 4. 扩展实体：IPv4 地址
        self.re_ip = re.compile(
            r"(?<![0-9a-zA-Z_])(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?![0-9a-zA-Z_])"
        )

        # 5. 扩展实体：银行卡号（16~19位）
        self.re_bank_card = re.compile(r"(?<!\d)(?:62\d{14,17}|[4-6]\d{15,18})(?!\d)")

        # 6. 扩展实体：中国车辆号牌（燃油车7位与新能源8位）
        self.re_license_plate = re.compile(
            r"(?<![A-Za-z0-9])[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼][A-Z][A-HJ-NP-Z0-9]{4,5}[A-HJ-NP-Z0-9挂学警港澳练](?![A-Za-z0-9])"
        )

        # 7. 智能中文姓名上下文嗅探正则
        self.re_name_pre = re.compile(
            rf"(?:{NAME_TITLE_PREFIXES})[：:\s]*([{COMMON_SURNAMES}][\u4e00-\u9fa5]{{1,2}})"
        )
        self.re_name_post = re.compile(
            rf"([{COMMON_SURNAMES}][\u4e00-\u9fa5]{{1,2}})(?:同志|先生|女士|老师|顾问|经理|主任|教授|工程师|专员|总监)"
        )
        self.post_title_prefixes = ["同志", "先生", "女士", "老师", "顾问", "经理", "主任", "教授", "工程师", "专员", "总监"]

        # 8. 单位机构后缀识别（综合强弱后缀并防止贪婪误伤）
        all_sufs = set(
            STRONG_ORG_SUFFIXES + WEAK_ORG_SUFFIXES + [
                "有限责任公司", "股份有限公司", "集团有限公司", "科技有限公司", "软件有限公司",
                "有限公司", "企业集团", "研究院", "研究所", "大学", "学院", "医院", "银行", "分行", "支行", "协会"
            ]
        )
        self.org_suffixes = sorted(list(all_sufs), key=len, reverse=True)
        suf_pattern = "|".join(re.escape(s) for s in self.org_suffixes)
        # 采用非贪婪模式匹配前置 2~12 字
        self.re_raw_org = re.compile(rf"([\u4e00-\u9fa5A-Za-z0-9]{{2,12}}?(?:{suf_pattern}))")
        self.stop_lead_words = [
            "来自", "位于", "设立在", "设立于", "任职于", "就职于", "服务于", "投资", "收购",
            "联合", "携手", "以及", "由", "与", "和", "同", "及", "在", "于", "向", "从",
            "到了", "来到", "去了", "去", "到", "考察了", "考察", "参观了", "参观", "走访了", "走访",
            "调研了", "调研", "访问了", "访问", "拜访了", "拜访", "签署了", "前往了", "前往", "交流",
            "组织", "开展", "推动", "支持", "帮助", "协助", "他是", "她是", "他", "她", "它", "我们",
            "他们", "你们", "今天", "昨天", "明天", "目前", "随后", "此前", "项目", "经", "毕业于", "就读于", "考入"
        ]

        # 9.1 金额与货币数据：带货币符号或带中文货币单位
        # 符号金额：¥1,500.00, $500, €300, £250
        self.re_currency_sym = re.compile(
            rf"(?:[¥$€￥£]|RMB|USD|HKD|EUR|GBP)\s*(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?"
        )
        # 中文货币金额：1500万元、500元、30.5万元
        self.re_currency_cn = re.compile(
            r"(?<![0-9a-zA-Z_\x02\x03])(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(?:万|亿|千|百|元|角|分|美金|美元|港币|欧|镑)"
        )

        # 9.2 占比与百分比：35.8%、100%、15.6个百分点、5‰
        self.re_percentages = re.compile(
            r"(?<![0-9a-zA-Z_\x02\x03])(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(?:%|‰|个百分点)"
        )

        # 9.3 人数与统计数量量词：150人、5名、80户、3项、5个、10套、20台、30辆、50家、2.5倍等
        count_units = r"(?:人|名|次|户|条|项|个|套|台|辆|家|宗|件|批|吨|千克|kg|m|km|㎡|m³|岁|点|倍)"
        self.re_counts = re.compile(
            rf"(?<![0-9a-zA-Z_\x02\x03])(?:\d{{1,3}}(?:,\d{{3}})+|\d+(?:\.\d+)?)\s*{count_units}"
        )

        # 9.4 日期与年份：2024年、12月、15日
        self.re_dates = re.compile(
            r"(?<![0-9a-zA-Z_\x02\x03])(?:\d{2,4}\s*年|\d{1,2}\s*月|\d{1,2}\s*[日号])"
        )

        # 9.5 独立纯数字或小数（如 100, 3.1415, 12, 5）
        self.re_standalone_number = re.compile(
            r"(?<![0-9a-zA-Z_\x02\x03])\d+(?:,\d{3})*(?:\.\d+)?(?![0-9a-zA-Z_\x02\x03])"
        )

    def extract_names(self, text: str) -> Set[str]:
        """基于上下文公文称谓和百家姓自动识别正文人名
        """
        names = set()
        for m in self.re_name_pre.finditer(text):
            name = m.group(1)
            for pt in self.post_title_prefixes:
                if name.endswith(pt[0]):
                    name = name[:-1]
                    break
            if name and name not in NAME_EXCLUDE_WORDS and len(name) >= 2:
                names.add(name)

        for m in self.re_name_post.finditer(text):
            name = m.group(1)
            if name and name not in NAME_EXCLUDE_WORDS and len(name) >= 2:
                names.add(name)

        return names

    def extract_organizations(self, text: str) -> List[Tuple[str, int, int]]:
        """基于非贪婪匹配与停用词过滤提取机构单位名，防止误伤整句
        """
        results = []
        for m in self.re_raw_org.finditer(text):
            full = m.group(1)
            start = m.start(1)
            end = m.end(1)

            matched_s = None
            for s in self.org_suffixes:
                if full.endswith(s):
                    matched_s = s
                    break
            if not matched_s:
                continue

            cleaned = full
            while True:
                matched_sw = False
                for sw in sorted(self.stop_lead_words, key=len, reverse=True):
                    if cleaned.startswith(sw):
                        rem = cleaned[len(sw):]
                        if rem.endswith(matched_s) and len(rem) - len(matched_s) >= 2:
                            start += len(sw)
                            cleaned = rem
                            matched_sw = True
                            break
                if matched_sw:
                    continue

                # 检查首字是否为停用字符/介词/助词
                if len(cleaned) - len(matched_s) > 2 and cleaned[0] in "在到去来回进出和与从向的是有对于关于中把被由及跟或了过着并且又即随":
                    start += 1
                    cleaned = cleaned[1:]
                    continue

                break

            prefix = cleaned[:-len(matched_s)]
            if 2 <= len(prefix) <= 12:
                results.append((cleaned, start, start + len(cleaned)))

        return results

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

        if self.config.mask_names:
            if self.config.custom_names:
                active_entities.update(self.config.custom_names)
            if self.config.auto_detect_names:
                detected_names = self.extract_names(text)
                active_entities.update(detected_names)

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

        # 2.5 扩展实体：IPv4 地址
        if self.config.mask_ip:
            matches = list(self.re_ip.finditer(text))
            if matches:
                for m in reversed(matches):
                    ip_str = m.group(0)
                    if "\x02" in ip_str or "\x03" in ip_str:
                        continue
                    stats["entity_count"] += 1
                    masked_val = self.mask_entity_text(ip_str)
                    text = text[:m.start()] + masked_val + text[m.end():]

        # 2.6 扩展实体：银行卡号
        if self.config.mask_bank_card:
            matches = list(self.re_bank_card.finditer(text))
            if matches:
                for m in reversed(matches):
                    card_str = m.group(0)
                    if "\x02" in card_str or "\x03" in card_str:
                        continue
                    stats["entity_count"] += 1
                    masked_val = self.mask_entity_text(card_str)
                    text = text[:m.start()] + masked_val + text[m.end():]

        # 2.7 扩展实体：中国车辆号牌
        if self.config.mask_license_plate:
            matches = list(self.re_license_plate.finditer(text))
            if matches:
                for m in reversed(matches):
                    plate_str = m.group(0)
                    if "\x02" in plate_str or "\x03" in plate_str:
                        continue
                    stats["entity_count"] += 1
                    masked_val = self.mask_entity_text(plate_str)
                    text = text[:m.start()] + masked_val + text[m.end():]

        # 2.8 智能机构/单位识别（防贪婪过滤）
        if self.config.mask_units and self.config.auto_detect_orgs:
            org_matches = self.extract_organizations(text)
            if org_matches:
                for org_str, start, end in reversed(org_matches):
                    if "\x02" in org_str or "\x03" in org_str:
                        continue
                    stats["entity_count"] += 1
                    masked_val = self.mask_entity_text(org_str)
                    text = text[:start] + masked_val + text[end:]

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
