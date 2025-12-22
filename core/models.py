from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

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
    name = models.CharField(max_length=100, verbose_name="食物名称")
    calories_per_100g = models.FloatField(verbose_name="每100g卡路里(大卡)")
    product_code = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="产品代码")

    # 营养素字段
    protein = models.FloatField(verbose_name="蛋白质(克)", null=True, blank=True)
    fat = models.FloatField(verbose_name="脂肪(克)", null=True, blank=True)
    carbohydrates = models.FloatField(verbose_name="碳水化合物(克)", null=True, blank=True)
    
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
    
# 8. 好友关系模型
class Friendship(models.Model):
    """
    管理用户间的好友关系，并包含双向授权。
    """
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, '待处理'),
        (STATUS_ACCEPTED, '已接受'),
        (STATUS_REJECTED, '已拒绝'),
    ]

    # from_user 是好友请求的发起者
    from_user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='friendship_requests_sent'
    )
    # to_user 是好友请求的接收者
    to_user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='friendship_requests_received'
    )
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name="关系状态")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    # --- 授权控制字段 ---
    # from_user_can_be_viewed: 标记 from_user (发起者) 是否授权 to_user (接收者) 查看自己的动态
    from_user_can_be_viewed = models.BooleanField(default=True, verbose_name="发起者动态可被查看")
    
    # to_user_can_be_viewed: 标记 to_user (接收者) 是否授权 from_user (发起者) 查看自己的动态
    to_user_can_be_viewed = models.BooleanField(default=True, verbose_name="接收者动态可被查看")

    class Meta:
        # 保证从A到B的好友请求是唯一的
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.get_status_display()})"

# 9. 通用评论模型
class Comment(models.Model):
    """
    一个通用的评论模型，可以附加到任何其他模型对象上。
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comments', verbose_name="评论作者")
    text = models.TextField(verbose_name="评论内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="评论时间")

    # --- 通用外键三要素 ---
    # 1. 关联到 ContentType，用于确定被评论的模型是哪一个（例如：SleepRecord 或 SportRecord）
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    # 2. 存储被评论记录的主键ID
    object_id = models.PositiveIntegerField()
    # 3. Django 通过这个虚拟字段，将上面两个字段组合成一个具体的模型实例
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user} 对 {self.content_type.model} (ID: {self.object_id}) 的评论"

# 10. 系统日志模型 (Member A)
class SystemLog(models.Model):
    """
    记录用户的关键操作日志，用于安全审计。
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='system_logs', verbose_name="操作用户", null=True, blank=True)
    action = models.CharField(max_length=255, verbose_name="操作行为")
    ip_address = models.GenericIPAddressField(verbose_name="IP地址", null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")
    details = models.TextField(verbose_name="详细信息", blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.user} - {self.action}"

# 11. 身体指标模型 (Member C -> Member A implemented)
class BodyMetric(models.Model):
    """
    记录用户的体重、身高、BMI。
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='body_metrics')
    weight = models.FloatField(verbose_name="体重(kg)")
    height = models.FloatField(verbose_name="身高(cm)")
    bmi = models.FloatField(verbose_name="BMI指数", blank=True, null=True)
    record_date = models.DateField(default=timezone.now, verbose_name="记录日期")

    def save(self, *args, **kwargs):
        # 自动计算 BMI
        if self.weight and self.height:
            # height 转为米
            height_m = self.height / 100
            self.bmi = round(self.weight / (height_m ** 2), 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.record_date} (BMI: {self.bmi})"

# 12. 文章分类模型 (Member C -> Member A implemented)
class ArticleCategory(models.Model):
    """
    健康文章的分类，如：睡眠知识、运动指导、饮食建议。
    """
    name = models.CharField(max_length=100, verbose_name="分类名称", unique=True)
    description = models.TextField(verbose_name="分类描述", blank=True, null=True)

    def __str__(self):
        return self.name

# 13. 健康文章模型 (Member C -> Member A implemented)
class HealthArticle(models.Model):
    """
    健康科普文章。
    """
    category = models.ForeignKey(ArticleCategory, on_delete=models.SET_NULL, null=True, related_name='articles', verbose_name="所属分类")
    title = models.CharField(max_length=200, verbose_name="文章标题")
    content = models.TextField(verbose_name="文章内容")
    author = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='authored_articles', verbose_name="作者")
    publish_date = models.DateTimeField(default=timezone.now, verbose_name="发布时间")
    views = models.PositiveIntegerField(default=0, verbose_name="阅读量")

    class Meta:
        ordering = ['-publish_date']

    def __str__(self):
        return self.title

# 14. 阅读历史模型 (Member C -> Member A implemented)
class UserReadHistory(models.Model):
    """
    记录用户阅读了哪些文章。
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='read_history')
    article = models.ForeignKey(HealthArticle, on_delete=models.CASCADE, related_name='read_records')
    read_time = models.DateTimeField(auto_now_add=True, verbose_name="阅读时间")

    class Meta:
        ordering = ['-read_time']

    def __str__(self):
        return f"{self.user.username} viewed {self.article.title}"
