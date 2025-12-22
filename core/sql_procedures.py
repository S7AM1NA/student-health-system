"""
SQL 存储过程、触发器和函数定义文件 (Member A)
本文件包含课程设计所需的 SQL 代码，需要在数据库中手动执行。

注意：SQLite 对存储过程和触发器的支持有限，以下代码针对 SQLite 语法优化。
如需迁移到 MySQL/PostgreSQL，请参考文件末尾的适配说明。
"""

# ============================================================
# 1. 触发器 (Triggers) - SQLite 语法
# ============================================================

TRIGGER_AUTO_CALCULATE_SLEEP_DURATION = """
-- 触发器：自动计算睡眠时长
-- 当插入或更新睡眠记录时，自动计算 duration 字段
CREATE TRIGGER IF NOT EXISTS trg_calculate_sleep_duration
AFTER INSERT ON core_sleeprecord
BEGIN
    UPDATE core_sleeprecord
    SET duration = (
        strftime('%s', NEW.wakeup_time) - strftime('%s', NEW.sleep_time)
    )
    WHERE id = NEW.id;
END;
"""

TRIGGER_AUTO_CALCULATE_BMI = """
-- 触发器：自动计算 BMI
-- 当插入身体指标记录时，自动计算 BMI = 体重(kg) / (身高(m))^2
CREATE TRIGGER IF NOT EXISTS trg_calculate_bmi
AFTER INSERT ON core_bodymetric
BEGIN
    UPDATE core_bodymetric
    SET bmi = ROUND(NEW.weight / ((NEW.height / 100.0) * (NEW.height / 100.0)), 2)
    WHERE id = NEW.id;
END;
"""

TRIGGER_AUTO_CALCULATE_MEAL_CALORIES = """
-- 触发器：自动计算餐品热量
-- 当插入餐品条目时，自动计算 calories_calculated
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
"""

TRIGGER_INCREMENT_ARTICLE_VIEWS = """
-- 触发器：自动增加文章阅读量
-- 当插入阅读历史记录时，自动增加对应文章的 views 计数
CREATE TRIGGER IF NOT EXISTS trg_increment_article_views
AFTER INSERT ON core_userreadhistory
BEGIN
    UPDATE core_healtharticle
    SET views = views + 1
    WHERE id = NEW.article_id;
END;
"""

# ============================================================
# 2. 视图 (Views) - 外模式定义
# ============================================================

VIEW_USER_DAILY_SUMMARY = """
-- 视图：用户每日健康摘要
-- 用于快速查询某用户某天的健康数据汇总
CREATE VIEW IF NOT EXISTS v_user_daily_summary AS
SELECT 
    u.id AS user_id,
    u.username,
    DATE(sr.wakeup_time) AS record_date,
    ROUND(sr.duration / 3600.0, 2) AS sleep_hours,
    (
        SELECT SUM(spr.duration_minutes) 
        FROM core_sportrecord spr 
        WHERE spr.user_id = u.id AND spr.record_date = DATE(sr.wakeup_time)
    ) AS total_sport_minutes,
    (
        SELECT SUM(spr.calories_burned) 
        FROM core_sportrecord spr 
        WHERE spr.user_id = u.id AND spr.record_date = DATE(sr.wakeup_time)
    ) AS total_calories_burned,
    (
        SELECT SUM(mi.calories_calculated)
        FROM core_meal m
        JOIN core_mealitem mi ON mi.meal_id = m.id
        WHERE m.user_id = u.id AND m.record_date = DATE(sr.wakeup_time)
    ) AS total_calories_eaten
FROM core_customuser u
LEFT JOIN core_sleeprecord sr ON sr.user_id = u.id;
"""

VIEW_USER_HEALTH_DATA = """
-- 视图：用户个人健康数据（外模式）
-- 普通用户只能通过此视图访问自己的数据
CREATE VIEW IF NOT EXISTS v_my_health_data AS
SELECT 
    sr.id, sr.user_id, sr.sleep_time, sr.wakeup_time, sr.duration
FROM core_sleeprecord sr;
-- 注意：实际权限控制在应用层通过 ORM 的 filter(user=request.user) 实现
"""

