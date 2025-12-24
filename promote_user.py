"""
用户权限升级脚本 - 将所有用户升级为管理员
使用方法: 在项目根目录运行 python promote_user.py
"""
import os
import sys

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_system.settings')

import django
django.setup()

from core.models import CustomUser

def main():
    print("=" * 50)
    print("  用户权限升级工具")
    print("=" * 50)
    
    users = CustomUser.objects.all()
    
    if not users.exists():
        print("\n❌ 数据库中没有任何用户，请先注册一个账号。")
        return
    
    print(f"\n找到 {users.count()} 个用户，正在升级为管理员...\n")
    
    upgraded_count = 0
    for user in users:
        old_status = user.is_staff
        user.is_staff = True
        user.is_superuser = True
        user.save()
        
        status = "✅ 已升级" if not old_status else "⏭️ 已是管理员"
        print(f"  {status}: {user.username} (ID: {user.id})")
        upgraded_count += 1
    
    print(f"\n{'=' * 50}")
    print(f"✅ 完成！共处理 {upgraded_count} 个用户。")
    print("现在您可以用任意账号登录后使用【数据管理】功能了。")
    print("=" * 50)

if __name__ == "__main__":
    main()
