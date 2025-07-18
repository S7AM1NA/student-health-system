import json
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt # 方便开发阶段调试API
from .models import CustomUser

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