/**
 * articles.js - 健康文章页面 JavaScript (Member B)
 * 功能: 加载文章分类、文章列表、文章详情
 */

document.addEventListener('DOMContentLoaded', function () {
    // DOM 元素
    const categoryFilter = document.getElementById('category-filter');
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const articleList = document.getElementById('article-list');
    const emptyState = document.getElementById('empty-state');
    const articleDetailModal = document.getElementById('articleDetailModal');

    // 详情模态框元素
    const detailTitle = document.getElementById('articleDetailModalLabel');
    const detailCategory = document.getElementById('detail-category');
    const detailAuthor = document.getElementById('detail-author');
    const detailDate = document.getElementById('detail-date');
    const detailViews = document.getElementById('detail-views');
    const articleContent = document.getElementById('article-content');

    let allArticles = [];

    // 初始化
    init();

    function init() {
        loadCategories();
        loadArticles();

        // 事件监听
        categoryFilter.addEventListener('change', filterArticles);
        searchBtn.addEventListener('click', filterArticles);
        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') filterArticles();
        });
    }

    // 加载分类
    async function loadCategories() {
        try {
            const response = await fetch('/api/article-categories/', {
                credentials: 'include'
            });
            if (!response.ok) throw new Error('加载分类失败');

            const categories = await response.json();
            categoryFilter.innerHTML = '<option value="">全部分类</option>' +
                categories.map(c => `<option value="${c.id}">${c.name} (${c.article_count})</option>`).join('');
        } catch (error) {
            console.error('加载分类失败:', error);
        }
    }

    // 加载文章列表
    async function loadArticles() {
        try {
            const response = await fetch('/api/articles/', {
                credentials: 'include'
            });
            if (!response.ok) throw new Error('加载文章失败');

            allArticles = await response.json();
            renderArticles(allArticles);
        } catch (error) {
            console.error('加载文章失败:', error);
            articleList.innerHTML = '<div class="col-12 text-center text-danger py-5">加载失败，请刷新重试</div>';
        }
    }

    // 过滤文章
    function filterArticles() {
        const categoryId = categoryFilter.value;
        const searchTerm = searchInput.value.toLowerCase().trim();

        let filtered = allArticles;

        if (categoryId) {
            filtered = filtered.filter(a => a.category == categoryId);
        }

        if (searchTerm) {
            filtered = filtered.filter(a =>
                a.title.toLowerCase().includes(searchTerm) ||
                (a.content && a.content.toLowerCase().includes(searchTerm))
            );
        }

        renderArticles(filtered);
    }

    // 渲染文章列表
    function renderArticles(articles) {
        if (articles.length === 0) {
            articleList.innerHTML = '';
            emptyState.classList.remove('d-none');
            return;
        }

        emptyState.classList.add('d-none');
        articleList.innerHTML = articles.map(article => `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card article-card h-100" onclick="viewArticle(${article.id})">
                    <div class="card-body">
                        <div class="mb-2">
                            <span class="badge bg-primary">${article.category_name || '未分类'}</span>
                        </div>
                        <h5 class="card-title">${escapeHtml(article.title)}</h5>
                        <p class="card-text text-muted">${escapeHtml(article.content ? article.content.substring(0, 100) + '...' : '')}</p>
                    </div>
                    <div class="card-footer bg-transparent border-top-0">
                        <small class="text-muted">
                            <i class="bi bi-person me-1"></i>${article.author_name || '匿名'}
                            <span class="float-end">
                                <i class="bi bi-eye me-1"></i>${article.views}
                            </span>
                        </small>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // 查看文章详情 (全局函数)
    window.viewArticle = async function (id) {
        try {
            const response = await fetch(`/api/articles/${id}/`, {
                credentials: 'include'
            });
            if (!response.ok) throw new Error('加载文章详情失败');

            const article = await response.json();

            // 填充详情
            detailTitle.textContent = article.title;
            detailCategory.textContent = article.category_name || '未分类';
            detailAuthor.textContent = article.author_name || '匿名';
            detailDate.textContent = article.publish_date ? article.publish_date.slice(0, 10) : '--';
            detailViews.textContent = article.views;

            // 简单地将内容中的换行转为 <p> 标签
            articleContent.innerHTML = article.content
                .split('\n')
                .filter(p => p.trim())
                .map(p => `<p>${escapeHtml(p)}</p>`)
                .join('');

            // 显示模态框
            const modal = new bootstrap.Modal(articleDetailModal);
            modal.show();

            // 更新列表中的阅读数
            const articleIndex = allArticles.findIndex(a => a.id === id);
            if (articleIndex !== -1) {
                allArticles[articleIndex].views = article.views;
            }

        } catch (error) {
            console.error('加载文章详情失败:', error);
            alert('加载文章详情失败');
        }
    };

    // HTML 转义
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
