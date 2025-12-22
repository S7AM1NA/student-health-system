"""
health_scraper.py - 健康文章爬虫脚本 (Member C)
功能: 从健康网站爬取文章并存储到数据库

使用方法:
    python manage.py shell
    >>> from core.health_scraper import HealthArticleScraper
    >>> scraper = HealthArticleScraper()
    >>> scraper.scrape_sample_articles()  # 生成示例文章
    >>> scraper.scrape_from_rss('https://example.com/rss')  # 从RSS源爬取
"""
import re
import random
from datetime import datetime, timedelta
from django.utils import timezone

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class HealthArticleScraper:
    """健康文章爬虫类"""
    
    # 预定义的文章分类
    CATEGORIES = {
        '睡眠健康': [
            '如何改善睡眠质量',
            '失眠的常见原因与解决方法',
            '睡眠与免疫力的关系',
            '最佳睡眠时间是几点到几点',
            '午睡的好处与注意事项',
        ],
        '运动健身': [
            '适合初学者的有氧运动',
            '力量训练入门指南',
            '跑步的正确姿势',
            '运动后如何正确拉伸',
            'HIIT训练的好处与风险',
        ],
        '营养饮食': [
            '均衡饮食的基本原则',
            '蛋白质摄入的重要性',
            '减肥期间应该怎么吃',
            '常见食物的热量对比',
            '健康零食的选择',
        ],
        '心理健康': [
            '压力管理的有效方法',
            '如何保持积极心态',
            '冥想对身心的益处',
            '克服焦虑的实用技巧',
            '工作与生活的平衡',
        ],
        '体重管理': [
            'BMI指数的正确理解',
            '科学减重的核心原则',
            '为什么节食减肥会反弹',
            '如何建立健康的饮食习惯',
            '体脂率与健康的关系',
        ],
    }
    
    # 预定义的文章内容模板
    ARTICLE_TEMPLATES = {
        '睡眠健康': """
睡眠是人体最基本的生理需求之一。良好的睡眠对于身心健康至关重要。

**睡眠的重要性**

1. 恢复体力：睡眠期间，身体进行自我修复和能量储备。
2. 增强免疫：充足的睡眠有助于免疫系统正常运作。
3. 巩固记忆：睡眠帮助大脑整理和存储白天获取的信息。
4. 调节情绪：睡眠不足会导致情绪波动和注意力下降。

**改善睡眠的建议**

- 保持规律的作息时间，即使在周末也尽量按时起床。
- 睡前避免使用电子设备，蓝光会影响褪黑素分泌。
- 保持卧室环境舒适，温度在18-22度为宜。
- 避免在睡前摄入咖啡因和酒精。
- 适度运动可以改善睡眠，但不要在睡前剧烈运动。

如果长期失眠，建议及时就医，寻求专业帮助。
""",
        '运动健身': """
运动是保持健康的重要方式。无论是有氧运动还是力量训练，都对身体有诸多益处。

**运动的好处**

1. 增强心肺功能：有氧运动可以提高心脏效率。
2. 增加肌肉力量：力量训练帮助维持肌肉质量。
3. 改善情绪：运动促进内啡肽分泌，带来愉悦感。
4. 控制体重：消耗热量，帮助维持健康体重。

**运动建议**

- 每周至少进行150分钟中等强度有氧运动。
- 每周进行2-3次力量训练，覆盖主要肌群。
- 运动前热身，运动后拉伸，预防受伤。
- 循序渐进，不要急于求成。
- 选择适合自己的运动方式，坚持最重要。

开始运动前，建议咨询医生，特别是有慢性病的人群。
""",
        '营养饮食': """
合理的饮食是健康的基石。均衡摄入各类营养素，是保持身体机能正常运转的关键。

**营养素的作用**

1. 碳水化合物：提供主要能量来源。
2. 蛋白质：构建和修复身体组织。
3. 脂肪：储能、保护器官、促进营养吸收。
4. 维生素和矿物质：参与各种代谢过程。

**健康饮食原则**

- 多吃蔬菜水果，每天至少5份。
- 选择全谷物，减少精制碳水。
- 适量摄入优质蛋白（瘦肉、鱼、蛋、豆类）。
- 控制盐、糖、油的摄入量。
- 保持充足的水分摄入。

记住：没有绝对的"好"或"坏"食物，关键是整体的饮食模式。
""",
        '心理健康': """
心理健康与身体健康同样重要。在快节奏的现代生活中，保持心理平衡尤为重要。

**心理健康的重要性**

1. 影响身体健康：长期压力会导致多种疾病。
2. 影响工作效率：良好的心理状态提高生产力。
3. 影响人际关系：情绪稳定有助于建立和谐关系。
4. 影响生活质量：心理健康是幸福感的重要组成部分。

**维护心理健康的方法**

- 学会识别压力信号，及时调整。
- 保持社交联系，与朋友家人沟通。
- 培养兴趣爱好，找到放松方式。
- 规律作息，保证充足睡眠。
- 必要时寻求专业心理帮助。

记住：关注心理健康不是软弱的表现，而是自我关爱的体现。
""",
        '体重管理': """
健康的体重管理不仅仅是关于数字，更是关于整体健康和生活方式。

**体重管理的核心原则**

1. 热量平衡：摄入与消耗的平衡决定体重变化。
2. 可持续性：极端减肥不可取，关键是长期坚持。
3. 全面考量：体重只是健康指标之一，不是唯一标准。
4. 个体差异：每个人的健康体重范围不同。

**科学管理体重的方法**

- 设定合理目标，每周减重0.5-1kg为宜。
- 记录饮食和运动，了解自己的习惯。
- 不要完全戒断某类食物，学会适度。
- 增加日常活动量，如走楼梯、步行。
- 关注进展而非完美，允许偶尔的"放纵"。

记住：健康的身体比数字更重要。如有需要，请咨询专业人士。
"""
    }
    
    def __init__(self):
        """初始化爬虫"""
        pass
    
    def scrape_sample_articles(self, count_per_category=3):
        """
        生成示例健康文章并存入数据库
        
        参数:
            count_per_category: 每个分类生成的文章数量
        
        返回:
            dict: 统计信息
        """
        from .models import ArticleCategory, HealthArticle, CustomUser
        
        # 获取管理员用户作为作者
        admin_user = CustomUser.objects.filter(is_staff=True).first()
        if not admin_user:
            admin_user = CustomUser.objects.first()
        
        result = {'categories_created': 0, 'articles_created': 0}
        
        for category_name, article_titles in self.CATEGORIES.items():
            # 创建或获取分类
            category, created = ArticleCategory.objects.get_or_create(
                name=category_name,
                defaults={'description': f'{category_name}相关的健康科普文章'}
            )
            if created:
                result['categories_created'] += 1
            
            # 获取该分类的内容模板
            content_template = self.ARTICLE_TEMPLATES.get(category_name, '')
            
            # 创建文章
            selected_titles = random.sample(article_titles, min(count_per_category, len(article_titles)))
            
            for i, title in enumerate(selected_titles):
                # 检查文章是否已存在
                if HealthArticle.objects.filter(title=title).exists():
                    continue
                
                # 生成文章内容（在模板基础上做一些个性化）
                content = f"# {title}\n\n{content_template}"
                
                # 随机生成发布日期（过去30天内）
                days_ago = random.randint(0, 30)
                publish_date = timezone.now() - timedelta(days=days_ago)
                
                # 创建文章
                HealthArticle.objects.create(
                    category=category,
                    title=title,
                    content=content,
                    author=admin_user,
                    publish_date=publish_date,
                    views=random.randint(0, 100)  # 随机初始阅读量
                )
                result['articles_created'] += 1
        
        return result
    
    def scrape_from_url(self, url):
        """
        从指定URL爬取文章内容
        
        注意：此功能需要根据目标网站结构进行定制
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests 或 beautifulsoup4 未安装，请运行: pip install requests beautifulsoup4")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 通用内容提取（需要根据实际网站调整）
            title = soup.find('h1').get_text(strip=True) if soup.find('h1') else '未知标题'
            
            # 尝试找到文章正文
            article_body = soup.find('article') or soup.find('div', class_=re.compile(r'content|article|post'))
            if article_body:
                # 移除脚本和样式
                for tag in article_body.find_all(['script', 'style', 'nav', 'aside']):
                    tag.decompose()
                content = article_body.get_text(separator='\n', strip=True)
            else:
                content = ''
            
            return {
                'title': title,
                'content': content,
                'url': url
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'url': url
            }


# 便捷函数：用于 Django shell
def generate_sample_articles():
    """
    在 Django shell 中快速生成示例文章
    
    使用方法:
        python manage.py shell
        >>> from core.health_scraper import generate_sample_articles
        >>> generate_sample_articles()
    """
    scraper = HealthArticleScraper()
    result = scraper.scrape_sample_articles()
    print(f"✅ 生成完成: 创建了 {result['categories_created']} 个分类和 {result['articles_created']} 篇文章")
    return result
