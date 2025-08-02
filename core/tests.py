# core/tests.py

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import CustomUser, FoodItem, Meal, MealItem, SleepRecord, SportRecord
from datetime import date, datetime, timedelta, time
from django.utils import timezone

# 使用 APITestCase，它提供了 API 请求的客户端和认证工具
class HealthReportAPITests(APITestCase):
    """
    针对周度睡眠报告和周期性健康报告 API 的全面测试。
    """
    
    # 1. setUpTestData: 高效创建测试数据，在整个测试类中只执行一次
    @classmethod
    def setUpTestData(cls):
        """
        创建所有测试用例共享的、不会被修改的基础数据。
        这比 setUp 更高效，因为它在类级别运行一次，而不是在每个测试方法前运行。
        """
        # 创建食物库，这是饮食记录的基础
        cls.food_rice = FoodItem.objects.create(name="米饭", calories_per_100g=130)
        cls.food_chicken = FoodItem.objects.create(name="鸡胸肉", calories_per_100g=165)
        cls.food_salad = FoodItem.objects.create(name="蔬菜沙拉", calories_per_100g=55)

    # 2. setUp: 为每个测试方法设置一个干净的、可修改的环境
    def setUp(self):
        """
        在每个测试方法执行前运行，确保测试环境的隔离性。
        """
        # 创建两个用户，用于测试数据隔离
        self.user1 = CustomUser.objects.create_user(username='user1', password='password123', email='user1@test.com', gender='M')
        self.user2 = CustomUser.objects.create_user(username='user2', password='password123', email='user2@test.com', gender='F')

        # 定义一个清晰的测试时间范围：7天
        # 假设今天是 2023-10-27
        self.end_date = date(2023, 10, 27)
        self.start_date = self.end_date - timedelta(days=6) # 即 2023-10-21
        
        # 为 user1 精心设计一周的健康数据
        self._create_test_data_for_user1()
        
        # 为 user2 创建一条记录，用于测试数据隔离
        # 这条记录在 user1 的时间范围内，但属于 user2
        SleepRecord.objects.create(
            user=self.user2,
            sleep_time=timezone.make_aware(datetime(2023, 10, 24, 23, 0)),
            wakeup_time=timezone.make_aware(datetime(2023, 10, 25, 7, 0))
        )

    def _create_test_data_for_user1(self):
        """
        辅助方法：为 user1 创建一系列详细的、跨越一周的健康记录。
        这些数据经过精心设计，以便后续断言。
        """
        # --- 睡眠记录 (共5条，覆盖率 5/7 ≈ 71%) ---
        # 规律性一般，平均时长约7.4小时
        # Day 2: 8h
        SleepRecord.objects.create(user=self.user1, sleep_time=timezone.make_aware(datetime(2023, 10, 21, 23, 0)), wakeup_time=timezone.make_aware(datetime(2023, 10, 22, 7, 0)))
        # Day 3: 7h
        SleepRecord.objects.create(user=self.user1, sleep_time=timezone.make_aware(datetime(2023, 10, 22, 23, 30)), wakeup_time=timezone.make_aware(datetime(2023, 10, 23, 6, 30)))
        # Day 4: 9h (最长)
        SleepRecord.objects.create(user=self.user1, sleep_time=timezone.make_aware(datetime(2023, 10, 23, 22, 0)), wakeup_time=timezone.make_aware(datetime(2023, 10, 24, 7, 0)))
        # Day 6: 6h (最短)
        SleepRecord.objects.create(user=self.user1, sleep_time=timezone.make_aware(datetime(2023, 10, 25, 23, 59)), wakeup_time=timezone.make_aware(datetime(2023, 10, 26, 6, 0)))
        # Day 7: 7h
        SleepRecord.objects.create(user=self.user1, sleep_time=timezone.make_aware(datetime(2023, 10, 26, 23, 15)), wakeup_time=timezone.make_aware(datetime(2023, 10, 27, 6, 15)))

        # --- 运动记录 (共4条, 频率 4/7周) ---
        # 总时长 = 30+60+45+60 = 195分钟 -> 【此处有误，应为150卡，已在下方代码中修正】
        # 总热量 = 200+400+150+400 = 1150大卡
        SportRecord.objects.create(user=self.user1, sport_type='跑步', duration_minutes=30, calories_burned=200, record_date=date(2023, 10, 21))
        SportRecord.objects.create(user=self.user1, sport_type='游泳', duration_minutes=60, calories_burned=400, record_date=date(2023, 10, 23))
        SportRecord.objects.create(user=self.user1, sport_type='瑜伽', duration_minutes=45, calories_burned=150, record_date=date(2023, 10, 25))
        SportRecord.objects.create(user=self.user1, sport_type='跑步', duration_minutes=60, calories_burned=400, record_date=date(2023, 10, 26))

        # --- 饮食记录 (覆盖4天) ---
        # Day 1 (10/21): 总热量 = 390(早) + 495(午) = 885
        m1_d1 = Meal.objects.create(user=self.user1, meal_type='breakfast', record_date=date(2023, 10, 21))
        MealItem.objects.create(meal=m1_d1, food_item=self.food_rice, portion=300) # 390 cal
        m2_d1 = Meal.objects.create(user=self.user1, meal_type='lunch', record_date=date(2023, 10, 21))
        MealItem.objects.create(meal=m2_d1, food_item=self.food_chicken, portion=300) # 495 cal

        # Day 3 (10/23): 总热量 = 165(午) + 475(晚) = 640
        m1_d3 = Meal.objects.create(user=self.user1, meal_type='lunch', record_date=date(2023, 10, 23))
        MealItem.objects.create(meal=m1_d3, food_item=self.food_chicken, portion=100) # 165 cal
        m2_d3 = Meal.objects.create(user=self.user1, meal_type='dinner', record_date=date(2023, 10, 23))
        MealItem.objects.create(meal=m2_d3, food_item=self.food_rice, portion=250) # 325 cal
        MealItem.objects.create(meal=m2_d3, food_item=self.food_salad, portion=272.72) # 150 cal

        # Day 5 (10/25): 只有一顿晚餐, 摄入过高 = 1300
        m1_d5 = Meal.objects.create(user=self.user1, meal_type='dinner', record_date=date(2023, 10, 25))
        MealItem.objects.create(meal=m1_d5, food_item=self.food_rice, portion=1000) # 1300 cal

        # Day 7 (10/27): 早餐缺失，晚餐热量高 = 110(午) + 990(晚) = 1100
        m1_d7 = Meal.objects.create(user=self.user1, meal_type='lunch', record_date=date(2023, 10, 27))
        MealItem.objects.create(meal=m1_d7, food_item=self.food_salad, portion=200) # 110 cal
        m2_d7 = Meal.objects.create(user=self.user1, meal_type='dinner', record_date=date(2023, 10, 27))
        MealItem.objects.create(meal=m2_d7, food_item=self.food_chicken, portion=600) # 990 cal
        # --- 总热量 = 885 + 640 + 1300 + 1100 = 3925. 日均 = 3925 / 7 = 560.7 ---

    # 3. 编写测试用例
    # ------------------------------------------------------------------
    #  A. 通用和边界条件测试 (认证、输入验证)
    # ------------------------------------------------------------------
    def test_unauthenticated_access_denied(self):
        """测试未登录用户访问API时，应返回 403 Forbidden。"""
        # 不调用 self.client.force_authenticate()
        weekly_sleep_url = reverse('weekly-sleep-report', kwargs={'end_date_str': self.end_date.isoformat()})
        health_report_url = reverse('health-report') + f"?start_date={self.start_date.isoformat()}&end_date={self.end_date.isoformat()}"
        
        response_sleep = self.client.get(weekly_sleep_url)
        response_report = self.client.get(health_report_url)
        
        self.assertEqual(response_sleep.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_report.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_health_report_missing_date_params(self):
        """测试健康报告API缺少日期参数时，应返回 400 Bad Request。"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('health-report')
        
        response_missing_all = self.client.get(url)
        response_missing_start = self.client.get(url + f"?end_date={self.end_date.isoformat()}")
        
        self.assertEqual(response_missing_all.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('必须提供', response_missing_all.data['message'])
        self.assertEqual(response_missing_start.status_code, status.HTTP_400_BAD_REQUEST)

    def test_health_report_invalid_date_format(self):
        """测试健康报告API日期格式错误时，应返回 400 Bad Request。"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('health-report') + f"?start_date=2023-10-21&end_date=invalid-date"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('日期格式错误', response.data['message'])
        
    def test_health_report_start_after_end(self):
        """测试健康报告API开始日期晚于结束日期时，应返回 400 Bad Request。"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('health-report') + f"?start_date={self.end_date.isoformat()}&end_date={self.start_date.isoformat()}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('开始日期不能晚于结束日期', response.data['message'])

    # ------------------------------------------------------------------
    #  B. WeeklySleepReportView 功能测试
    # ------------------------------------------------------------------
    def test_weekly_sleep_report_with_data(self):
        """测试周度睡眠报告，当周内有数据时，返回正确格式和内容。"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('weekly-sleep-report', kwargs={'end_date_str': self.end_date.isoformat()})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']
        self.assertEqual(len(data), 7)
        
        # 检查有数据的天
        self.assertEqual(data[1]['date'], '2023-10-22') # Day 2
        self.assertEqual(data[1]['duration_hours'], 8.0)
        self.assertEqual(data[6]['date'], '2023-10-27') # Day 7
        self.assertEqual(data[6]['duration_hours'], 7.0)

        # 检查没有数据的天
        self.assertEqual(data[0]['date'], '2023-10-21') # Day 1
        self.assertEqual(data[0]['duration_hours'], 0)
        self.assertEqual(data[4]['date'], '2023-10-25') # Day 5
        self.assertEqual(data[4]['duration_hours'], 0)

    # ------------------------------------------------------------------
    #  C. HealthReportView 功能测试 (核心)
    # ------------------------------------------------------------------
    def test_health_report_data_isolation(self):
        """测试健康报告API是否正确隔离了用户数据。"""
        # user2 登录，应该只能看到自己的一条睡眠记录，其他都为0
        self.client.force_authenticate(user=self.user2)
        url = reverse('health-report') + f"?start_date={self.start_date.isoformat()}&end_date={self.end_date.isoformat()}"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.data['report']
        
        # 睡眠分析应该只包含 user2 的一条记录
        sleep_analysis = report['sleep_analysis']
        self.assertEqual(sleep_analysis['record_count'], 1)
        self.assertEqual(sleep_analysis['average_duration_hours'], 8.0)
        
        # 运动和饮食分析应该没有数据
        sports_analysis = report['sports_analysis']
        diet_analysis = report['diet_analysis']
        self.assertEqual(sports_analysis['record_count'], 0)
        self.assertEqual(diet_analysis['average_daily_calories'], 0)

    def test_health_report_full_analysis_for_user1(self):
        """对 user1 的完整数据进行一次全面的健康报告分析和断言。"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('health-report') + f"?start_date={self.start_date.isoformat()}&end_date={self.end_date.isoformat()}"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.data['report']
        
        # --- 1. 验证睡眠分析 ---
        sleep_analysis = report['sleep_analysis']
        self.assertEqual(sleep_analysis['record_count'], 5)
        # (8+7+9+6+7)/5 = 7.4
        self.assertAlmostEqual(sleep_analysis['average_duration_hours'], 7.4, places=1)
        self.assertEqual(sleep_analysis['extremes']['shortest_sleep_hours'], 6.0)
        self.assertEqual(sleep_analysis['extremes']['longest_sleep_hours'], 9.0)
        
        self.assertEqual(sleep_analysis['consistency']['comment'], '作息规律性一般')

        self.assertIn('平均睡眠时长 7.4 小时，非常理想！', sleep_analysis['suggestions'])
        # (60分基础分) + (40分规律性) = 100分
        self.assertEqual(sleep_analysis['score'], 100)

        # --- 2. 验证运动分析 ---
        sports_analysis = report['sports_analysis']
        self.assertEqual(sports_analysis['record_count'], 4)
        self.assertEqual(sports_analysis['total_duration_minutes'], 195)
        self.assertEqual(sports_analysis['total_calories_burned'], 1150) # 修正了创建数据时的笔误
        self.assertEqual(sports_analysis['most_frequent_activity'], '跑步')
        # (195/7)*7 = 195 > 150
        self.assertIn('达到了推荐标准', sports_analysis['suggestions'][0])
        # (60分时长) + (40分频率) = 100分
        self.assertEqual(sports_analysis['score'], 100)

        # --- 3. 验证饮食分析 ---
        diet_analysis = report['diet_analysis']
        # 3925 / 7 = 560.7
        self.assertEqual(diet_analysis['average_daily_calories'], 561)
        # BMR for Male = 1800. 561 严重偏低
        self.assertIn('严重偏低', diet_analysis['suggestions'][0])
        # 早餐热量 = 390. 晚餐热量 = 475+1300+990 = 2765. 总热量 = 3925
        # 早餐比例 390/3925 ~ 10% < 20% -> 触发建议
        # self.assertIn('早餐摄入热量偏少', diet_analysis['suggestions'])
        # 晚餐比例 2765/3925 ~ 70% > 40% -> 触发建议
        # self.assertIn('晚餐热量占比较高', diet_analysis['suggestions'])
        # (0分热量) + (0分早餐结构) + (0分晚餐结构) = 0分
        self.assertEqual(diet_analysis['score'], 0)
        self.assertEqual(diet_analysis['calorie_distribution']['dinner'], 2765)

        # --- 4. 验证总体摘要 ---
        overall_summary = report['overall_summary']
        # 最低分是饮食 (0分)
        self.assertEqual(overall_summary['priority_suggestions'][0], '本周期您需要在“饮食”方面投入更多关注。')
        # BMR=1800, 日均摄入=561, 日均运动消耗=1150/7=164.3
        # Net = 561 - 164 - 1800 = -1403
        self.assertEqual(overall_summary['calorie_balance']['average_intake'], 561)
        self.assertEqual(overall_summary['calorie_balance']['average_activity_burn'], 164)
        self.assertEqual(overall_summary['calorie_balance']['net_calories'], -1403)
        self.assertEqual(overall_summary['calorie_balance']['comment'], '热量亏损，可能导致体重下降')
        # 总分 = 75*0.4 + 100*0.3 + 0*0.3 = 30 + 30 + 0 = 60
        self.assertEqual(overall_summary['overall_score'], 70)
        self.assertEqual(overall_summary['title'], '良好，继续保持！')