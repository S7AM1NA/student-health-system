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
    WeeklySleepReportView,
    HealthReportView,
)

from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

router = DefaultRouter()
router.register(r'sleep', SleepRecordViewSet, basename='sleeprecord')
router.register(r'sports', SportRecordViewSet, basename='sportrecord')
router.register(r'foods', FoodItemViewSet, basename='fooditem')
router.register(r'meals', MealViewSet, basename='meal')
router.register(r'meal-items', MealItemViewSet, basename='mealitem')

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
    path('profile/', profile_page_view, name='profile'),

    # ==========================================================
    #  API 路由 (API Routes)
    # ==========================================================

    # 1. 认证相关的 API
    path('api/register/', register_view, name='api-register'),
    path('api/login/', login_view, name='api-login'),
    path('api/logout/', logout_view, name='api-logout'),
    
    # 2. 看板数据和个人档案的 API
    path('api/dashboard/<str:date_str>/', DashboardView.as_view(), name='api-dashboard'),
    path('api/profile/', ProfileView.as_view(), name='api-profile'),
    
    # 功能1：周度睡眠报告 API
    # URL 示例: /api/reports/weekly-sleep/2023-10-27/
    path('api/reports/weekly-sleep/<str:end_date_str>/', WeeklySleepReportView.as_view(), name='weekly-sleep-report'),
    # 功能2：周期性健康报告 API
    # URL 示例: /api/reports/health-summary/?start_date=2023-10-01&end_date=2023-10-27
    path('api/reports/health-summary/', HealthReportView.as_view(), name='health-report'),

    # 3. 所有由 ViewSet 自动生成的 CRUD API
    #    这会自动创建如 /api/sleep/, /api/sports/ 等一系列接口
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    # 这一行会自动根据你的 STATICFILES_DIRS 设置来提供服务
    urlpatterns += staticfiles_urlpatterns()
