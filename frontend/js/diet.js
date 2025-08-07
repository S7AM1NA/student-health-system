document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. 定义常量和获取DOM元素 ---
    const dietForm = document.getElementById('diet-form');
    const foodDatalist = document.getElementById('food-datalist');
    const dietDetailsContainer = document.getElementById('diet-details-container');
    const totalCaloriesEl = document.getElementById('total-calories-eaten-display');
    
    // ✨ 新增元素获取
    const dateSelector = document.getElementById('date-selector');
    const displayDateEl = document.getElementById('display-date');
    const recordListTitleEl = document.getElementById('record-list-title');

    // API的URL
    const API_FOODS_URL = '/api/foods/';
    const API_MEALS_URL = '/api/meals/';
    const API_MEAL_ITEMS_URL = '/api/meal-items/';

    // --- 2. 核心功能函数 ---

    // [不变] 函数：获取食物库并填充datalist
    async function fetchAndPopulateFoodItems() {
        try {
            const response = await fetch(API_FOODS_URL, { credentials: 'include' });
            const foodItems = await response.json();
            
            foodDatalist.innerHTML = '';
            foodItems.forEach(food => {
                const option = document.createElement('option');
                option.value = food.name;
                option.dataset.id = food.id;
                option.dataset.calories = food.calories_per_100g;
                foodDatalist.appendChild(option);
            });
        } catch (error) {
            console.error('获取食物库失败:', error);
        }
    }

    /**
     * 函数：获取并渲染指定日期的餐次记录
     * @param {string} dateStr - 'YYYY-MM-DD'格式的日期
     */
    async function fetchAndRenderMeals(dateStr) {
        // 更新UI上的日期和加载状态
        displayDateEl.textContent = dateStr;
        recordListTitleEl.textContent = `${dateStr} 的饮食详情`;
        dietDetailsContainer.innerHTML = `<div class="text-center"><div class="spinner-border spinner-border-sm"></div></div>`;
        updateTotalCalories([]); // 先清零总热量

        const url = `${API_MEALS_URL}?record_date=${dateStr}`;
        try {
            const response = await fetch(url, { credentials: 'include' });
            if (!response.ok) throw new Error('获取餐次数据失败');
            const meals = await response.json();
            renderMeals(meals);
            updateTotalCalories(meals);
        } catch (error) {
            console.error('获取餐次数据失败:', error);
            dietDetailsContainer.innerHTML = `<p class="text-danger">数据加载失败: ${error.message}</p>`;
        }
        fetchAndRenderRecommendation(dateStr, 'lunch');
    }

    /**
     * 获取并渲染指定日期的饮食推荐
     * @param {string} dateStr - 日期 'YYYY-MM-DD'
     * @param {string} mealType - 餐次 'breakfast', 'lunch', etc.
     */
    async function fetchAndRenderRecommendation(dateStr, mealType) {
        const container = document.getElementById('recommendation-container');
        if (!container) return;

        container.innerHTML = `<div class="card card-body text-center"><div class="spinner-border spinner-border-sm"></div></div>`;

        const API_URL = `/api/recommendations/diet/?date=${dateStr}&meal_type=${mealType}`;
        try {
            const response = await fetch(API_URL, { credentials: 'include' });
            const result = await response.json();

            if (result.status === 'info') {
                // 处理“热量已达标”等提示信息
                container.innerHTML = `<div class="card card-body text-center text-muted">${result.message}</div>`;
                return;
            }

            if (result.status !== 'success') throw new Error(result.message);

            renderRecommendation(result.recommendations);

        } catch (error) {
            console.error('获取饮食推荐失败:', error);
            container.innerHTML = `<div class="card card-body text-center text-danger small">推荐加载失败</div>`;
        }
    }

    /**
     * ✨ [新增] 渲染推荐套餐的辅助函数
     * @param {Array} recommendations - 推荐套餐数组
     */
    function renderRecommendation(recommendations) {
        const container = document.getElementById('recommendation-container');
        if (!container || recommendations.length === 0) {
            container.innerHTML = `<div class="card card-body text-center text-muted">暂无推荐</div>`;
            return;
        }

        // 我们只展示第一个推荐套餐
        const a_recommendation = recommendations[0]
        
        const itemsHtml = a_recommendation.items.map(item => `
            <li class="list-group-item d-flex justify-content-between">
                <span>${item.name}</span>
                <span class="text-muted">${item.portion_g}g</span>
            </li>
        `).join('');

        container.innerHTML = `
            <div class="card">
                <div class="card-header bg-success-subtle">
                    <strong>${a_recommendation.title}</strong>
                </div>
                <ul class="list-group list-group-flush">
                    ${itemsHtml}
                </ul>
                <div class="card-footer text-muted small">
                    <div>总热量: <strong>${a_recommendation.total_calories.toFixed(0)} 大卡</strong></div>
                    <div class="mt-1">
                        <span class="me-2">蛋白质: ${a_recommendation.total_macros.protein.toFixed(1)}g</span>
                        <span class="me-2">| 碳水: ${a_recommendation.total_macros.carbs.toFixed(1)}g</span>
                        <span>| 脂肪: ${a_recommendation.total_macros.fat.toFixed(1)}g</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    // 辅助函数：渲染餐次列表
    function renderMeals(meals) {
        dietDetailsContainer.innerHTML = '';

        if (meals.length === 0) {
            dietDetailsContainer.innerHTML = '<p class="text-center text-muted">当日暂无饮食记录</p>';
            return;
        }

        const mealTypes = { breakfast: '早餐', lunch: '午餐', dinner: '晚餐', snack: '加餐/零食' };
        
        for (const meal of meals) {
            const card = document.createElement('div');
            card.className = 'card mb-3';
            
            let mealItemsHtml = '';
            if (meal.meal_items.length > 0) {
                mealItemsHtml = meal.meal_items.map(item => `
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <div>${item.food_item_name} <span class="text-muted">(${item.portion}克)</span></div>
                        <div>
                            <span class="badge bg-primary rounded-pill me-2">${item.calories_calculated.toFixed(0)} 大卡</span>
                            <button class="btn btn-sm btn-outline-secondary me-1" data-bs-toggle="modal" data-bs-target="#editMealItemModal" data-item-id="${item.id}" data-food-name="${item.food_item_name}" data-portion="${item.portion}">修改</button>
                            <button class="btn btn-sm btn-outline-danger" onclick="handleDeleteItem(${item.id})">删除</button>
                        </div>
                    </li>
                `).join('');
            } else {
                mealItemsHtml = '<li class="list-group-item text-muted">暂无食物</li>';
            }

            card.innerHTML = `
                <div class="card-header d-flex justify-content-between">
                    <strong>${mealTypes[meal.meal_type]  || '未知餐次'}</strong>
                    <strong>总计: ${meal.total_calories.toFixed(0)} 大卡</strong>
                </div>
                <ul class="list-group list-group-flush">${mealItemsHtml}</ul>
            `;
            dietDetailsContainer.appendChild(card);
        }
    }

    // 辅助函数：更新总热量
    function updateTotalCalories(meals) {
        const totalCalories = meals.reduce((sum, meal) => sum + meal.total_calories, 0);
        if (totalCaloriesEl) {
            totalCaloriesEl.textContent = totalCalories.toFixed(0);
        }
    }

    /**
     * 处理删除餐品条目的请求
     */
    async function handleDeleteItem(itemId) {
        if (!confirm('您确定要删除这条食物记录吗？')) return;
        const url = `${API_MEAL_ITEMS_URL}${itemId}/`;
        try {
            const response = await fetch(url, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCsrfToken() },
                credentials: 'include',
            });
            if (!response.ok) throw new Error('删除失败');
            
            // ✨ 刷新当前正在查看的日期的数据 ✨
            await fetchAndRenderMeals(dateSelector.value);
        } catch (error) {
            console.error('删除食物记录失败:', error);
            alert(`删除失败: ${error.message}`);
        }
    }
    window.handleDeleteItem = handleDeleteItem;

    /**
     *  处理修改表单的提交事件
     */
    async function handleEditFormSubmit(event) {
        event.preventDefault();
        const itemId = document.getElementById('edit-item-id').value;
        const newPortion = document.getElementById('edit-portion').value;
        if (!itemId || !newPortion || parseFloat(newPortion) <= 0) return;

        const url = `${API_MEAL_ITEMS_URL}${itemId}/`;
        const data = { portion: parseFloat(newPortion) };
        try {
            const response = await fetch(url, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                credentials: 'include',
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error('修改失败');

            const modalEl = document.getElementById('editMealItemModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
            
            await fetchAndRenderMeals(dateSelector.value);
        } catch (error) {
            console.error('修改食物记录失败:', error);
            alert(`修改失败: ${error.message}`);
        }
    }

    /**
     *  处理主表单提交（添加新食物）
     */
    async function handleFormSubmit(event) {
        event.preventDefault();

        const mealType = document.getElementById('meal-type').value;
        const foodName = document.getElementById('food-item').value;
        const portion = document.getElementById('portion').value;
        let foodId = null;
        const options = foodDatalist.querySelectorAll('option');
        for (const option of options) {
            if (option.value === foodName) {
                foodId = option.dataset.id;
                break;
            }
        }
        if (!foodId) {
            alert('请从列表中选择一个有效的食物！');
            return;
        }

        const recordDate = dateSelector.value;
        if (!recordDate) {
            alert('请先选择一个日期！');
            return;
        }
        
        try {
            let mealId = await getOrCreateMeal(recordDate, mealType);
            const mealItemData = {
                meal: mealId,
                food_item: parseInt(foodId, 10),
                portion: parseFloat(portion)
            };

            const response = await fetch(API_MEAL_ITEMS_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                credentials: 'include',
                body: JSON.stringify(mealItemData)
            });
            if (!response.ok) throw new Error('添加食物失败');
            
            dietForm.reset();
            await fetchAndRenderMeals(recordDate);
        } catch (error) {
            console.error('提交饮食记录失败:', error);
            alert(`提交失败: ${error.message}`);
        }
    }

    // 辅助函数：获取或创建餐次ID
    async function getOrCreateMeal(dateStr, mealType) {
        const checkUrl = `${API_MEALS_URL}?record_date=${dateStr}&meal_type=${mealType}`;
        let response = await fetch(checkUrl, { credentials: 'include' });
        let existingMeals = await response.json();
        if (existingMeals.length > 0) {
            return existingMeals[0].id;
        } else {
            const mealData = { record_date: dateStr, meal_type: mealType };
            response = await fetch(API_MEALS_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                credentials: 'include',
                body: JSON.stringify(mealData)
            });
            if (!response.ok) throw new Error('创建餐次失败');
            const newMeal = await response.json();
            return newMeal.id;
        }
    }

    // --- 3. 初始化和事件绑定 ---

    /**
     * 初始化页面
     */
    function initializePage() {
        // (假设 getFormattedDate 是在 global.js 中定义的全局函数)
        const todayStr = getFormattedDate(new Date());
        
        // 1. 设置日期选择器的默认值为今天
        dateSelector.value = todayStr;

        // 2. 并行加载初始数据（食物库和今天的数据）
        Promise.all([
            fetchAndPopulateFoodItems(),
            fetchAndRenderMeals(todayStr)
        ]);

        // 3. 监听日期选择器的变化
        dateSelector.addEventListener('change', function() {
            const selectedDate = this.value;
            if (selectedDate) {
                fetchAndRenderMeals(selectedDate);
            }
        });

        // 4. 绑定表单和模态框的事件监听
        dietForm.addEventListener('submit', handleFormSubmit);
        const editModalEl = document.getElementById('editMealItemModal');
        const editForm = document.getElementById('edit-meal-item-form');
        if (editModalEl && editForm) {
            editModalEl.addEventListener('show.bs.modal', function (event) {
                const button = event.relatedTarget;
                const itemId = button.dataset.itemId;
                const foodName = button.dataset.foodName;
                const portion = button.dataset.portion;
                document.getElementById('edit-item-id').value = itemId;
                document.getElementById('edit-food-name').value = foodName;
                document.getElementById('edit-portion').value = portion;
            });
            editForm.addEventListener('submit', handleEditFormSubmit);
        }
    }

    // 启动！
    initializePage();
});