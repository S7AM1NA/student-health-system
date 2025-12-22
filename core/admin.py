from django.contrib import admin
from .models import (
    CustomUser, SleepRecord, SportRecord, FoodItem, Meal, MealItem,
    UserHealthGoal, Friendship, Comment,
    SystemLog, BodyMetric, ArticleCategory, HealthArticle, UserReadHistory
)

# 1. 用户相关
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'gender', 'date_of_birth', 'is_staff')
    search_fields = ('username', 'email')

# 2. 健康记录
@admin.register(SleepRecord)
class SleepRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'sleep_time', 'wakeup_time', 'duration')
    list_filter = ('user',)

@admin.register(SportRecord)
class SportRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'sport_type', 'duration_minutes', 'calories_burned', 'record_date')
    list_filter = ('sport_type', 'record_date')

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'calories_per_100g', 'protein', 'fat', 'carbohydrates')
    search_fields = ('name',)

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ('user', 'meal_type', 'record_date')
    list_filter = ('meal_type', 'record_date')

@admin.register(MealItem)
class MealItemAdmin(admin.ModelAdmin):
    list_display = ('meal', 'food_item', 'portion', 'calories_calculated')

# 3. 健康目标与社交
@admin.register(UserHealthGoal)
class UserHealthGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_sleep_duration', 'target_sport_duration_minutes', 'target_diet_calories')

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'status', 'created_at')
    list_filter = ('status',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'object_id', 'created_at')

# 4. 新增模型 (Member A)
@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('action', 'details')
    readonly_fields = ('timestamp', 'user', 'action', 'ip_address', 'details')

@admin.register(BodyMetric)
class BodyMetricAdmin(admin.ModelAdmin):
    list_display = ('user', 'weight', 'height', 'bmi', 'record_date')
    list_filter = ('record_date',)

@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(HealthArticle)
class HealthArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'publish_date', 'views')
    list_filter = ('category', 'publish_date')
    search_fields = ('title', 'content')

@admin.register(UserReadHistory)
class UserReadHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'read_time')
    list_filter = ('read_time',)

