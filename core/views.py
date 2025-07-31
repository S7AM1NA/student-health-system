import json
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt # 方便开发阶段调试API

from rest_framework import viewsets, permissions # 导入 permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .models import CustomUser, SleepRecord, SportRecord, FoodItem, Meal, MealItem
from .serializers import (
    SleepRecordSerializer, 
    SportRecordSerializer, 
    FoodItemSerializer, 
    MealSerializer, 
    MealItemSerializer,
    UserProfileSerializer
)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def index_view(request):
    """
    应用的统一入口。
    - 已登录 -> 跳转到看板
    - 未登录 -> 跳转到登录页
    """
    if request.user.is_authenticated:
        return redirect('dashboard') # 重定向到 name='dashboard' 的URL -> /dashboard/
    else:
        return redirect('login')     # 重定向到 name='login' 的URL -> /login/


def login_page_view(request):
    """
    渲染登录页面。如果用户已登录还尝试访问此页，则直接送回看板。
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    # 告诉Django去 'frontend' 文件夹里找 login.html
    return render(request, 'login.html') 


def register_page_view(request):
    """
    渲染注册页面。
    """
    # 告诉Django去 'frontend' 文件夹里找 register.html
    return render(request, 'register.html')

@login_required(login_url='/login/') # 关键保护！
def dashboard_page_view(request):
    """
    渲染主看板页面。
    @login_required 装饰器确保只有登录用户能访问。
    如果未登录的用户尝试直接访问 /dashboard/，会自动被重定向到 /login/。
    """
    # 告诉Django去 'frontend' 文件夹里找 dashboard.html
    return render(request, 'dashboard.html')

@csrf_exempt # 临时禁用CSRF保护，方便前端直接调用
def register_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        if not all([username, password, email]):
            return JsonResponse({'status': 'error', 'message': '所有字段都是必填的'}, status=400)

        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({'status': 'error', 'message': '用户名已存在'}, status=400)

        user = CustomUser.objects.create_user(username=username, password=password, email=email)
        return JsonResponse({'status': 'success', 'message': '用户注册成功'}, status=201)
    return JsonResponse({'status': 'error', 'message': '仅支持POST请求'}, status=405)

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({'status': 'success', 'message': '登录成功', 'user_id': user.id, 'username': user.username})
        else:
            return JsonResponse({'status': 'error', 'message': '用户名或密码错误'}, status=400)
    return JsonResponse({'status': 'error', 'message': '仅支持POST请求'}, status=405)

@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'status': 'success', 'message': '已成功注销'})
    return JsonResponse({'status': 'error', 'message': '仅支持POST请求'}, status=405)

class SleepRecordViewSet(viewsets.ModelViewSet):
    serializer_class = SleepRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = SleepRecord.objects.filter(user=self.request.user)
        
        # 【优化】支持按 record_date 查询参数进行筛选
        record_date_str = self.request.query_params.get('record_date')
        if record_date_str:
            # 对于睡眠记录，我们约定按“起床日期”进行筛选
            queryset = queryset.filter(wakeup_time__date=record_date_str)
            
        return queryset.order_by('-wakeup_time')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='today-check')
    def today_check(self, request):
        """
        【新增】轻量级接口，检查今天是否已有睡眠记录。
        访问URL: GET /api/sleep/today-check/
        """
        today = timezone.now().date()
        record = self.get_queryset().filter(wakeup_time__date=today).first()
        
        if record:
            return Response({"record_exists": True, "record_id": record.id})
        else:
            return Response({"record_exists": False, "record_id": None})

class SportRecordViewSet(viewsets.ModelViewSet):
    serializer_class = SportRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = SportRecord.objects.filter(user=self.request.user)
        
        # 【优化】支持按 record_date 查询参数进行筛选
        record_date_str = self.request.query_params.get('record_date')
        if record_date_str:
            queryset = queryset.filter(record_date=record_date_str)

        return queryset.order_by('-record_date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='today-check')
    def today_check(self, request):
        """
        【新增】轻量级接口，检查今天是否已有运动记录。
        访问URL: GET /api/sports/today-check/
        """
        today = timezone.now().date()
        # 运动记录可能有多条，我们只需要判断是否存在即可
        record = self.get_queryset().filter(record_date=today).first()
        
        if record:
            # 如果一天内有多条运动记录，返回第一条的ID供参考
            return Response({"record_exists": True, "record_id": record.id})
        else:
            return Response({"record_exists": False, "record_id": None})

class FoodItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    提供一个只读的食物库列表接口
    """
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer
    permission_classes = [permissions.IsAuthenticated] # 登录用户才能查看食物库


