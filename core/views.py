import json, requests, random
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt # 方便开发阶段调试API

from rest_framework import viewsets, permissions # 导入 permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .models import CustomUser, SleepRecord, SportRecord, FoodItem, Meal, MealItem, UserHealthGoal
from .serializers import (
    SleepRecordSerializer, 
    SportRecordSerializer, 
    FoodItemSerializer, 
    MealSerializer, 
    MealItemSerializer,
    UserProfileSerializer,
    UserHealthGoalSerializer
)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# ==========================================================
# 【新增】外部食物数据服务
# ==========================================================
class OpenFoodFactsService:
    """
    一个专门用于从 Open Food Facts API 获取数据并缓存到本地数据库的服务。
    """
    BASE_URL = "https://world.openfoodfacts.org/cgi/search.pl"
    
    def fetch_and_cache_foods(self, search_term, page_size=20):
        """
        根据搜索词从 API 获取食物数据，并将其存储或更新到本地 FoodItem 模型中。
        """
        params = {
            "search_terms": search_term,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": page_size,
            # 添加筛选条件，我们只关心有完整营养成分的食物
            "tagtype_0": "states",
            "tag_contains_0": "contains",
            "tag_0": "en:nutrition-facts-completed"
        }

        try:
            # 设置10秒超时，防止外部API响应过慢影响我们的服务
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status() # 如果请求失败 (例如 404, 500), 会抛出异常
            data = response.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            # 如果API出错，打印错误日志并安全退出，不影响后续逻辑
            print(f"从Open Food Facts获取'{search_term}'数据时出错: {e}")
            return

        products = data.get("products", [])
        
        for product in products:
            # 确保产品包含我们需要的所有核心数据
            code = product.get('code')
            name = product.get('product_name')
            # API以千焦(kj)和千卡(kcal)两种单位提供能量，我们使用kcal
            calories = product.get('nutriments', {}).get('energy-kcal_100g')

            if all([code, name, calories]):
                # 使用 update_or_create 方法来高效地处理缓存：
                # 它会根据 product_code 查找。如果找到，则更新记录；如果没找到，则创建新记录。
                # 这完美地避免了数据重复。
                FoodItem.objects.update_or_create(
                    product_code=code,
                    defaults={
                        'name': name,
                        'calories_per_100g': float(calories)
                    }
                )

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

@login_required(login_url='/login/')
def profile_page_view(request):
    return render(request, 'profile.html')

@login_required(login_url='/login/')
def sleep_page_view(request):
    """
    渲染睡眠记录页面
    """
    return render(request, 'sleep.html')

@login_required(login_url='/login/')
def sport_page_view(request):
    """
    渲染运动记录页面
    """
    return render(request, 'sport.html')

@login_required(login_url='/login/')
def diet_page_view(request):
    """
    渲染饮食记录页面
    """
    return render(request, 'diet.html')

