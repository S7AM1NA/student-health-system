# core/management/commands/import_food_data.py

import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from core.models import FoodItem

class Command(BaseCommand):
    help = '从指定目录下的所有JSON文件导入食物数据到FoodItem数据库中'

    def add_arguments(self, parser):
        # 参数现在是目录路径，而不是单个文件路径
        parser.add_argument('directory_path', type=str, help='包含JSON文件的目录路径')

    def handle(self, *args, **options):
        # 使用 pathlib 处理路径，更现代、更健壮
        dir_path = Path(options['directory_path'])

        # 检查路径是否存在且是一个目录
        if not dir_path.is_dir():
            raise CommandError(f'错误: "{dir_path}" 不是一个有效的目录。')

        # 使用 glob 查找目录下所有 .json 文件
        json_files = list(dir_path.glob('*.json'))

        if not json_files:
            self.stdout.write(self.style.WARNING(f'在目录 "{dir_path}" 中没有找到任何 .json 文件。'))
            return

        self.stdout.write(self.style.SUCCESS(f'在 "{dir_path}" 中找到 {len(json_files)} 个JSON文件。开始导入...'))
        
        # 初始化总计数器
        total_created = 0
        total_updated = 0
        total_skipped = 0

        # 遍历所有找到的JSON文件
        for file_path in json_files:
            self.stdout.write(f'\n--- 正在处理文件: {file_path.name} ---')
            try:
                # 调用一个辅助方法来处理单个文件的导入逻辑
                created, updated, skipped = self._import_file(file_path)
                total_created += created
                total_updated += updated
                total_skipped += skipped
                self.stdout.write(self.style.SUCCESS(f'处理完成: 新增 {created}, 更新 {updated}, 跳过 {skipped}'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'处理文件 {file_path.name} 时发生严重错误: {e}'))

        # 在所有文件处理完毕后，打印总报告
        self.stdout.write(self.style.SUCCESS('\n===================='))
        self.stdout.write(self.style.SUCCESS('所有文件导入完成！'))
        self.stdout.write(f'  - 总计新增: {total_created}')
        self.stdout.write(f'  - 总计更新: {total_updated}')
        self.stdout.write(f'  - 总计跳过: {total_skipped}')

    def _import_file(self, file_path):
        """处理单个JSON文件的导入逻辑。"""
        created_count = 0
        updated_count = 0
        skipped_count = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR(f'文件 "{file_path.name}" 格式错误，不是有效的JSON。'))
            return 0, 0, 1 # 返回计数值
        
        if not isinstance(data, list):
            self.stderr.write(self.style.ERROR(f'文件 "{file_path.name}" 的JSON顶层结构不是一个列表。'))
            return 0, 0, 1

        for item in data:
            food_name = item.get('foodName')
            calories_str = item.get('energyKCal')
            product_code = item.get('foodCode')

            if not all([food_name, calories_str, product_code]):
                skipped_count += 1
                continue

            try:
                calories_float = float(calories_str)
            except (ValueError, TypeError):
                skipped_count += 1
                continue

            try:
                _, created = FoodItem.objects.update_or_create(
                    product_code=product_code,
                    defaults={
                        'name': food_name,
                        'calories_per_100g': calories_float
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'导入 "{food_name}" 时数据库出错: {e}'))
                skipped_count += 1
        
        return created_count, updated_count, skipped_count