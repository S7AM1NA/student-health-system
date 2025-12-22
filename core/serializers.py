# core/serializers.py
from rest_framework import serializers
from django.db.models import Q
from .models import (
    SleepRecord, SportRecord, FoodItem, Meal, MealItem, CustomUser, 
    UserHealthGoal, Friendship, Comment, ContentType,
    BodyMetric, ArticleCategory, HealthArticle, UserReadHistory, SystemLog
)

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
    """用于展示一"餐"的完整信息，包括它包含的所有食物"""
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
        fields = ['id', 'username', 'email', 'gender', 'date_of_birth']
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

class FriendshipSerializer(serializers.ModelSerializer):
    """
    【最终功能版】通过重写create方法，将所有创建逻辑内聚到Serializer中。
    """
    from_user_info = UserProfileSerializer(source='from_user', read_only=True)
    to_user_info = UserProfileSerializer(source='to_user', read_only=True)
    to_user_username = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Friendship
        fields = [
            'id', 'from_user', 'to_user', 'status', 'created_at',
            'from_user_info', 'to_user_info',
            'from_user_can_be_viewed', 'to_user_can_be_viewed',
            'to_user_username'
        ]
        read_only_fields = ['from_user', 'to_user', 'status', 'created_at', 'from_user_info', 'to_user_info']

    def create(self, validated_data):
        # 1. 从 validated_data 中弹出 to_user_username，这样它就不会被传给 Friendship.objects.create()
        to_user_username = validated_data.pop('to_user_username')
        
        # 2. 从上下文中获取请求的发起者
        from_user = self.context['request'].user

        # 3. 查找目标用户
        try:
            to_user = CustomUser.objects.get(username=to_user_username)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError(f"找不到用户名为 '{to_user_username}' 的用户。")

        # 4. 执行所有验证逻辑
        if to_user == from_user:
            raise serializers.ValidationError("你不能添加自己为好友。")
        
        if Friendship.objects.filter(
            (Q(from_user=from_user, to_user=to_user) | 
             Q(from_user=to_user, to_user=from_user))
        ).exists():
            raise serializers.ValidationError("你们之间已经存在好友关系或待处理的请求。")
            
        # 5. 使用正确的字段创建 Friendship 实例
        friendship = Friendship.objects.create(
            from_user=from_user, 
            to_user=to_user, 
            status=Friendship.STATUS_PENDING
        )
        return friendship

class CommentSerializer(serializers.ModelSerializer):
    """
    序列化评论数据。
    """
    # 显示评论作者的用户名
    author_username = serializers.CharField(source='user.username', read_only=True)
    # 允许前端通过模型名称（如 'sleeprecord'）来指定评论对象，更方便
    content_type = serializers.SlugRelatedField(
        slug_field='model',
        queryset=ContentType.objects.all()
    )

    class Meta:
        model = Comment
        fields = [
            'id', 'author_username', 'text', 'created_at',
            'content_type', 'object_id', 'user'
        ]
        read_only_fields = ['id', 'author_username', 'created_at', 'user']


# ============================================================
# 新增序列化器 (Member A)
# ============================================================

class BodyMetricSerializer(serializers.ModelSerializer):
    """
    身体指标序列化器：用于记录和展示用户的体重、身高、BMI。
    BMI 由后端自动计算，前端只需提交 weight 和 height。
    """
    class Meta:
        model = BodyMetric
        fields = ['id', 'user', 'weight', 'height', 'bmi', 'record_date']
        read_only_fields = ['id', 'user', 'bmi']


class ArticleCategorySerializer(serializers.ModelSerializer):
    """
    文章分类序列化器。
    """
    article_count = serializers.SerializerMethodField()

    class Meta:
        model = ArticleCategory
        fields = ['id', 'name', 'description', 'article_count']

    def get_article_count(self, obj):
        return obj.articles.count()


class HealthArticleSerializer(serializers.ModelSerializer):
    """
    健康文章序列化器。
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    author_name = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = HealthArticle
        fields = [
            'id', 'title', 'content', 'category', 'category_name',
            'author', 'author_name', 'publish_date', 'views'
        ]
        read_only_fields = ['id', 'author', 'author_name', 'publish_date', 'views']


class UserReadHistorySerializer(serializers.ModelSerializer):
    """
    用户阅读历史序列化器。
    """
    article_title = serializers.CharField(source='article.title', read_only=True)

    class Meta:
        model = UserReadHistory
        fields = ['id', 'user', 'article', 'article_title', 'read_time']
        read_only_fields = ['id', 'user', 'read_time']


class SystemLogSerializer(serializers.ModelSerializer):
    """
    系统日志序列化器（只读，仅供管理员查看）。
    """
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = SystemLog
        fields = ['id', 'username', 'action', 'ip_address', 'timestamp', 'details']
        read_only_fields = fields  # 全部只读