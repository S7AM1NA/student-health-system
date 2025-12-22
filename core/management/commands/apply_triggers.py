"""
Django Management Command: apply_triggers
应用 SQL 触发器和视图到数据库

使用方法: python manage.py apply_triggers
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = '应用 SQL 触发器和视图到 SQLite 数据库'

    def handle(self, *args, **options):
        triggers = [
            # 触发器1: 自动计算睡眠时长
            """
            CREATE TRIGGER IF NOT EXISTS trg_calculate_sleep_duration
            AFTER INSERT ON core_sleeprecord
            BEGIN
                UPDATE core_sleeprecord
                SET duration = (
                    strftime('%s', NEW.wakeup_time) - strftime('%s', NEW.sleep_time)
                )
                WHERE id = NEW.id;
            END;
            """,
            # 触发器2: 自动计算 BMI
            """
            CREATE TRIGGER IF NOT EXISTS trg_calculate_bmi
            AFTER INSERT ON core_bodymetric
            BEGIN
                UPDATE core_bodymetric
                SET bmi = ROUND(NEW.weight / ((NEW.height / 100.0) * (NEW.height / 100.0)), 2)
                WHERE id = NEW.id;
            END;
            """,
            # 触发器3: 自动计算餐品热量
            """
            CREATE TRIGGER IF NOT EXISTS trg_calculate_meal_item_calories
            AFTER INSERT ON core_mealitem
            BEGIN
                UPDATE core_mealitem
                SET calories_calculated = (
                    SELECT ROUND((fi.calories_per_100g / 100.0) * NEW.portion, 2)
                    FROM core_fooditem fi
                    WHERE fi.id = NEW.food_item_id
                )
                WHERE id = NEW.id;
            END;
            """,
            # 触发器4: 自动增加文章阅读量
            """
            CREATE TRIGGER IF NOT EXISTS trg_increment_article_views
            AFTER INSERT ON core_userreadhistory
            BEGIN
                UPDATE core_healtharticle
                SET views = views + 1
                WHERE id = NEW.article_id;
            END;
            """,
        ]

        views = [
            # 视图1: 用户每日健康摘要
            """
            CREATE VIEW IF NOT EXISTS v_user_daily_summary AS
            SELECT 
                u.id AS user_id,
                u.username,
                DATE(sr.wakeup_time) AS record_date,
                ROUND(sr.duration / 3600.0, 2) AS sleep_hours
            FROM core_customuser u
            LEFT JOIN core_sleeprecord sr ON sr.user_id = u.id;
            """,
        ]

        with connection.cursor() as cursor:
            self.stdout.write(self.style.NOTICE('正在应用触发器...'))
            for i, trigger_sql in enumerate(triggers, 1):
                try:
                    cursor.executescript(trigger_sql)
                    self.stdout.write(self.style.SUCCESS(f'  ✅ 触发器 {i} 应用成功'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ❌ 触发器 {i} 失败: {e}'))

            self.stdout.write(self.style.NOTICE('正在创建视图...'))
            for i, view_sql in enumerate(views, 1):
                try:
                    cursor.executescript(view_sql)
                    self.stdout.write(self.style.SUCCESS(f'  ✅ 视图 {i} 创建成功'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ❌ 视图 {i} 失败: {e}'))

        self.stdout.write(self.style.SUCCESS('\\n所有触发器和视图已应用完成！'))