class MealViewSet(viewsets.ModelViewSet):
    serializer_class = MealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Meal.objects.filter(user=self.request.user).prefetch_related('meal_items__food_item')
        
        # 【优化】支持按 record_date 查询参数进行筛选
        record_date_str = self.request.query_params.get('record_date')
        if record_date_str:
            queryset = queryset.filter(record_date=record_date_str)
            
        return queryset.order_by('-record_date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='today-check')
    def today_check(self, request):
        """
        【新增】轻量级接口，检查今天是否已有任何餐次记录。
        访问URL: GET /api/meals/today-check/
        """
        today = timezone.now().date()
        record = self.get_queryset().filter(record_date=today).first()
        
        if record:
            # 如果一天内有多餐，返回第一餐的ID供参考
            return Response({"record_exists": True, "record_id": record.id})
        else:
            return Response({"record_exists": False, "record_id": None})


class MealItemViewSet(viewsets.ModelViewSet):
    """
    管理一餐中具体“餐品”的增删改查
    """
    serializer_class = MealItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 确保用户只能管理自己餐次下的餐品
        return MealItem.objects.filter(meal__user=self.request.user)

    # 注意：这里没有 perform_create，因为前端在创建 MealItem 时，
    # 会在POST请求的数据中明确指定它属于哪个 meal (meal_id)。

from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime, time
from django.db.models import Sum, Count
from django.utils import timezone

# ... 导入你所有的模型 ...
from .models import SleepRecord, SportRecord, Meal

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, date_str):
        try:
            # 1. 解析日期并获取当前用户
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            user = request.user
        except ValueError:
            return Response({'status': 'error', 'message': '日期格式错误，请使用YYYY-MM-DD'}, status=400)

        # 2. 初始化数据结构
        response_data = {
            "date": date_str,
            "sleep": {"record_exists": False},
            "sports": {"record_exists": False},
            "diet": {"record_exists": False},
        }
        
        # --- 数据聚合 ---
        
        # 3. 聚合睡眠数据
        # 假设睡眠记录是“跨天”的，我们找起床时间是目标日期的记录
        sleep_record = SleepRecord.objects.filter(
            user=user, 
            wakeup_time__date=target_date
        ).first()

        if sleep_record:
            duration_total_seconds = sleep_record.duration.total_seconds()
            response_data['sleep'] = {
                "duration_hours": round(duration_total_seconds / 3600, 1),
                "sleep_time": sleep_record.sleep_time.isoformat(),
                "wakeup_time": sleep_record.wakeup_time.isoformat(),
                "record_exists": True
            }

        # 4. 聚合运动数据
        sports_records = SportRecord.objects.filter(user=user, record_date=target_date)
        if sports_records.exists():
            sports_summary = sports_records.aggregate(
                total_calories_burned=Sum('calories_burned'),
                total_duration_minutes=Sum('duration_minutes'),
                count=Count('id')
            )
            response_data['sports'] = {
                "total_calories_burned": sports_summary.get('total_calories_burned') or 0,
                "total_duration_minutes": sports_summary.get('total_duration_minutes') or 0,
                "count": sports_summary.get('count') or 0,
                "record_exists": True
            }
            
        # 5. 聚合饮食数据
        meals = Meal.objects.filter(user=user, record_date=target_date)
        if meals.exists():
            total_calories_eaten = sum(meal.total_calories for meal in meals)
            response_data['diet'] = {
                "total_calories_eaten": total_calories_eaten,
                "record_exists": True
            }

        # --- 健康建议生成 (简化版BMR) ---
        # 简化版：假设基础代谢率 (BMR) 是一个固定值，比如 1500 大卡。
        # 真实项目中可以根据用户的性别、年龄、体重来计算。
        BMR = 1500 
        
        calories_in = response_data.get('diet', {}).get('total_calories_eaten', 0)
        calories_out = response_data.get('sports', {}).get('total_calories_burned', 0)
        sleep_hours = response_data.get('sleep', {}).get('duration_hours', 0)
        diet_record_exists = response_data.get('diet', {}).get('record_exists', False)
        
        status_code = "NEUTRAL"
        suggestion = "新的一天开始了，别忘了记录你的健康数据哦！"

        # 按优先级判断
        if calories_in > BMR * 1.2:
            status_code = "HIGH_INTAKE"
            suggestion = "今天摄入的热量有点多哦，注意控制饮食！"
        elif 0 < calories_in < BMR * 0.8:
            status_code = "LOW_INTAKE"
            suggestion = "热量摄入不足，身体需要能量来维持活力！"
        elif 0 < sleep_hours < 6.5:
            status_code = "POOR_SLEEP"
            suggestion = "睡眠是健康的基础，昨晚没睡好，今天要早点休息。"
        elif diet_record_exists and calories_out < 200:
            status_code = "LOW_ACTIVITY"
            suggestion = "生命在于运动，今天的运动量有点少哦！"
        elif abs(calories_in - (calories_out + BMR)) <= 300 and calories_in > 0:
            status_code = "BALANCED"
            suggestion = "今日热量摄入与消耗非常均衡，请继续保持！"

        # 如果所有记录都不存在，覆盖默认提示
        all_records_exist = any([
            response_data.get('sleep', {}).get('record_exists', False),
            response_data.get('sports', {}).get('record_exists', False),
            response_data.get('diet', {}).get('record_exists', False)
        ])

        if not all_records_exist:
            message = f"{date_str} 暂无健康数据记录"
        else:
            message = f"{date_str} 的健康数据获取成功"

        response_data['health_summary'] = {
            "suggestion": suggestion,
            "status_code": status_code
        }

        # 最终返回的完整数据
        final_response = {
            "status": "success",
            "message": message,
            "user": {
                "username": user.username,
                "user_id": user.id
            },
            "data": response_data
        }
        
        return Response(final_response)
    
class ProfileView(APIView):
    """
    处理用户个人档案的读取(GET)和更新(PUT)。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        处理 GET /api/profile/ 请求，返回当前用户档案。
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        """
        处理 PUT /api/profile/ 请求，更新当前用户档案。
        使用 partial=True 允许部分字段更新，类似PATCH。
        """
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)