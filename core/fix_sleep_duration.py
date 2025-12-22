"""
fix_sleep_duration.py - 修复现有睡眠记录的时长
使用方法: python manage.py shell < core/fix_sleep_duration.py
"""

from core.models import SleepRecord

def fix_sleep_durations():
    """修复所有睡眠记录的时长"""
    records = SleepRecord.objects.all()
    fixed_count = 0
    
    for record in records:
        if record.sleep_time and record.wakeup_time:
            old_duration = record.duration
            record.duration = record.wakeup_time - record.sleep_time
            record.save()
            
            if old_duration != record.duration:
                fixed_count += 1
                print(f"✅ 修复记录 #{record.id}: {old_duration} → {record.duration}")
    
    print(f"\n完成！修复了 {fixed_count} 条记录")
    print(f"总记录数: {records.count()}")

# 执行修复
if __name__ == "__main__":
    fix_sleep_durations()
else:
    fix_sleep_durations()
