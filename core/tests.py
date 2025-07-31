# core/tests.py

import json
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, time, datetime

from rest_framework.test import APITestCase
from rest_framework import status

from .models import CustomUser, SleepRecord, SportRecord, Meal, MealItem, FoodItem

# ----------------------------------------------------------------------
# 测试的组织结构：
# 1. BaseAPITestCase: 一个基础类，用于创建所有测试都需要共享的用户和数据。
# 2. 针对每个主要功能的测试类，继承自 BaseAPITestCase。
#    - AuthAPITests: 测试注册、登录、注销。
#    - ProfileAPITests: 测试个人档案。
#    - SleepAPITests: 测试睡眠记录的所有 CRUD 和自定义接口。
#    - SportAPITests: 测试运动记录的所有 CRUD 和自定义接口。
#    - MealAPITests: 测试餐次和餐品的所有 CRUD 和自定义接口。
#    - DashboardAPITests: 测试核心的看板聚合数据接口。
# ----------------------------------------------------------------------


class BaseAPITestCase(APITestCase):
    """
    一个基础的测试用例类，为所有其他测试类提供共享的设置。
    """
    def setUp(self):
        """
        在所有测试执行前运行，创建共享的资源。
        """
        # 创建主测试用户
        self.user = CustomUser.objects.create_user(
            username='testuser', 
            password='testpassword123',
            email='test@example.com',
            gender='M',
            date_of_birth='2000-01-01'
        )

        # 创建另一个用户，用于测试数据隔离和权限
        self.other_user = CustomUser.objects.create_user(
            username='otheruser', 
            password='otherpassword123',
            email='other@example.com'
        )

        # 创建一个共享的食物库条目
        self.food_item = FoodItem.objects.create(name='苹果', calories_per_100g=52)

        # 预定义日期
        self.today = timezone.now().date()
        self.yesterday = self.today - timedelta(days=1)