# ============================================================
# 3. 存储过程（模拟）- SQLite 不支持存储过程，使用 Python 函数模拟
# ============================================================

def get_weekly_health_report_sql(user_id, end_date):
    """
    存储过程（模拟）：获取用户周度健康报告
    
    参数:
        user_id: 用户ID
        end_date: 报告结束日期 (YYYY-MM-DD)
    
    返回:
        SQL 查询语句
    """
    return f"""
    SELECT 
        DATE(sr.wakeup_time) AS date,
        ROUND(sr.duration / 3600.0, 2) AS sleep_hours,
        COALESCE((
            SELECT SUM(spr.calories_burned) 
            FROM core_sportrecord spr 
            WHERE spr.user_id = {user_id} AND spr.record_date = DATE(sr.wakeup_time)
        ), 0) AS calories_burned,
        COALESCE((
            SELECT SUM(mi.calories_calculated)
            FROM core_meal m
            JOIN core_mealitem mi ON mi.meal_id = m.id
            WHERE m.user_id = {user_id} AND m.record_date = DATE(sr.wakeup_time)
        ), 0) AS calories_eaten
    FROM core_sleeprecord sr
    WHERE sr.user_id = {user_id}
      AND DATE(sr.wakeup_time) BETWEEN DATE('{end_date}', '-6 days') AND DATE('{end_date}')
    ORDER BY DATE(sr.wakeup_time);
    """


def calculate_calorie_balance_sql(user_id, date):
    """
    函数（模拟）：计算用户某天的热量平衡
    
    参数:
        user_id: 用户ID
        date: 日期 (YYYY-MM-DD)
    
    返回:
        SQL 查询语句，返回 (calories_in, calories_out, balance)
    """
    return f"""
    SELECT 
        COALESCE((
            SELECT SUM(mi.calories_calculated)
            FROM core_meal m
            JOIN core_mealitem mi ON mi.meal_id = m.id
            WHERE m.user_id = {user_id} AND m.record_date = '{date}'
        ), 0) AS calories_in,
        COALESCE((
            SELECT SUM(spr.calories_burned)
            FROM core_sportrecord spr
            WHERE spr.user_id = {user_id} AND spr.record_date = '{date}'
        ), 0) AS calories_out,
        (
            COALESCE((
                SELECT SUM(mi.calories_calculated)
                FROM core_meal m
                JOIN core_mealitem mi ON mi.meal_id = m.id
                WHERE m.user_id = {user_id} AND m.record_date = '{date}'
            ), 0) -
            COALESCE((
                SELECT SUM(spr.calories_burned)
                FROM core_sportrecord spr
                WHERE spr.user_id = {user_id} AND spr.record_date = '{date}'
            ), 0)
        ) AS balance;
    """


# ============================================================
# 4. 执行脚本：将触发器应用到数据库
# ============================================================

def apply_triggers_to_database():
    """
    将所有触发器应用到 SQLite 数据库
    在 Django shell 中执行: python manage.py shell < core/sql_procedures.py
    """
    from django.db import connection
    
    triggers = [
        TRIGGER_AUTO_CALCULATE_SLEEP_DURATION,
        TRIGGER_AUTO_CALCULATE_BMI,
        TRIGGER_AUTO_CALCULATE_MEAL_CALORIES,
        TRIGGER_INCREMENT_ARTICLE_VIEWS,
    ]
    
    views = [
        VIEW_USER_DAILY_SUMMARY,
        VIEW_USER_HEALTH_DATA,
    ]
    
    with connection.cursor() as cursor:
        for trigger_sql in triggers:
            try:
                cursor.executescript(trigger_sql)
                print(f"✅ Trigger applied successfully")
            except Exception as e:
                print(f"❌ Error applying trigger: {e}")
        
        for view_sql in views:
            try:
                cursor.executescript(view_sql)
                print(f"✅ View created successfully")
            except Exception as e:
                print(f"❌ Error creating view: {e}")
    
    print("\\n所有触发器和视图已应用完成！")


# 如果直接运行此文件，则应用触发器
if __name__ == "__main__":
    apply_triggers_to_database()
