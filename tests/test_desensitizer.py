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


if __name__ == "__main__":
    unittest.main()
