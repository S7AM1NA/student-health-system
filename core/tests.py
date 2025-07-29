import json # 确保在文件顶部导入 json
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from datetime import date, datetime, timedelta
from django.utils import timezone

# 从你的模型中导入所有需要的类
from .models import CustomUser, SleepRecord, SportRecord, FoodItem, Meal, MealItem

class APITestCase(TestCase):
    """
    一个基础的测试类，设置了所有测试用例都需要的东西。
    """
    def setUp(self):
        """
        这个方法在每个测试函数运行前都会被调用。
        我们在这里创建通用的测试数据。
        """
        # 1. 创建一个API客户端，用来模拟HTTP请求
        self.client = APIClient()

        # 2. 创建一个测试用户
        self.test_user_data = {
            'username': 'testuser',
            'password': 'testpassword123',
            'email': 'testuser@example.com'
        }
        self.user = CustomUser.objects.create_user(**self.test_user_data)
        
        # 3. (可选) 创建第二个用户，用于测试数据隔离
        self.other_user = CustomUser.objects.create_user(
            username='otheruser', 
            password='otherpassword', 
            email='other@example.com'
        )

class AuthAPITest(APITestCase):
    """
    专门测试用户认证相关的API (注册、登录、注销)
    """
    def test_user_registration(self):
        """测试新用户能否成功注册"""
        url = reverse('register')
        new_user_data = {
            'username': 'newuser',
            'password': 'newpassword123',
            'email': 'new@example.com'
        }
        response = self.client.post(url, new_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.count(), 3) # 包含 setUp 中创建的两个

    def test_user_login_and_logout(self):
        """测试用户能否成功登录和注销"""
        # 测试登录
        login_url = reverse('login')
        response = self.client.post(login_url, self.test_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        login_data = json.loads(response.content)
        self.assertIn('user_id', login_data)

        # 测试注销
        logout_url = reverse('logout')
        response = self.client.post(logout_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        logout_data = json.loads(response.content)
        self.assertEqual(logout_data['message'], '已成功注销')


class DashboardAPITest(APITestCase):
    """
    专门测试 Dashboard API 的数据聚合和计算正确性
    """
    def setUp(self):
        """
        覆盖父类的 setUp，并创建 Dashboard 需要的特定数据。
        """
        # 先调用父类的 setUp 来创建用户和客户端
        super().setUp()

        # 定义一个目标测试日期
        self.target_date = date(2024, 5, 21)
        
        # === 为 self.user 创建测试数据 ===
        
        # 1. 创建睡眠数据 (起床时间是目标日)
        SleepRecord.objects.create(
            user=self.user,
            # 使用 timezone.make_aware() 来附加时区信息
            sleep_time=timezone.make_aware(datetime(2024, 5, 20, 23, 0)),
            wakeup_time=timezone.make_aware(datetime(2024, 5, 21, 7, 0))
        )

        # 2. 创建运动数据 (两条记录都在目标日)
        SportRecord.objects.create(
            user=self.user, sport_type='跑步', duration_minutes=30, 
            calories_burned=250.5, record_date=self.target_date
        )
        SportRecord.objects.create(
            user=self.user, sport_type='游泳', duration_minutes=30, 
            calories_burned=200, record_date=self.target_date
        )

        # 3. 创建饮食数据 (一餐，包含两个条目)
        food_rice = FoodItem.objects.create(name='米饭', calories_per_100g=116)
        food_chicken = FoodItem.objects.create(name='鸡胸肉', calories_per_100g=133)
        
        meal = Meal.objects.create(user=self.user, meal_type='lunch', record_date=self.target_date)
        MealItem.objects.create(meal=meal, food_item=food_rice, portion=150) # 1.5 * 116 = 174
        MealItem.objects.create(meal=meal, food_item=food_chicken, portion=200) # 2 * 133 = 266

        # === 为 self.other_user 创建无关数据，用于测试隔离性 ===
        SportRecord.objects.create(
            user=self.other_user, sport_type='爬山', duration_minutes=120,
            calories_burned=800, record_date=self.target_date
        )

    def test_dashboard_with_full_data(self):
        """
        测试当天有全部数据时，Dashboard API的计算是否正确。
        """
        # 模拟 self.user 登录
        self.client.force_authenticate(user=self.user)

        # 构造请求URL
        url = reverse('dashboard', kwargs={'date_str': self.target_date.strftime('%Y-%m-%d')})
        response = self.client.get(url)

        # --- 开始断言 ---
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()['data']

        # 验证睡眠数据
        self.assertTrue(data['sleep']['record_exists'])
        self.assertEqual(data['sleep']['duration_hours'], 8.0)

        # 验证运动数据
        self.assertTrue(data['sports']['record_exists'])
        self.assertEqual(data['sports']['total_calories_burned'], 450.5)
        self.assertEqual(data['sports']['total_duration_minutes'], 60)
        self.assertEqual(data['sports']['count'], 2)

        # 验证饮食数据
        self.assertTrue(data['diet']['record_exists'])
        self.assertEqual(data['diet']['total_calories_eaten'], 440) # 174 + 266

        # 验证健康建议 (根据我们的数据，应该是摄入不足)
        self.assertEqual(data['health_summary']['status_code'], 'LOW_INTAKE')

    def test_dashboard_with_no_data(self):
        """
        测试当天没有任何数据时，Dashboard API的返回是否正确。
        """
        self.client.force_authenticate(user=self.user)

        # 请求一个没有任何数据的日期
        no_data_date = self.target_date + timedelta(days=1)
        url = reverse('dashboard', kwargs={'date_str': no_data_date.strftime('%Y-%m-%d')})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()['data']
        message = response.json()['message']

        self.assertFalse(data['sleep']['record_exists'])
        self.assertFalse(data['sports']['record_exists'])
        self.assertFalse(data['diet']['record_exists'])
        self.assertEqual(data['health_summary']['status_code'], 'NEUTRAL')
        self.assertIn("暂无健康数据记录", message)
    
    def test_dashboard_data_isolation(self):
        """
        测试用户只能看到自己的数据，看不到 other_user 的数据。
        """
        # 我们用 self.user 登录，但请求的数据中不应该包含 self.other_user 的运动记录
        self.test_dashboard_with_full_data()