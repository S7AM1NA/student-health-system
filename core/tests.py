# core/tests.py

import json
from pathlib import Path
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from .models import CustomUser, FoodItem, UserHealthGoal, Meal, MealItem, SportRecord
from datetime import date

class SmartDietRecommendationV3Tests(APITestCase):
    """
    测试 V3.0: 动态运动感知智能饮食推荐API
    此测试将在一个包含完整食物库数据的环境中运行。
    """

    @classmethod
    def setUpTestData(cls):
        """
        在整个测试类运行前，从项目中的'data'目录导入所有食物数据到测试数据库中。
        """
        # 1. 创建测试用户和目标
        cls.user = CustomUser.objects.create_user(
            username='testuser_v3', 
            password='testpassword123',
            gender='M' # 设定性别以使用BMR
        )
        cls.goal = UserHealthGoal.objects.create(
            user=cls.user,
            target_diet_calories=2000 # 注意：这个字段现在的作用变小了，BMR是主要基准
        )
        
        # 2. 导入完整的食物数据库
        print("\n[测试数据准备] 正在将 'data' 目录下的所有JSON文件导入到测试数据库...")
        
        data_dir = Path(__file__).resolve().parent.parent / 'food_data_json'

        if not data_dir.is_dir():
            raise FileNotFoundError(f"测试数据目录 '{data_dir}' 未找到。")

        json_files = list(data_dir.glob('*.json'))
        if not json_files:
            raise FileNotFoundError(f"在 '{data_dir}' 中没有找到任何 .json 文件。")

        food_items_to_create = []
        for file_path in json_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                items = json.load(f)
                for item in items:
                    try:
                        food_data = {
                            'name': item.get('foodName'),
                            'product_code': item.get('foodCode'),
                            'calories_per_100g': float(item.get('energyKCal', 0)),
                            'protein': float(item.get('protein', 0)),
                            'fat': float(item.get('fat', 0)),
                            'carbohydrates': float(item.get('CHO', 0)),
                        }
                        # 确保核心数据有效，特别是product_code
                        if food_data['name'] and food_data['product_code']:
                            food_items_to_create.append(FoodItem(**food_data))
                    except (ValueError, TypeError):
                        continue
        
        # 使用 bulk_create 批量创建，忽略已存在的product_code
        FoodItem.objects.bulk_create(food_items_to_create, ignore_conflicts=True)
        print(f"[测试数据准备] 成功加载 {FoodItem.objects.count()} 条食物数据。")


    def setUp(self):
        """在每个测试方法运行前，进行用户登录。"""
        self.client.force_authenticate(user=self.user)

    def _get_recommendation(self, test_date, meal_type):
        """辅助方法，用于发起API请求"""
        url = f'/api/recommendations/diet/?date={test_date}&meal_type={meal_type}'
        return self.client.get(url, format='json')

    def _print_recommendations(self, recommendations):
        """以可读格式打印推荐的套餐详情。"""
        self.assertTrue(isinstance(recommendations, list))
        print("\n--- 推荐套餐详情 ---")
        if not recommendations:
            print("  (本次未生成推荐)")
            return
        for i, rec in enumerate(recommendations):
            macros = rec.get('total_macros', {})
            p, c, f = macros.get('protein', 0), macros.get('carbs', 0), macros.get('fat', 0)
            print(f"套餐 {i+1} (总热量: {rec.get('total_calories', 'N/A')} 大卡) | 营养: 碳 {c}g, 蛋 {p}g, 脂 {f}g")
            items = rec.get('items', [])
            for item in items:
                print(f"  - {item.get('name', '未知食物')}: {item.get('portion_g', 'N/A')}g")
        print("--------------------")

    def test_no_sport_day_recommendation(self):
        """场景一：无运动日，应使用默认营养配比。"""
        print("\n[测试场景一：无运动日（基准测试）]")
        response = self._get_recommendation(test_date='2024-01-01', meal_type='lunch')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        context = response.data.get('recommendation_context', {})
        # 验证使用的是默认配比
        self.assertEqual(context.get('used_macro_ratios', {}).get('protein'), 0.25)
        
        print("成功验证：无运动日使用默认营养配比。推荐套餐如下：")
        self._print_recommendations(response.data.get('recommendations'))

    def test_post_strength_training_recommendation(self):
        """场景二：力量训练后，应使用高蛋白配比。"""
        print("\n[测试场景二：力量训练后]")
        test_date = '2024-01-02'
        SportRecord.objects.create(
            user=self.user,
            sport_type="大重量杠铃深蹲",
            duration_minutes=60,
            calories_burned=400,
            record_date=test_date
        )
        response = self._get_recommendation(test_date=test_date, meal_type='dinner')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        context = response.data.get('recommendation_context', {})
        # 验证使用的是高蛋白配比
        self.assertEqual(context.get('used_macro_ratios', {}).get('protein'), 0.40)
        
        recommendations = response.data.get('recommendations', [])
        self.assertTrue(len(recommendations) > 0)
        # 验证推荐结果中蛋白质含量确实很高
        macros = recommendations[0]['total_macros']
        self.assertGreater(macros['protein'], macros['fat'] * 1.5, "高蛋白餐的蛋白质应远高于脂肪")

        print("成功验证：力量训练后使用高蛋白配比。推荐套餐如下：")
        self._print_recommendations(recommendations)

    def test_post_endurance_training_recommendation(self):
        """场景三：耐力训练后，应使用高碳水配比。"""
        print("\n[测试场景三：耐力训练后]")
        test_date = '2024-01-03'
        SportRecord.objects.create(
            user=self.user,
            sport_type="户外长跑1小时",
            duration_minutes=60,
            calories_burned=500,
            record_date=test_date
        )
        response = self._get_recommendation(test_date=test_date, meal_type='dinner')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        context = response.data.get('recommendation_context', {})
        # 验证使用的是高碳水配比
        self.assertEqual(context.get('used_macro_ratios', {}).get('carbs'), 0.55)
        
        recommendations = response.data.get('recommendations', [])
        self.assertTrue(len(recommendations) > 0)
        # 验证推荐结果中碳水含量是最高的
        macros = recommendations[0]['total_macros']
        self.assertGreater(macros['carbs'], macros['protein'], "高碳水餐的碳水应高于蛋白质")

        print("成功验证：耐力训练后使用高碳水配比。推荐套餐如下：")
        self._print_recommendations(recommendations)

    def test_no_recommendation_when_calories_met_with_sport(self):
        """场景四：即使运动了，但热量已超标，仍不应推荐。"""
        print("\n[测试场景四：运动后但热量已达标（回归测试）]")
        test_date = '2024-01-04'
        # 运动消耗300大卡，动态目标变为 1800(BMR) + 300 = 2100
        SportRecord.objects.create(
            user=self.user, sport_type="游泳", duration_minutes=45, 
            calories_burned=300, record_date=test_date
        )
        # 摄入2200大卡，超过动态目标
        meal = Meal.objects.create(user=self.user, meal_type='lunch', record_date=test_date)
        food = FoodItem.objects.order_by('-calories_per_100g').first()
        portion = (2200 / food.calories_per_100g) * 100
        MealItem.objects.create(meal=meal, food_item=food, portion=portion)
        
        response = self._get_recommendation(test_date=test_date, meal_type='dinner')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'info')
        self.assertIn("今日热量已基本达标", response.data['message'])

        print("成功验证：运动后但热量达标，不再提供推荐。")