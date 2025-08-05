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