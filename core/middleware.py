"""
System Logging Middleware (Member A)
记录用户的关键操作到 SystemLog 表，用于安全审计。
"""
from .models import SystemLog


def get_client_ip(request):
    """获取客户端真实IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class SystemLoggingMiddleware:
    """
    中间件：自动记录用户的敏感操作（POST/PUT/DELETE 请求）到 SystemLog。
    """
    # 需要记录的敏感路径前缀
    SENSITIVE_PATHS = [
        '/api/register/',
        '/api/login/',
        '/api/logout/',
        '/api/profile/',
        '/api/sleep/',
        '/api/sports/',
        '/api/meals/',
        '/api/goals/',
        '/api/friends/',
        '/api/body-metrics/',
        '/api/articles/',
    ]
    
    # 需要记录的HTTP方法
    LOGGED_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 获取响应
        response = self.get_response(request)
        
        # 只记录敏感路径的敏感方法
        if request.method in self.LOGGED_METHODS:
            if any(request.path.startswith(path) for path in self.SENSITIVE_PATHS):
                self._log_action(request, response)
        
        return response

    def _log_action(self, request, response):
        """记录操作到数据库"""
        try:
            user = request.user if request.user.is_authenticated else None
            action = f"{request.method} {request.path}"
            ip_address = get_client_ip(request)
            
            # 构建详细信息
            details = f"Status: {response.status_code}"
            if request.method in ['POST', 'PUT', 'PATCH']:
                # 记录请求体（脱敏处理密码）
                body = request.POST.dict() if request.POST else {}
                if 'password' in body:
                    body['password'] = '******'
                if body:
                    details += f" | Data: {body}"
            
            SystemLog.objects.create(
                user=user,
                action=action,
                ip_address=ip_address,
                details=details
            )
        except Exception as e:
            # 日志记录失败不应影响主业务
            print(f"SystemLog Error: {e}")