@login_required(login_url='/login/')
def report_page_view(request):
    """
    渲染健康报告页面
    """
    return render(request, 'report.html')

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
        """
        
        现在此方法能够根据URL中的查询参数来过滤结果集：
        - 支持按 `record_date` 筛选, e.g., /api/meals/?record_date=2025-08-01
        - 支持按 `meal_type` 筛选, e.g., /api/meals/?meal_type=lunch
        - 支持两者组合筛选, e.g., /api/meals/?record_date=2025-08-01&meal_type=lunch
        """
        # 1. 基础查询集：获取当前登录用户的所有餐次
        queryset = Meal.objects.filter(user=self.request.user).prefetch_related('meal_items__food_item')
        
        # 2. 按 'record_date' 参数进行筛选
        #    我们从请求的查询参数中获取 'record_date' 的值
        record_date_str = self.request.query_params.get('record_date', None)
        if record_date_str:
            # 如果参数存在，就在现有查询集的基础上，追加一层过滤
            queryset = queryset.filter(record_date=record_date_str)

        # 3. 按 'meal_type' 参数进行筛选
        #    同样，我们获取 'meal_type' 的值
        meal_type_str = self.request.query_params.get('meal_type', None)
        if meal_type_str:
            # 如果参数存在，再追加一层过滤
            queryset = queryset.filter(meal_type=meal_type_str)
            
        # 4. 返回最终经过层层筛选后的结果集，并按日期降序排列
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
from datetime import datetime, time, timedelta
from django.db.models import Sum, Count, Avg, Min, Max
from django.utils import timezone
from collections import Counter

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

        # 2. 初始化数据结构 (保持不变)
        response_data = {
            "date": date_str,
            "sleep": {"record_exists": False, "duration_hours": 0},
            "sports": {"record_exists": False, "total_duration_minutes": 0, "total_calories_burned": 0},
            "diet": {"record_exists": False, "total_calories_eaten": 0},
        }
        
        # --- 3, 4, 5. 数据聚合 (逻辑微调，确保即使没记录也有默认值) ---
        # 睡眠
        sleep_record = SleepRecord.objects.filter(user=user, wakeup_time__date=target_date).first()
        if sleep_record:
            response_data['sleep'] = {
                "duration_hours": round(sleep_record.duration.total_seconds() / 3600, 1),
                "sleep_time": sleep_record.sleep_time.isoformat(), "wakeup_time": sleep_record.wakeup_time.isoformat(),
                "record_exists": True
            }

        # 运动
        sports_records = SportRecord.objects.filter(user=user, record_date=target_date)
        if sports_records.exists():
            sports_summary = sports_records.aggregate(
                total_calories_burned=Sum('calories_burned'), total_duration_minutes=Sum('duration_minutes'), count=Count('id')
            )
            response_data['sports'] = {
                "total_calories_burned": sports_summary.get('total_calories_burned') or 0,
                "total_duration_minutes": sports_summary.get('total_duration_minutes') or 0,
                "count": sports_summary.get('count') or 0, "record_exists": True
            }
            
        # 饮食
        meals = Meal.objects.filter(user=user, record_date=target_date)
        if meals.exists():
            response_data['diet'] = {
                "total_calories_eaten": sum(meal.total_calories for meal in meals),
                "record_exists": True
            }

        # --- 6. 【新增】获取健康目标并计算完成度 ---
        goal, _ = UserHealthGoal.objects.get_or_create(user=user)
        
        def calculate_progress(actual, target):
            if target and target > 0:
                # 返回完成百分比，最高不超过100%，方便前端直接用作进度条
                return min(round((actual / target) * 100), 100)
            return 0 # 如果没有设置目标，则进度为0

        response_data['goals'] = {
            "target_sleep_duration": goal.target_sleep_duration,
            "progress_sleep_duration": calculate_progress(response_data['sleep']['duration_hours'], goal.target_sleep_duration),
            
            "target_sport_duration_minutes": goal.target_sport_duration_minutes,
            "progress_sport_duration": calculate_progress(response_data['sports']['total_duration_minutes'], goal.target_sport_duration_minutes),

            "target_sport_calories": goal.target_sport_calories,
            "progress_sport_calories": calculate_progress(response_data['sports']['total_calories_burned'], goal.target_sport_calories),

            "target_diet_calories": goal.target_diet_calories,
            # 对于饮食，我们不封顶，以便用户看到是否超标
            "progress_diet_calories": round((response_data['diet']['total_calories_eaten'] / goal.target_diet_calories) * 100) if goal.target_diet_calories else 0,
        }

        # --- 健康建议生成  ---
        BMR = 1800 if self.request.user.gender == 'M' else 1500
        
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

