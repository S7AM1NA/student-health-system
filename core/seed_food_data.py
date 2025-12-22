"""
seed_food_data.py - 食物数据库初始化脚本
使用方法: python manage.py shell < core/seed_food_data.py
或者在 Django shell 中: exec(open('core/seed_food_data.py').read())
"""

from core.models import FoodItem

# 常见食物数据 (每100g的营养成分)
FOOD_DATA = [
    # 主食类
    {"name": "米饭", "calories_per_100g": 116, "protein": 2.6, "fat": 0.3, "carbohydrates": 25.9},
    {"name": "馒头", "calories_per_100g": 223, "protein": 7.0, "fat": 1.1, "carbohydrates": 47.0},
    {"name": "面条", "calories_per_100g": 137, "protein": 4.5, "fat": 0.5, "carbohydrates": 28.5},
    {"name": "全麦面包", "calories_per_100g": 246, "protein": 8.5, "fat": 3.4, "carbohydrates": 45.8},
    {"name": "燕麦", "calories_per_100g": 367, "protein": 15.0, "fat": 7.0, "carbohydrates": 61.0},
    
    # 肉类
    {"name": "鸡胸肉", "calories_per_100g": 133, "protein": 24.6, "fat": 5.0, "carbohydrates": 0.0},
    {"name": "牛肉", "calories_per_100g": 125, "protein": 20.0, "fat": 4.2, "carbohydrates": 0.0},
    {"name": "猪瘦肉", "calories_per_100g": 143, "protein": 20.3, "fat": 6.2, "carbohydrates": 0.0},
    {"name": "三文鱼", "calories_per_100g": 139, "protein": 19.8, "fat": 6.3, "carbohydrates": 0.0},
    {"name": "虾", "calories_per_100g": 93, "protein": 18.6, "fat": 1.2, "carbohydrates": 0.0},
    
    # 蛋奶类
    {"name": "鸡蛋", "calories_per_100g": 147, "protein": 13.3, "fat": 8.8, "carbohydrates": 2.8},
    {"name": "牛奶", "calories_per_100g": 54, "protein": 3.0, "fat": 3.2, "carbohydrates": 3.4},
    {"name": "酸奶", "calories_per_100g": 72, "protein": 2.5, "fat": 2.7, "carbohydrates": 9.3},
    {"name": "豆腐", "calories_per_100g": 81, "protein": 8.1, "fat": 3.7, "carbohydrates": 4.2},
    
    # 蔬菜类
    {"name": "西兰花", "calories_per_100g": 34, "protein": 4.1, "fat": 0.6, "carbohydrates": 4.3},
    {"name": "菠菜", "calories_per_100g": 28, "protein": 2.6, "fat": 0.3, "carbohydrates": 4.5},
    {"name": "番茄", "calories_per_100g": 19, "protein": 0.9, "fat": 0.2, "carbohydrates": 3.9},
    {"name": "黄瓜", "calories_per_100g": 15, "protein": 0.8, "fat": 0.2, "carbohydrates": 2.9},
    {"name": "胡萝卜", "calories_per_100g": 39, "protein": 1.0, "fat": 0.2, "carbohydrates": 8.8},
    {"name": "白菜", "calories_per_100g": 17, "protein": 1.5, "fat": 0.2, "carbohydrates": 3.2},
    
    # 水果类
    {"name": "苹果", "calories_per_100g": 52, "protein": 0.3, "fat": 0.2, "carbohydrates": 13.8},
    {"name": "香蕉", "calories_per_100g": 93, "protein": 1.4, "fat": 0.2, "carbohydrates": 22.8},
    {"name": "橙子", "calories_per_100g": 48, "protein": 0.8, "fat": 0.2, "carbohydrates": 11.8},
    {"name": "葡萄", "calories_per_100g": 69, "protein": 0.5, "fat": 0.2, "carbohydrates": 17.1},
    {"name": "西瓜", "calories_per_100g": 30, "protein": 0.6, "fat": 0.1, "carbohydrates": 7.6},
    
    # 坚果类
    {"name": "核桃", "calories_per_100g": 654, "protein": 15.2, "fat": 65.2, "carbohydrates": 9.6},
    {"name": "杏仁", "calories_per_100g": 578, "protein": 21.3, "fat": 49.9, "carbohydrates": 21.7},
    {"name": "花生", "calories_per_100g": 567, "protein": 24.8, "fat": 44.3, "carbohydrates": 21.7},
]

def seed_food_database():
    """填充食物数据库"""
    created_count = 0
    updated_count = 0
    
    for food_data in FOOD_DATA:
        food, created = FoodItem.objects.get_or_create(
            name=food_data["name"],
            defaults={
                "calories_per_100g": food_data["calories_per_100g"],
                "protein": food_data["protein"],
                "fat": food_data["fat"],
                "carbohydrates": food_data["carbohydrates"]
            }
        )
        
        if created:
            created_count += 1
            print(f"✅ 创建: {food_data['name']}")
        else:
            # 更新已存在的食物
            food.calories_per_100g = food_data["calories_per_100g"]
            food.protein = food_data["protein"]
            food.fat = food_data["fat"]
            food.carbohydrates = food_data["carbohydrates"]
            food.save()
            updated_count += 1
            print(f"🔄 更新: {food_data['name']}")
    
    print(f"\n完成！创建 {created_count} 个食物，更新 {updated_count} 个食物")
    print(f"食物库总数: {FoodItem.objects.count()}")

# 执行填充
if __name__ == "__main__":
    seed_food_database()
else:
    # 在 Django shell 中直接执行
    seed_food_database()
