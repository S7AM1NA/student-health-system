from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    index_view,
    login_page_view,
    register_page_view,
    dashboard_page_view,
    sleep_page_view,
    sport_page_view,
    diet_page_view,
    profile_page_view,
    report_page_view,
    friends_page_view,
    body_metrics_page_view,  # 新增 (Member B)
    articles_page_view,       # 新增 (Member B)
    data_management_view,     # 新增 (Member B)
    register_view,
    login_view, 
    logout_view,
    DashboardView,
    SleepRecordViewSet, 
    SportRecordViewSet, 
    FoodItemViewSet, 
    MealViewSet, 
    MealItemViewSet,
    ProfileView,
    UserHealthGoalView,
    WeeklySleepReportView,
    HealthReportView,
    HealthAlertView,
    DietRecommendationView,
    FriendshipViewSet,
    HealthFeedView,
    CommentViewSet,
    # 新增 ViewSets (Member A)
    BodyMetricViewSet,
    ArticleCategoryViewSet,
    HealthArticleViewSet,
    UserReadHistoryViewSet,
    SystemLogViewSet,
    # 新增 Views (Member C)
    DataExportView,
    FoodImportView,
)

from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

# 数据导出视图 - 使用纯 Django 函数视图实现
@login_required
def data_export_view(request):
    """
    数据导出 API (纯 Django 视图)
    支持 Excel/CSV/JSON 格式导出用户健康数据
    
    GET /data-export/?format=excel&start_date=2024-01-01&end_date=2024-01-31
    """
    from datetime import datetime, timedelta
    from django.utils import timezone
    from .data_io import ExcelExporter, CSVExporter, export_user_data_json
    
    export_format = request.GET.get('format', 'excel').lower()
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    # 解析日期
    try:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else timezone.now().date()
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else end_date - timedelta(days=30)
    except ValueError:
        return HttpResponse('日期格式错误，请使用 YYYY-MM-DD', status=400)
    
    user = request.user
    
    try:
        if export_format == 'excel':
            return ExcelExporter.export_user_health_data(user, start_date, end_date)
        elif export_format == 'csv':
            return CSVExporter.export_sleep_csv(user, start_date, end_date)
        elif export_format == 'json':
            return export_user_data_json(user)
        else:
            return HttpResponse(f'不支持的格式: {export_format}', status=400)
    except ImportError as e:
        return HttpResponse(f'缺少依赖: {e}', status=500)
    except Exception as e:
        return HttpResponse(f'导出失败: {e}', status=500)

router = DefaultRouter()
router.register(r'sleep', SleepRecordViewSet, basename='sleeprecord')
router.register(r'sports', SportRecordViewSet, basename='sportrecord')
router.register(r'foods', FoodItemViewSet, basename='fooditem')
router.register(r'meals', MealViewSet, basename='meal')
router.register(r'meal-items', MealItemViewSet, basename='mealitem')
router.register(r'friendships', FriendshipViewSet, basename='friendship')
router.register(r'comments', CommentViewSet, basename='comment')
# 新增路由 (Member A)
router.register(r'body-metrics', BodyMetricViewSet, basename='bodymetric')
router.register(r'article-categories', ArticleCategoryViewSet, basename='articlecategory')
router.register(r'articles', HealthArticleViewSet, basename='healtharticle')
router.register(r'read-history', UserReadHistoryViewSet, basename='userreadhistory')
router.register(r'system-logs', SystemLogViewSet, basename='systemlog')

urlpatterns = [
# ==========================================================
    #  页面路由 (Page Routes)
    # ==========================================================
    
    # 将根路径 '/' 指向新的 index_view 视图，作为应用的统一入口
    path('', index_view, name='index'), 

    # 将 '/login/' 路径指向 login_page_view 视图，它只负责显示登录页面
    path('login/', login_page_view, name='login'),

    # 将 '/register/' 路径指向 register_page_view 视图
    path('register/', register_page_view, name='register'),
    
    # 将 '/dashboard/' 路径指向受保护的 dashboard_page_view 视图
    path('dashboard/', dashboard_page_view, name='dashboard'),

    path('sleep/', sleep_page_view, name='sleep_page'),
    path('sport/', sport_page_view, name='sport_page'),
    path('diet/', diet_page_view, name='diet_page'),
    path('report/', report_page_view, name='report_page'),
    path('profile/', profile_page_view, name='profile'),
    path('friends/', friends_page_view, name='friends_page'),
    # 新增页面路由 (Member B)
    path('body-metrics/', body_metrics_page_view, name='body_metrics_page'),
    path('articles/', articles_page_view, name='articles_page'),
    path('data-management/', data_management_view, name='data_management_page'),

    # ==========================================================
    #  API 路由 (API Routes)
    # ==========================================================

    # 1. 认证相关的 API
    path('api/register/', register_view, name='api-register'),
    path('api/login/', login_view, name='api-login'),
    path('api/logout/', logout_view, name='api-logout'),
    
    # 2. 看板数据和个人档案以及个人目标的 API
    path('api/dashboard/<str:date_str>/', DashboardView.as_view(), name='api-dashboard'),
    path('api/profile/', ProfileView.as_view(), name='api-profile'),
    path('api/goals/', UserHealthGoalView.as_view(), name='api-health-goals'),
    
    # 3. 报告、预警与推荐 API
    path('api/reports/weekly-sleep/<str:end_date_str>/', WeeklySleepReportView.as_view(), name='weekly-sleep-report'),
    path('api/reports/health-summary/', HealthReportView.as_view(), name='health-report'),
    path('api/alerts/check/', HealthAlertView.as_view(), name='api-health-alerts'),
    path('api/recommendations/diet/', DietRecommendationView.as_view(), name='api-diet-recommendation'),

    # 4. 好友健康动态 API
    path('api/feed/', HealthFeedView.as_view(), name='api-health-feed'),

    # 5. 数据导入导出 API (Member C)
    path('data-export/', data_export_view, name='api-data-export'),
    path('api/import/foods/', FoodImportView.as_view(), name='api-food-import'),

    # 6. 所有由 ViewSet 自动生成的 CRUD API
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    # 这一行会自动根据你的 STATICFILES_DIRS 设置来提供服务
    urlpatterns += staticfiles_urlpatterns()
