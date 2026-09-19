"""单元测试：验证脱敏规则与序号保护
"""

import unittest
from gearify.core.desensitizer import Desensitizer, DesensitizerConfig


class TestDesensitizer(unittest.TestCase):

    def setUp(self):
        config = DesensitizerConfig(
            custom_names=["张三", "李小龙", "欧阳明月"],
            custom_units=["腾讯", "百度科技", "研发一部", "部"],
            custom_industries=["互联网", "金融", "新能源汽车"],
            whitelist=["Gearify安全规范", "2024标准"],
        )
        self.desensitizer = Desensitizer(config)

    def test_entity_length_capping(self):
        """测试实体脱敏长度限制：1字=×, 2字=××, >=3字=××× (最长3个)
        """
        # 1字实体
        res, _ = self.desensitizer.desensitize("所属归类：部")
        self.assertEqual(res, "所属归类：×")

        # 2字实体
        res, _ = self.desensitizer.desensitize("联系人：张三，所属单位：腾讯，从事行业：金融")
        self.assertEqual(res, "联系人：××，所属单位：××，从事行业：××")

        # 3字实体
        res, _ = self.desensitizer.desensitize("联系人：李小龙，所属单位：研发一部，从事行业：互联网")
        self.assertEqual(res, "联系人：×××，所属单位：×××，从事行业：×××")

        # 4字及以上实体（必须截断在3个×）
        res, _ = self.desensitizer.desensitize("联系人：欧阳明月，所属单位：百度科技，从事行业：新能源汽车")
        self.assertEqual(res, "联系人：×××，所属单位：×××，从事行业：×××")

    def test_number_length_capping(self):
        """测试数据脱敏长度限制：1位数字=×, 2位及以上数字/百分比/金额=×× (最长2个)
        """
        # 1位数字
        res, _ = self.desensitizer.desensitize("接待了5人，完成3项指标，评分8分")
        self.assertIn("×人", res)
        self.assertIn("×项指标", res)
        self.assertIn("×分", res)

        # 2位及以上数字、百分比、金额
        res, _ = self.desensitizer.desensitize("销售额1500万元，增长35.8%，签约28家，参与员工120人")
        self.assertIn("××万元", res)
        self.assertIn("××%", res)
        self.assertIn("××家", res)
        self.assertIn("××人", res)

        # 货币符号
        res, _ = self.desensitizer.desensitize("单笔交易金额为 ¥128,000.00 元")
        self.assertIn("¥××", res)

    def test_sequence_protection(self):
        """测试大纲与段落序号保护不受破坏
        """
        sample = """
一、业务概述
（一）基本情况
1. 第一季度经营指标
1.1 销售团队
① 组建5人攻坚小组
② 创收250万元
2. 第二季度部署
第一章 考核准则
第3条 奖励细则
(1) 评选优秀员工3名
A. 考核标准
"""
        res, _ = self.desensitizer.desensitize(sample)
        
        # 序号严禁被替换
        self.assertIn("一、业务概述", res)
        self.assertIn("（一）基本情况", res)
        self.assertIn("1. 第一季度", res)
        self.assertIn("1.1 销售团队", res)
        self.assertIn("① 组建×人攻坚小组", res)
        self.assertIn("② 创收××万元", res)
        self.assertIn("2. 第二季度", res)
        self.assertIn("第一章 考核准则", res)
        self.assertIn("第3条 奖励细则", res)
        self.assertIn("(1) 评选优秀员工×名", res)
        self.assertIn("A. 考核标准", res)

    def test_id_and_phone(self):
        """测试身份证和手机号
        """
        text = "居民身份证：420102199001011234，手机：13812345678"
        res, _ = self.desensitizer.desensitize(text)
        # 身份证和手机号作为长实体，应替换为3个×
        self.assertIn("居民身份证：×××", res)
        self.assertIn("手机：×××", res)

    def test_whitelist(self):
        """测试白名单豁免
        """
        text = "遵循 Gearify安全规范 与 2024标准 执行"
        res, _ = self.desensitizer.desensitize(text)
        self.assertIn("Gearify安全规范", res)
        self.assertIn("2024标准", res)

    def test_anti_greedy_org_protection(self):
        """测试机构防贪婪匹配与停用词过滤，杜绝误伤整句
        """
        # 1. 日常口语中的办公室、医院不应被吞噬整句
        text1 = "张三和李四今天一起来到办公室"
        res1, _ = self.desensitizer.desensitize(text1)
        self.assertIn("办公室", res1)
        self.assertIn("今天一起来到", res1)

        text2 = "他在办公室吃午饭，下午去医院看病"
        res2, _ = self.desensitizer.desensitize(text2)
        self.assertIn("吃午饭", res2)
        self.assertIn("看病", res2)

        # 2. 真实企业/机构正确脱敏为 3 个 ×
        text3 = "他来自华为云计算技术有限公司进行交流，随后访问了清华大学"
        res3, _ = self.desensitizer.desensitize(text3)
        self.assertIn("他来自×××进行交流", res3)
        self.assertIn("随后访问了×××", res3)

    def test_contextual_name_detection(self):
        """测试基于公文称谓和百家姓的智能姓名探测
        """
        # 前置引导词 + 姓名
        text1 = "本次项目联系人：王建国，技术顾问：周华健"
        res1, _ = self.desensitizer.desensitize(text1)
        self.assertIn("联系人：×××", res1)
        self.assertIn("技术顾问：×××", res1)

        # 后置尊称/职务 + 姓名
        text2 = "参加例会的有赵立经理与陈华同志"
        res2, _ = self.desensitizer.desensitize(text2)
        self.assertIn("××经理", res2)
        self.assertIn("××同志", res2)

        # 非人名排除词不误伤
        text3 = "关键是把握正确方向，李子成熟了"
        res3, _ = self.desensitizer.desensitize(text3)
        self.assertEqual(text3, res3)

    def test_extended_entities(self):
        """测试扩展敏感类型：IPv4 地址、银行卡号、车牌号
        """
        # IPv4
        text_ip = "管理控制台IP地址为 192.168.1.100 和 10.0.0.1"
        res_ip, _ = self.desensitizer.desensitize(text_ip)
        self.assertIn("192.168.1.100", text_ip)
        self.assertNotIn("192.168.1.100", res_ip)
        self.assertNotIn("10.0.0.1", res_ip)

        # 银行卡号（19位纯数字）
        text_card = "收款银行卡号：6222021234567890123，请核对"
        res_card, _ = self.desensitizer.desensitize(text_card)
        self.assertNotIn("6222021234567890123", res_card)
        self.assertIn("卡号：×××", res_card)

        # 车牌号
        text_plate = "通行车辆号牌：京A88888 以及 粤B12345D"
        res_plate, _ = self.desensitizer.desensitize(text_plate)
        self.assertIn("通行车辆号牌：××× 以及 ×××", res_plate)


if __name__ == "__main__":
    unittest.main()

