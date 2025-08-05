from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# 1. 扩展默认用户模型，方便未来添加个人信息
class CustomUser(AbstractUser):
    # 在这里可以为用户添加额外的个人健康档案字段
    # 比如：性别、出生日期等。后续可以继续添加别的字段。
    GENDER_CHOICES = [
        ('M', '男'),
        ('F', '女'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True, verbose_name="性别")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="出生日期")

    def __str__(self):
        return self.username

# 2. 睡眠记录模型
class SleepRecord(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sleep_records')
    sleep_time = models.DateTimeField(verbose_name="入睡时间")
    wakeup_time = models.DateTimeField(verbose_name="起床时间")
    duration = models.DurationField(verbose_name="睡眠时长", blank=True, null=True) # 自动计算

    def save(self, *args, **kwargs):
        self.duration = self.wakeup_time - self.sleep_time
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} 的睡眠记录 ({self.sleep_time.date()})"

# 3. 运动记录模型
class SportRecord(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sport_records')
    sport_type = models.CharField(max_length=100, verbose_name="运动类型")
    duration_minutes = models.PositiveIntegerField(verbose_name="运动时长(分钟)")
    calories_burned = models.FloatField(verbose_name="消耗卡路里(大卡)")
    record_date = models.DateField(default=timezone.now, verbose_name="记录日期")

    def __str__(self):
        return f"{self.user.username} 的运动记录 ({self.sport_type})"

# 4. 食物库模型 (供饮食记录参考)
class FoodItem(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="食物名称")
    calories_per_100g = models.FloatField(verbose_name="每100g卡路里(大卡)")
    
    def __str__(self):
        return self.name

# 5. 餐次模型
# 这个模型是“一餐”的容器，比如“2025-07-18的午餐”
class Meal(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='meals')
    meal_type = models.CharField(max_length=20, choices=[('breakfast', '早餐'), ('lunch', '午餐'), ('dinner', '晚餐'), ('snack', '加餐')], verbose_name="餐次类型")
    record_date = models.DateField(default=timezone.now, verbose_name="记录日期")

    # 使用 @property 装饰器，可以像访问字段一样方便地计算一餐的总热量
    @property
    def total_calories(self):
        # self.meal_items 是通过 MealItem 中的 related_name='meal_items' 反向关联过来的
        # 它会统计所有关联到这顿餐的食物条目的热量，并求和
        total = self.meal_items.aggregate(total=models.Sum('calories_calculated'))['total']
        return total or 0

    def __str__(self):
        # get_meal_type_display() 可以将 'lunch' 这样的标识符显示为 '午餐'
        return f"{self.user.username} 的 {self.get_meal_type_display()} ({self.record_date})"

# 6. 餐品模型
# 这个模型代表一餐中的具体食物，比如午餐中的“米饭”
class MealItem(models.Model):
    # 关联到具体的某一餐
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='meal_items') 
    # 从食物库中选择食物
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE, verbose_name="食物条目")
    # 用户输入这份食物的克数
    portion = models.FloatField(verbose_name="份量(克)")
    # 卡路里由系统自动计算，不允许用户填写，因此 blank=True
    calories_calculated = models.FloatField(verbose_name="计算卡路里(大卡)", blank=True, null=True)

    def save(self, *args, **kwargs):
        # 在保存之前，自动计算热量
        # 热量 = (每100克热量 / 100) * 实际克数
        self.calories_calculated = (self.food_item.calories_per_100g / 100) * self.portion
        super().save(*args, **kwargs) # 调用父类的save方法，将数据存入数据库

    def __str__(self):
        return f"{self.portion}克 {self.food_item.name}"
    
# 7. 用户健康目标模型
class UserHealthGoal(models.Model):
    """
    存储用户设定的每日健康目标。
    通过 OneToOneField 与 CustomUser 关联，确保每个用户只有一套目标。
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='health_goal', verbose_name="关联用户")
    
    # 睡眠目标 (小时)
    target_sleep_duration = models.FloatField(
        verbose_name="目标睡眠时长(小时)", 
        null=True, blank=True,
        help_text="例如: 7.5"
    )
    
    # 运动目标 (时长和热量)
    target_sport_duration_minutes = models.PositiveIntegerField(
        verbose_name="目标运动时长(分钟)",
        null=True, blank=True
    )
    target_sport_calories = models.PositiveIntegerField(
        verbose_name="目标运动消耗热量(大卡)",
        null=True, blank=True
    )

    # 饮食目标 (摄入热量)
    target_diet_calories = models.PositiveIntegerField(
        verbose_name="目标饮食摄入热量(大卡)",
        null=True, blank=True
    )

    def __str__(self):
        return f"{self.user.username}的健康目标"