class AuthAPITests(BaseAPITestCase):
    """测试认证相关的API (/api/register/, /api/login/, /api/logout/)"""

    def test_user_registration_success(self):
        """测试：成功注册一个新用户"""
        url = reverse('api-register')
        data = {'username': 'newuser', 'password': 'newpassword', 'email': 'new@example.com'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(username='newuser').exists())

    def test_user_registration_duplicate_username(self):
        """测试：使用已存在的用户名注册应失败"""
        url = reverse('api-register')
        data = {'username': self.user.username, 'password': 'password', 'email': 'diff@example.com'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        """测试：使用正确的凭据登录"""
        url = reverse('api-login')
        data = {'username': self.user.username, 'password': 'testpassword123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('user_id', response_data)

    def test_user_login_failed(self):
        """测试：使用错误的密码登录应失败"""
        url = reverse('api-login')
        data = {'username': self.user.username, 'password': 'wrongpassword'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_logout(self):
        """测试：已登录用户可以成功注销"""
        # 先登录
        self.client.force_authenticate(user=self.user)
        # 再注销
        url = reverse('api-logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ProfileAPITests(BaseAPITestCase):
    """测试个人档案API (/api/profile/)"""

    def setUp(self):
        # 继承父类的setUp并模拟登录
        super().setUp()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('api-profile')

    def test_get_profile_success(self):
        """测试：已登录用户可以获取自己的档案"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)

    def test_get_profile_unauthenticated(self):
        """测试：未登录用户无法获取档案"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_profile_success(self):
        """测试：用户可以成功更新自己的档案"""
        data = {'gender': 'F', 'email': 'updated@example.com'}
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.gender, 'F')
        self.assertEqual(self.user.email, 'updated@example.com')


class SportAPITests(BaseAPITestCase):
    """测试运动记录API (/api/sports/)"""
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)
        
        # 创建一些测试数据
        self.sport_today = SportRecord.objects.create(user=self.user, sport_type='跑步', duration_minutes=30, calories_burned=300, record_date=self.today)
        self.sport_yesterday = SportRecord.objects.create(user=self.user, sport_type='游泳', duration_minutes=45, calories_burned=400, record_date=self.yesterday)
        self.other_user_sport = SportRecord.objects.create(user=self.other_user, sport_type='篮球', duration_minutes=60, calories_burned=500, record_date=self.today)
        
        self.list_url = reverse('sportrecord-list')
        self.detail_url = reverse('sportrecord-detail', kwargs={'pk': self.sport_today.pk})

    def test_list_sports_records(self):
        """测试：获取运动记录列表，应只包含自己的记录"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # 应该只看到自己的2条记录
        self.assertNotIn(self.other_user_sport.id, [r['id'] for r in response.data])

    def test_filter_sports_by_date(self):
        """测试：按日期筛选运动记录"""
        response = self.client.get(self.list_url, {'record_date': self.today})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.sport_today.id)

    def test_create_sport_record(self):
        """测试：创建一条新的运动记录"""
        data = {'sport_type': '瑜伽', 'duration_minutes': 60, 'calories_burned': 150, 'record_date': self.today.strftime('%Y-%m-%d')}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SportRecord.objects.filter(user=self.user).count(), 3)

    def test_retrieve_own_sport_record(self):
        """测试：获取自己拥有的单条运动记录详情"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['sport_type'], self.sport_today.sport_type)

    def test_cannot_retrieve_others_sport_record(self):
        """测试：无法获取他人拥有的运动记录详情，应返回404"""
        url = reverse('sportrecord-detail', kwargs={'pk': self.other_user_sport.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_sport_record(self):
        """测试：可以删除自己的运动记录"""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SportRecord.objects.filter(pk=self.sport_today.pk).exists())

    def test_sport_today_check(self):
        """测试：today-check接口"""
        url = reverse('sportrecord-today-check')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['record_exists'])
        self.assertEqual(response.data['record_id'], self.sport_today.id)


class MealAPITests(BaseAPITestCase):
    """测试餐次和餐品API (/api/meals/ 和 /api/meal-items/)"""
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

        # 创建餐次和餐品数据
        self.meal = Meal.objects.create(user=self.user, meal_type='lunch', record_date=self.today)
        self.meal_item = MealItem.objects.create(meal=self.meal, food_item=self.food_item, portion=150) # 150g 苹果
        
        # 重新获取 meal 对象，确保 @property 能计算最新的 total_calories
        self.meal.refresh_from_db()

        self.list_url = reverse('meal-list')
        self.detail_url = reverse('meal-detail', kwargs={'pk': self.meal.pk})
        self.item_list_url = reverse('mealitem-list')
        self.item_detail_url = reverse('mealitem-detail', kwargs={'pk': self.meal_item.pk})

    def test_list_meals_with_nested_items_and_calories(self):
        """测试：获取餐次列表，检查嵌套数据和总热量计算"""
        response = self.client.get(self.list_url, {'record_date': self.today})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        meal_data = response.data[0]
        self.assertEqual(meal_data['total_calories'], (self.food_item.calories_per_100g / 100) * 150)
        self.assertEqual(len(meal_data['meal_items']), 1)
        self.assertEqual(meal_data['meal_items'][0]['id'], self.meal_item.id)

    def test_create_meal(self):
        """测试：创建一顿新的餐次"""
        data = {'meal_type': 'dinner', 'record_date': self.today.strftime('%Y-%m-%d')}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Meal.objects.filter(user=self.user, meal_type='dinner').exists())

    def test_create_meal_item(self):
        """测试：为一餐添加一个新的餐品"""
        data = {'meal': self.meal.id, 'food_item': self.food_item.id, 'portion': 200}
        response = self.client.post(self.item_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.meal.meal_items.count(), 2)
        
        # 检查自动计算的卡路里
        self.assertAlmostEqual(response.data['calories_calculated'], (self.food_item.calories_per_100g / 100) * 200)

    def test_delete_meal_cascades_to_items(self):
        """测试：删除一餐会级联删除其下的所有餐品"""
        meal_item_id = self.meal_item.id
        self.client.delete(self.detail_url)
        self.assertFalse(Meal.objects.filter(pk=self.meal.pk).exists())
        self.assertFalse(MealItem.objects.filter(pk=meal_item_id).exists())


class DashboardAPITests(BaseAPITestCase):
    """测试看板聚合数据API (/api/dashboard/<date_str>/)"""
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

    def test_dashboard_with_no_data(self):
        """测试：某天没有任何数据时，看板API的返回结构"""
        url = reverse('api-dashboard', kwargs={'date_str': '2025-01-01'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']
        self.assertFalse(data['sleep']['record_exists'])
        self.assertFalse(data['sports']['record_exists'])
        self.assertFalse(data['diet']['record_exists'])
        self.assertEqual(data['health_summary']['status_code'], 'NEUTRAL')

    def test_dashboard_with_all_data_fully_verified(self):
        """
        【增强版】测试：当天有所有类型的数据时，对看板API的返回结果进行全字段校验。
        """
        # ----------------------------------------------------------------------
        # 1. 准备精确的、可预测的测试数据
        # ----------------------------------------------------------------------

        # a. 睡眠数据: 精确睡 7.5 小时
        wakeup_time = timezone.make_aware(datetime.combine(self.today, time(7, 30)))
        sleep_time = wakeup_time - timedelta(hours=7, minutes=30)
        SleepRecord.objects.create(user=self.user, sleep_time=sleep_time, wakeup_time=wakeup_time)

        # b. 运动数据: 创建2条记录，用于测试 SUM 和 COUNT 聚合
        SportRecord.objects.create(user=self.user, sport_type='跑步', duration_minutes=30, calories_burned=250.5, record_date=self.today)
        SportRecord.objects.create(user=self.user, sport_type='拉伸', duration_minutes=15, calories_burned=50, record_date=self.today)
        
        # c. 饮食数据: 创建一餐，包含2个餐品
        meal = Meal.objects.create(user=self.user, meal_type='lunch', record_date=self.today)
        # 餐品1: 150g 苹果 (52 kcal/100g) -> 78 kcal
        MealItem.objects.create(meal=meal, food_item=self.food_item, portion=150) 
        # 餐品2: 200g 鸡胸肉 -> 270 kcal
        chicken = FoodItem.objects.create(name='鸡胸肉', calories_per_100g=135)
        MealItem.objects.create(meal=meal, food_item=chicken, portion=200)

        # ----------------------------------------------------------------------
        # 2. 定义预期结果
        # ----------------------------------------------------------------------
        expected_sleep_duration = 7.5
        expected_sports_duration = 30 + 15
        expected_sports_calories = 250.5 + 50
        expected_sports_count = 2
        expected_diet_calories = (52 / 100 * 150) + (135 / 100 * 200) # 78 + 270 = 348
        
        # 预测健康建议 (BMR=1500, calories_in=348, sleep=7.5)
        # 因为 0 < 348 < 1500 * 0.8 (1200)，所以预期状态是 LOW_INTAKE
        expected_status_code = "LOW_INTAKE"
        expected_suggestion = "热量摄入不足，身体需要能量来维持活力！"

        # ----------------------------------------------------------------------
        # 3. 发起请求并进行全字段断言
        # ----------------------------------------------------------------------
        url = reverse('api-dashboard', kwargs={'date_str': self.today.strftime('%Y-%m-%d')})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # a. 校验顶层结构
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['message'], f"{self.today.strftime('%Y-%m-%d')} 的健康数据获取成功")
        self.assertEqual(response.data['user']['username'], self.user.username)
        self.assertEqual(response.data['user']['user_id'], self.user.id)
        
        data = response.data['data']
        self.assertEqual(data['date'], self.today.strftime('%Y-%m-%d'))
        
        # b. 校验睡眠数据 (sleep)
        sleep_data = data['sleep']
        self.assertTrue(sleep_data['record_exists'])
        self.assertEqual(sleep_data['duration_hours'], expected_sleep_duration)
        self.assertEqual(sleep_data['sleep_time'], sleep_time.isoformat())
        self.assertEqual(sleep_data['wakeup_time'], wakeup_time.isoformat())
        
        # c. 校验运动数据 (sports)
        sports_data = data['sports']
        self.assertTrue(sports_data['record_exists'])
        self.assertEqual(sports_data['total_calories_burned'], expected_sports_calories)
        self.assertEqual(sports_data['total_duration_minutes'], expected_sports_duration)
        self.assertEqual(sports_data['count'], expected_sports_count)

        # d. 校验饮食数据 (diet)
        diet_data = data['diet']
        self.assertTrue(diet_data['record_exists'])
        # 使用 assertAlmostEqual 对浮点数进行比较更安全
        self.assertAlmostEqual(diet_data['total_calories_eaten'], expected_diet_calories)

        # e. 校验健康摘要 (health_summary)
        summary_data = data['health_summary']
        self.assertEqual(summary_data['status_code'], expected_status_code)
        self.assertEqual(summary_data['suggestion'], expected_suggestion)

    def test_dashboard_triggers_high_intake_suggestion(self):
        """测试：高热量摄入是否能触发对应的健康建议"""
        # 创建一顿极高热量的餐
        high_cal_food = FoodItem.objects.create(name='蛋糕', calories_per_100g=400)
        meal = Meal.objects.create(user=self.user, meal_type='dinner', record_date=self.today)
        MealItem.objects.create(meal=meal, food_item=high_cal_food, portion=1000) # 4000 大卡

        url = reverse('api-dashboard', kwargs={'date_str': self.today.strftime('%Y-%m-%d')})
        response = self.client.get(url)
        self.assertEqual(response.data['data']['health_summary']['status_code'], 'HIGH_INTAKE')

