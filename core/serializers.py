# core/serializers.py
from rest_framework import serializers
from .models import SleepRecord, SportRecord, FoodItem, Meal, MealItem, CustomUser, UserHealthGoal

class SleepRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SleepRecord
        # 'user' 会自动关联当前登录用户，'duration' 会自动计算，所以前端只需提交两个字段
        fields = ['id', 'sleep_time', 'wakeup_time', 'duration']
        read_only_fields = ['id', 'duration', 'user'] # 这些字段是只读的

class SportRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportRecord
        # 前端需要提交 sport_type, duration_minutes, calories_burned
        fields = ['id', 'sport_type', 'duration_minutes', 'calories_burned', 'record_date']
        # user 和 record_date 都是自动生成的
        read_only_fields = ['id', 'user']

class FoodItemSerializer(serializers.ModelSerializer):
    """用于展示食物库中的食物信息"""
    class Meta:
        model = FoodItem
        fields = ['id', 'name', 'calories_per_100g']


class MealItemSerializer(serializers.ModelSerializer):
    """用于展示一餐中具体的食物条目"""
    # 使用 StringRelatedField 可以直接显示食物的名字，而不是ID，前端会很方便
    food_item_name = serializers.StringRelatedField(source='food_item.name', read_only=True)

    class Meta:
        model = MealItem
        # 前端需要提交 food_item 的ID和 portion(克数)
        fields = ['id', 'meal', 'food_item', 'food_item_name', 'portion', 'calories_calculated']
        read_only_fields = ['id', 'calories_calculated', 'food_item_name']


class MealSerializer(serializers.ModelSerializer):
    """用于展示一“餐”的完整信息，包括它包含的所有食物"""
    # 使用嵌套序列化，当获取一餐的详情时，会把关联的 MealItem 一起显示出来
    meal_items = MealItemSerializer(many=True, read_only=True)
    # 直接从模型的 @property 获取总热量
    total_calories = serializers.FloatField(read_only=True)

    class Meta:
        model = Meal
        # 前端创建时只需要提交 meal_type
        fields = ['id', 'user', 'meal_type', 'record_date', 'total_calories', 'meal_items']
        read_only_fields = ['id', 'user', 'total_calories', 'meal_items']

class UserProfileSerializer(serializers.ModelSerializer):
    """
    用于读取和更新用户个人档案。
    """
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'gender', 'date_of_birth']
        # 用户名在个人档案更新时不应被修改
        read_only_fields = ['username']

class UserHealthGoalSerializer(serializers.ModelSerializer):
    """
    用于读取和更新用户的个人健康目标。
    """
    class Meta:
        model = UserHealthGoal
        # 前端可以提交这四个字段的任意组合来进行更新
        fields = [
            'id', 'user', 
            'target_sleep_duration', 
            'target_sport_duration_minutes', 
            'target_sport_calories',
            'target_diet_calories'
        ]
        # user 字段是自动关联的，不应由前端提交
        read_only_fields = ['id', 'user']