class UserHealthGoalView(APIView):
    """
    处理用户个人健康目标的读取(GET)和创建/更新(PUT)。
    访问URL: /api/goals/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        处理 GET /api/goals/ 请求。
        返回当前用户的健康目标，如果不存在则自动创建一个空的目标对象。
        """
        # get_or_create 是一个非常方便的方法，它能确保每个用户都有一个目标对象
        goal, created = UserHealthGoal.objects.get_or_create(user=request.user)
        serializer = UserHealthGoalSerializer(goal)
        return Response(serializer.data)

    def put(self, request):
        """
        处理 PUT /api/goals/ 请求。
        用请求中的数据更新当前用户的健康目标。
        """
        goal, created = UserHealthGoal.objects.get_or_create(user=request.user)
        # 使用 partial=True 允许部分更新，用户可以只修改一个目标，而不必提交所有字段
        serializer = UserHealthGoalSerializer(goal, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class WeeklySleepReportView(APIView):
    """
    提供一周睡眠数据的 API。
    用于前端可视化图表。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, end_date_str):
        """
        处理 GET /api/reports/weekly-sleep/<end_date_str>/ 请求。
        返回从 end_date_str 往前推7天的数据。
        """
        try:
            end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'status': 'error', 'message': '日期格式错误，请使用 YYYY-MM-DD'}, status=400)

        start_date_obj = end_date_obj - timedelta(days=6)
        user = request.user

        # 范围开始于 start_date_obj 的 00:00:00
        start_datetime = timezone.make_aware(datetime.combine(start_date_obj, time.min))
        # 范围结束于 end_date_obj 的 23:59:59...
        end_datetime = timezone.make_aware(datetime.combine(end_date_obj, time.max))

        # 使用 __range 进行查询，这是最可靠的方式
        sleep_records = SleepRecord.objects.filter(
            user=user,
            wakeup_time__range=[start_datetime, end_datetime]
        )

        # 将查询结果处理成以日期为键的字典
        # 注意：要从 record.wakeup_time 中获取本地时区的日期
        sleep_data_map = {
            timezone.localtime(record.wakeup_time).date().isoformat(): round(record.duration.total_seconds() / 3600, 1)
            for record in sleep_records
        }

        # 构建最终的7天数据列表
        report_data = []
        for i in range(7):
            current_date = start_date_obj + timedelta(days=i)
            date_str = current_date.isoformat()
            duration = sleep_data_map.get(date_str, 0)
            report_data.append({
                "date": date_str,
                "duration_hours": duration
            })

        return Response({
            "status": "success",
            "message": f"获取 {start_date_obj} 到 {end_date_obj} 的睡眠数据成功",
            "data": report_data
        })

class HealthReportView(APIView):
    """
    生成指定时间周期内的综合、详细的健康报告。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        处理 GET /api/reports/health-summary/?start_date=...&end_date=... 请求。
        """
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if not start_date_str or not end_date_str:
            return Response({'status': 'error', 'message': '必须提供 start_date 和 end_date 查询参数'}, status=400)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'status': 'error', 'message': '日期格式错误，请使用 YYYY-MM-DD'}, status=400)
            
        if start_date > end_date:
            return Response({'status': 'error', 'message': '开始日期不能晚于结束日期'}, status=400)

        user = request.user
        num_days = (end_date - start_date).days + 1

        sleep_records = SleepRecord.objects.filter(user=user, wakeup_time__date__range=[start_date, end_date])
        sport_records = SportRecord.objects.filter(user=user, record_date__range=[start_date, end_date])
        meals = Meal.objects.filter(user=user, record_date__range=[start_date, end_date]).prefetch_related('meal_items')

        sleep_analysis = self.analyze_sleep(sleep_records, num_days)
        sports_analysis = self.analyze_sports(sport_records, num_days)
        diet_analysis = self.analyze_diet(meals, num_days)

        overall_summary = self.generate_overall_summary(
            sleep_analysis, sports_analysis, diet_analysis, user, start_date, end_date
        )

        final_report = {
            "status": "success",
            "report": {
                "period": {
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "total_days": num_days
                },
                "overall_summary": overall_summary,
                "sleep_analysis": sleep_analysis,
                "sports_analysis": sports_analysis,
                "diet_analysis": diet_analysis,
            }
        }
        return Response(final_report)

    # analyze_sleep, analyze_sports, analyze_diet 方法保持不变...
    def analyze_sleep(self, records, num_days):
        analysis = {
            "score": 0, "suggestions": [], "record_count": 0, "average_duration_hours": 0,
            "consistency": {"comment": "数据不足"}, "extremes": {}, "data_coverage_percent": 0
        }
        record_count = records.count()
        analysis["record_count"] = record_count
        if record_count == 0:
            analysis["suggestions"].append("您在此期间没有记录任何睡眠数据。规律睡眠是健康基石。")
            return analysis

        unique_dates_count = records.values('wakeup_time__date').distinct().count()
        # 2. 用不重复的日期数来计算覆盖率
        analysis["data_coverage_percent"] = round((unique_dates_count / num_days) * 100) if num_days > 0 else 0
        summary = records.aggregate(
            avg_duration=Avg('duration'),
            min_duration=Min('duration'),
            max_duration=Max('duration')
        )
        avg_hours = summary['avg_duration'].total_seconds() / 3600 if summary['avg_duration'] else 0
        analysis["average_duration_hours"] = round(avg_hours, 1)
        analysis["extremes"] = {
            "shortest_sleep_hours": round(summary['min_duration'].total_seconds() / 3600, 1) if summary['min_duration'] else 0,
            "longest_sleep_hours": round(summary['max_duration'].total_seconds() / 3600, 1) if summary['max_duration'] else 0,
        }
        if record_count > 1:
            sleep_times_minutes = [(r.sleep_time.hour * 60 + r.sleep_time.minute) for r in records]
            wakeup_times_minutes = [(r.wakeup_time.hour * 60 + r.wakeup_time.minute) for r in records]
            sleep_std_dev = self._calculate_std_dev(sleep_times_minutes)
            wakeup_std_dev = self._calculate_std_dev(wakeup_times_minutes)
            analysis["consistency"] = {
                "sleep_time_std_dev_minutes": round(sleep_std_dev),
                "wakeup_time_std_dev_minutes": round(wakeup_std_dev),
                "comment": "作息非常规律" if sleep_std_dev < 30 and wakeup_std_dev < 30 else "作息规律性一般" if sleep_std_dev < 60 and wakeup_std_dev < 60 else "作息不太规律，波动较大"
            }
        score = 0
        if 7 <= avg_hours <= 9: score += 60; analysis["suggestions"].append(f"平均睡眠时长 {analysis['average_duration_hours']} 小时，非常理想！")
        else: score += 30; analysis["suggestions"].append(f"平均睡眠时长 {analysis['average_duration_hours']} 小时，建议调整至7-9小时。")
        if analysis["consistency"].get("sleep_time_std_dev_minutes", 100) < 45: score += 40
        else: score += 15; analysis["suggestions"].append("您的入睡和起床时间波动较大，尝试建立更固定的作息时间表。")
        analysis["score"] = min(100, score)
        return analysis

    def analyze_sports(self, records, num_days):
        analysis = {"score": 0, "suggestions": [], "record_count": 0, "total_duration_minutes": 0, "total_calories_burned": 0,
                    "frequency_per_week": 0, "most_frequent_activity": "无", "data_coverage_percent": 0}
        record_count = records.count()
        analysis["record_count"] = record_count
        if record_count == 0: analysis["suggestions"].append("您在此期间没有运动记录。适度运动有益身心。"); return analysis
        summary = records.aggregate(total_duration=Sum('duration_minutes'), total_calories=Sum('calories_burned'))
        analysis["total_duration_minutes"] = summary['total_duration'] or 0
        analysis["total_calories_burned"] = round(summary['total_calories'] or 0)
        analysis["frequency_per_week"] = round((record_count / num_days) * 7, 1)
        sport_types = [r.sport_type for r in records]
        analysis["most_frequent_activity"] = Counter(sport_types).most_common(1)[0][0] if sport_types else "无"
        unique_dates = records.values_list('record_date', flat=True).distinct().count()
        analysis["data_coverage_percent"] = round((unique_dates / num_days) * 100)
        score = 0
        weekly_minutes = (analysis["total_duration_minutes"] / num_days) * 7
        if weekly_minutes >= 150: score += 60; analysis["suggestions"].append(f"每周平均运动时长约 {int(weekly_minutes)} 分钟，达到了推荐标准，非常棒！")
        elif weekly_minutes >= 75: score += 40; analysis["suggestions"].append(f"每周平均运动时长约 {int(weekly_minutes)} 分钟，有规律的运动习惯，请继续保持。")
        else: score += 20; analysis["suggestions"].append(f"每周平均运动时长约 {int(weekly_minutes)} 分钟，运动量稍显不足，建议增加运动频率或时长。")
        if analysis["frequency_per_week"] >= 3: score += 40
        elif analysis["frequency_per_week"] >= 1: score += 20
        analysis["score"] = min(100, score)
        return analysis

    def analyze_diet(self, records, num_days):
        analysis = {"score": 0, "suggestions": [], "average_daily_calories": 0, "calorie_distribution": {}, "data_coverage_percent": 0}
        if not records.exists():
            analysis["suggestions"].append("您在此期间没有饮食记录。记录饮食是管理健康的第一步。")
            return analysis
            
        total_calories = sum(meal.total_calories for meal in records)
        analysis["average_daily_calories"] = round(total_calories / num_days)

        unique_dates = records.values_list('record_date', flat=True).distinct().count()
        analysis["data_coverage_percent"] = round((unique_dates / num_days) * 100)
        
        dist = {'breakfast': 0, 'lunch': 0, 'dinner': 0, 'snack': 0}
        for meal in records:
            dist[meal.meal_type] += meal.total_calories
        analysis["calorie_distribution"] = {k: round(v) for k, v in dist.items()}

        BMR = 1800 if self.request.user.gender == 'M' else 1500
        avg_calories = analysis["average_daily_calories"]
        
        # 1. 热量摄入评分 (满分60)
        calorie_score = 0
        # 从最严格的“理想”范围开始判断
        if BMR * 0.9 <= avg_calories <= BMR * 1.3:
            calorie_score = 60
            analysis["suggestions"].append(f"日均热量摄入 {avg_calories} 大卡，控制得非常理想。")
        # 然后是较宽的“可接受”范围
        elif BMR * 0.7 <= avg_calories < BMR * 1.5:
            calorie_score = 30
            if avg_calories >= BMR * 1.3:
                analysis["suggestions"].append(f"日均热量摄入 {avg_calories} 大卡，略微偏高，请注意。")
            else: # avg_calories < BMR * 0.9
                analysis["suggestions"].append(f"日均热量摄入 {avg_calories} 大卡，略微偏低，请确保能量充足。")
        # 最后是“不佳”范围
        else:
            calorie_score = 0
            if avg_calories > BMR * 1.5:
                 analysis["suggestions"].append(f"日均热量摄入 {avg_calories} 大卡，严重偏高，请立即调整饮食！")
            elif avg_calories > 0:
                 analysis["suggestions"].append(f"日均热量摄入 {avg_calories} 大卡，严重偏低，身体可能处于能量匮乏状态！")

        # 2. 饮食结构评分 (满分40)
        structure_score = 0
        total_dist_cal = sum(dist.values())
        if total_dist_cal > 0:
            breakfast_ratio = dist['breakfast'] / total_dist_cal
            dinner_ratio = dist['dinner'] / total_dist_cal
            
            if breakfast_ratio >= 0.2:
                structure_score += 20
            else:
                analysis["suggestions"].append("早餐摄入热量偏少，一顿营养丰富的早餐能开启活力满满的一天。")

            if dinner_ratio <= 0.4:
                structure_score += 20
            else:
                analysis["suggestions"].append("晚餐热量占比较高，建议将更多热量分配到早餐和午餐。")
        
        # 3. 总分
        analysis["score"] = min(100, calorie_score + structure_score)
        return analysis

    def generate_overall_summary(self, sleep, sports, diet, user, start_date, end_date):
        BMR = 1800 if user.gender == 'M' else 1500
        avg_intake = diet['average_daily_calories']
        
        num_days_in_period = (end_date - start_date).days + 1
        avg_activity_burn = (sports['total_calories_burned'] / num_days_in_period) if sports['total_calories_burned'] > 0 and num_days_in_period > 0 else 0

        net_calories = avg_intake - avg_activity_burn - BMR
        overall_score = round(sleep['score'] * 0.4 + diet['score'] * 0.3 + sports['score'] * 0.3)
        
        title = "健康状况评估"
        if overall_score >= 85: title = "优秀！健康生活方式的典范"
        elif overall_score >= 70: title = "良好，继续保持！"
        elif overall_score >= 50: title = "基本均衡，但有提升空间"
        else: title = "需重点关注，健康警报"

        scores = {'睡眠': sleep['score'], '饮食': diet['score'], '运动': sports['score']}
        lowest_area = min(scores, key=scores.get)
        priority_suggestions = [f"本周期您需要在“{lowest_area}”方面投入更多关注。"]
        if lowest_area == '睡眠': priority_suggestions.extend(sleep['suggestions'])
        elif lowest_area == '饮食': priority_suggestions.extend(diet['suggestions'])
        else: priority_suggestions.extend(sports['suggestions'])
            
        return {
            "title": title,
            "overall_score": overall_score,
            "calorie_balance": {
                "average_intake": avg_intake,
                "average_activity_burn": round(avg_activity_burn),
                "estimated_bmr": BMR,
                "net_calories": round(net_calories),
                "comment": "热量基本平衡" if abs(net_calories) < 200 else "热量盈余，可能导致体重增加" if net_calories > 0 else "热量亏损，可能导致体重下降"
            },
            "priority_suggestions": priority_suggestions
        }
        
    def _calculate_std_dev(self, data):
        n = len(data)
        if n < 2: return 0
        mean = sum(data) / n
        variance = sum([(x - mean) ** 2 for x in data]) / (n-1)
        return variance ** 0.5
    
class HealthAlertView(APIView):
    """
    提供健康异常预警功能。
    检查用户近期是否存在连续多天数据不佳的情况。
    """
    permission_classes = [IsAuthenticated]

    # --- 可配置的预警阈值 ---
    # 连续多少天不达标就触发预警
    CONSECUTIVE_DAYS_THRESHOLD = 3 
    # 睡眠不足的小时数阈值
    INSUFFICIENT_SLEEP_THRESHOLD_HOURS = 7.0
    # 运动量过低的卡路里阈值
    LOW_ACTIVITY_CALORIES_THRESHOLD = 100 
    # 我们检查过去多少天的数据
    DAYS_TO_CHECK = 5 

    def get(self, request):
        """
        处理 GET /api/alerts/check/ 请求。
        返回一个包含所有当前触发的预警信息的列表。
        """
        user = request.user
        today = timezone.now().date()
        start_date = today - timedelta(days=self.DAYS_TO_CHECK - 1)
        
        alerts = []

        # 1. 检查睡眠不足预警
        sleep_records = SleepRecord.objects.filter(
            user=user, 
            wakeup_time__date__range=[start_date, today]
        )
        # 将记录按日期分组，方便查找
        sleep_by_date = {
            timezone.localtime(r.wakeup_time).date(): r.duration.total_seconds() / 3600
            for r in sleep_records
        }

        consecutive_poor_sleep_days = 0
        for i in range(self.DAYS_TO_CHECK):
            check_date = today - timedelta(days=i)
            # 如果某天有记录且睡眠时间少于阈值
            if check_date in sleep_by_date and sleep_by_date[check_date] < self.INSUFFICIENT_SLEEP_THRESHOLD_HOURS:
                consecutive_poor_sleep_days += 1
            else:
                # 一旦不满足条件，连续天数就中断，重置计数器
                consecutive_poor_sleep_days = 0 
            
            # 如果达到连续天数阈值，添加预警并停止检查
            if consecutive_poor_sleep_days >= self.CONSECUTIVE_DAYS_THRESHOLD:
                alerts.append({
                    "alert_code": "POOR_SLEEP_STREAK",
                    "message": f"您已连续{self.CONSECUTIVE_DAYS_THRESHOLD}天睡眠不足{self.INSUFFICIENT_SLEEP_THRESHOLD_HOURS}小时，请注意保证充足的休息。"
                })
                break

        # 2. 检查运动量过低预警
        sport_records = SportRecord.objects.filter(
            user=user, 
            record_date__range=[start_date, today]
        )
        # 按天聚合消耗的卡路里
        calories_by_date = {}
        for r in sport_records:
            calories_by_date[r.record_date] = calories_by_date.get(r.record_date, 0) + r.calories_burned

        consecutive_low_activity_days = 0
        for i in range(self.DAYS_TO_CHECK):
            check_date = today - timedelta(days=i)
            # 如果某天记录的总卡路里低于阈值（包括没有记录的情况，视为0）
            if calories_by_date.get(check_date, 0) < self.LOW_ACTIVITY_CALORIES_THRESHOLD:
                consecutive_low_activity_days += 1
            else:
                consecutive_low_activity_days = 0
            
            if consecutive_low_activity_days >= self.CONSECUTIVE_DAYS_THRESHOLD:
                alerts.append({
                    "alert_code": "LOW_ACTIVITY_STREAK",
                    "message": f"您已连续{self.CONSECUTIVE_DAYS_THRESHOLD}天运动量过低，建议增加适度锻炼来保持活力。"
                })
                break
        
        return Response(alerts)
    
# 智能饮食推荐视图
class DietRecommendationView(APIView):
    """
    V4.0: 模拟大厨配餐逻辑，不仅考虑营养，更注重荤素搭配和套餐的合理性。
    """
    permission_classes = [IsAuthenticated]

    # ... (宏量营养素配比和常量定义与V3.0相同) ...
    DEFAULT_MACRO_RATIOS = {'carbs': 0.50, 'protein': 0.25, 'fat': 0.25}
    STRENGTH_MACRO_RATIOS = {'carbs': 0.40, 'protein': 0.40, 'fat': 0.20}
    ENDURANCE_MACRO_RATIOS = {'carbs': 0.55, 'protein': 0.25, 'fat': 0.20}
    MIXED_MACRO_RATIOS = {'carbs': 0.45, 'protein': 0.35, 'fat': 0.20}
    CALORIES_PER_GRAM = {'carbs': 4, 'protein': 4, 'fat': 9}
    MEAL_CALORIE_RATIOS = {'breakfast': 0.30, 'lunch': 0.40, 'dinner': 0.30, 'snack': 0.15}
    CALORIE_TOLERANCE = 0.1

    def get(self, request):
        # ... (此部分代码与V3.0相同，用于计算 target_meal_calories) ...
        user = request.user
        date_str = request.query_params.get('date')
        meal_type = request.query_params.get('meal_type')
        if not date_str or not meal_type or meal_type not in self.MEAL_CALORIE_RATIOS:
            return Response({'status': 'error', 'message': '必须提供有效的 date 和 meal_type'}, status=400)
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'status': 'error', 'message': '日期格式错误'}, status=400)

        bmr = 1800 if user.gender == 'M' else 1500
        sports_today = SportRecord.objects.filter(user=user, record_date=target_date)
        calories_burned_today = sports_today.aggregate(total=Sum('calories_burned'))['total'] or 0
        dynamic_target_calories = bmr + calories_burned_today

        meals_today = Meal.objects.filter(user=user, record_date=target_date)
        calories_eaten_today = sum(meal.total_calories for meal in meals_today)
        remaining_calories = dynamic_target_calories - calories_eaten_today
        
        if remaining_calories <= 100:
             return Response({"status": "info", "message": "今日热量已基本达标", "recommendations": []})
        
        target_meal_calories = remaining_calories * self.MEAL_CALORIE_RATIOS[meal_type]

        # 【核心算法升级】
        latest_sport = sports_today.order_by('-id').first()
        macro_ratios = self._get_dynamic_macro_ratios(latest_sport)
        
        # 1. 计算本餐的宏量营养素目标（单位：克）
        target_protein = (target_meal_calories * macro_ratios['protein']) / self.CALORIES_PER_GRAM['protein']
        target_carbs = (target_meal_calories * macro_ratios['carbs']) / self.CALORIES_PER_GRAM['carbs']
        target_fat = (target_meal_calories * macro_ratios['fat']) / self.CALORIES_PER_GRAM['fat']
        
        # 2. 食物分类
        food_categories = self._categorize_foods()
        if not food_categories['protein_sources'] or not food_categories['carb_sources']:
             return Response({'status': 'error', 'message': '食物库中缺少必要的主食或蛋白质来源'}, status=500)

        # 3. 生成并评分候选套餐
        candidates = []
        for _ in range(50):
            # 传递更具体的目标给构建器
            combo = self._build_one_combo_v4(food_categories, target_protein, target_carbs, target_fat)
            if combo:
                score = self._score_combo(combo, target_meal_calories, macro_ratios)
                candidates.append((score, combo))

        if not candidates:
            return Response({'status': 'error', 'message': '无法生成合适的饮食推荐'}, status=500)

        # 4. 排序并返回最优结果
        candidates.sort(key=lambda x: x[0], reverse=True)
        top_3_recommendations = [combo for score, combo in candidates[:3]]
        
        # ... (返回Response的代码与V3.0相同) ...
        return Response({
            "status": "success",
            "message": f"根据您今天的运动情况，为您生成了{meal_type}的营养推荐",
            "recommendation_context": {
                "dynamic_target_calories": round(dynamic_target_calories),
                "bmr_estimated": bmr,
                "calories_burned_from_sport": round(calories_burned_today),
                "calories_eaten_today": round(calories_eaten_today),
                "target_meal_calories": round(target_meal_calories),
                "target_macros_grams": {"protein": round(target_protein), "carbs": round(target_carbs), "fat": round(target_fat)},
                "used_macro_ratios": macro_ratios,
            },
            "recommendations": top_3_recommendations
        })

    def _categorize_foods(self):
        """【升级】更精细的食物分类"""
        categories = {
            'protein_sources': [], 'carb_sources': [], 'fat_sources': [],
            'vegetables': [], 'fruits': []
        }
        all_foods = FoodItem.objects.filter(calories_per_100g__gt=0).exclude(protein__isnull=True).exclude(fat__isnull=True).exclude(carbohydrates__isnull=True)
        
        for food in all_foods:
            p, c, f = food.protein, food.carbohydrates, food.fat
            total = p + c + f
            if total == 0: continue

            # 定义分类逻辑
            # 水果类（基于名称和中等碳水）
            if any(keyword in food.name for keyword in ['果', '莓', '蕉', '瓜', '梨', '桃', '李', '杏', '枣', '橘', '橙', '柚', '提', '葡', '芒']):
                if c / total > 0.4 and food.calories_per_100g < 100:
                    categories['fruits'].append(food)
                    continue
            # 主要蛋白质来源 (肉、蛋、豆制品)
            if p / total > 0.35 and c / total < 0.4:
                categories['protein_sources'].append(food)
            # 主要碳水来源 (主食、根茎类)
            elif c / total > 0.5:
                categories['carb_sources'].append(food)
            # 主要脂肪来源 (坚果、油)
            elif f / total > 0.5:
                categories['fat_sources'].append(food)
            # 蔬菜类 (低卡)
            elif food.calories_per_100g < 60:
                categories['vegetables'].append(food)
        return categories

    def _build_one_combo_v4(self, categories, target_p, target_c, target_f):
        """【V4核心算法】模拟大厨配餐，注重荤素搭配"""
        combo_items = []
        
        # --- 1. 定主菜 (蛋白质) ---
        protein_food = random.choice(categories['protein_sources'])
        # 目标是满足蛋白质需求的 70% ~ 100%
        protein_needed = target_p * random.uniform(0.7, 1.0)
        # 计算所需份量 (克)
        protein_portion = (protein_needed / protein_food.protein) * 100 if protein_food.protein > 0 else 0
        if protein_portion > 0:
            combo_items.append({'food': protein_food, 'portion': round(protein_portion / 10) * 10})

        # --- 2. 配主食 (碳水) ---
        carb_food = random.choice(categories['carb_sources'])
        carb_needed = target_c * random.uniform(0.8, 1.0)
        carb_portion = (carb_needed / carb_food.carbohydrates) * 100 if carb_food.carbohydrates > 0 else 0
        if carb_portion > 0:
            combo_items.append({'food': carb_food, 'portion': round(carb_portion / 10) * 10})

        # --- 3. 加蔬菜 (保证份量) ---
        if categories['vegetables']:
            # 随机选择1到2种蔬菜
            num_veg = random.randint(1, 2)
            selected_veg = random.sample(categories['vegetables'], min(num_veg, len(categories['vegetables'])))
            for veg in selected_veg:
                # 蔬菜份量固定在100-200g，保证“看得到”
                veg_portion = random.choice([100, 150, 200])
                combo_items.append({'food': veg, 'portion': veg_portion})

        # --- 4. (可选) 补充脂肪或水果 ---
        # 计算当前已有的宏量
        current_macros = self._format_combo(combo_items)['total_macros']
        fat_gap = target_f - current_macros['fat']

        # 如果脂肪不足，且有脂肪源，且有50%几率
        if fat_gap > 3 and categories['fat_sources'] and random.random() < 0.5:
            fat_food = random.choice(categories['fat_sources'])
            fat_portion = (fat_gap / fat_food.fat) * 100 if fat_food.fat > 0 else 0
            if fat_portion > 5: # 至少需要5g以上
                combo_items.append({'food': fat_food, 'portion': round(fat_portion / 5) * 5})
        # 或者，有25%几率加个水果
        elif categories['fruits'] and random.random() < 0.25:
             fruit_food = random.choice(categories['fruits'])
             fruit_portion = random.choice([80, 100, 120, 150])
             combo_items.append({'food': fruit_food, 'portion': fruit_portion})

        return self._format_combo(combo_items)

    # _get_dynamic_macro_ratios, _score_combo, _format_combo 方法与V3.0版本相同，无需修改
    # (此处为完整性再次提供)
    def _get_dynamic_macro_ratios(self, sport_record):
        if not sport_record:
            return self.DEFAULT_MACRO_RATIOS
        sport_type = sport_record.sport_type.lower()
        strength_keywords = ['力量', '举重', '器械', '卧推', '深蹲', '硬拉', '推举', '弯举', '划船', '引体向上', '俯卧撑', '哑铃', '杠铃', '抗阻', '增肌', '塑形']
        endurance_keywords = ['跑', '游泳', '单车', '自行车', '椭圆机', '有氧', '操', '跳绳', '登山', '快走', '慢跑', '长跑', '马拉松', '划船机', '动感单车']
        mixed_keywords = ['hiit', 'crossfit', '交叉训练', '循环训练', '球类', '篮球', '足球', '羽毛球', '网球', '拳击', '搏击', '武术', '舞蹈']
        if any(keyword in sport_type for keyword in strength_keywords): return self.STRENGTH_MACRO_RATIOS
        if any(keyword in sport_type for keyword in mixed_keywords): return self.MIXED_MACRO_RATIOS
        if any(keyword in sport_type for keyword in endurance_keywords): return self.ENDURANCE_MACRO_RATIOS
        return self.DEFAULT_MACRO_RATIOS

    def _score_combo(self, combo, target_calories, macro_ratios):
        calories_diff = abs(combo['total_calories'] - target_calories)
        calorie_score = max(0, 1 - (calories_diff / target_calories))
        total_p = combo['total_macros']['protein']
        total_c = combo['total_macros']['carbs']
        total_f = combo['total_macros']['fat']
        cals_from_macros = (total_p * 4) + (total_c * 4) + (total_f * 9)
        if cals_from_macros == 0: return 0
        ratio_p, ratio_c, ratio_f = (total_p * 4) / cals_from_macros, (total_c * 4) / cals_from_macros, (total_f * 9) / cals_from_macros
        protein_err, carbs_err, fat_err = abs(ratio_p - macro_ratios['protein']), abs(ratio_c - macro_ratios['carbs']), abs(ratio_f - macro_ratios['fat'])
        macro_score = max(0, 1 - (protein_err + carbs_err + fat_err) / 2)
        return calorie_score * 0.6 + macro_score * 0.4

    def _format_combo(self, items):
        total_calories, total_protein, total_fat, total_carbs = 0, 0, 0, 0
        formatted_items = []
        for item in items:
            food, portion = item['food'], item['portion']
            factor = portion / 100.0
            item_calories, item_protein, item_fat, item_carbs = round(food.calories_per_100g * factor), round(food.protein * factor, 1), round(food.fat * factor, 1), round(food.carbohydrates * factor, 1)
            total_calories, total_protein, total_fat, total_carbs = total_calories + item_calories, total_protein + item_protein, total_fat + item_fat, total_carbs + item_carbs
            formatted_items.append({"food_id": food.id, "name": food.name, "portion_g": portion, "calories": item_calories, "macros": {"protein": item_protein, "fat": item_fat, "carbs": item_carbs,}})
        return {"title": "智能营养套餐", "total_calories": total_calories, "total_macros": {"protein": round(total_protein, 1), "fat": round(total_fat, 1), "carbs": round(total_carbs, 1),}, "items": formatted_items}
