// frontend/js/diet.js

document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. 定义常量和获取DOM元素 ---
    const dietForm = document.getElementById('diet-form');
    const foodDatalist = document.getElementById('food-datalist');
    const dietDetailsContainer = document.getElementById('diet-details-container');
    const totalCaloriesEl = document.getElementById('total-calories-eaten-display');

    // API的URL
    const API_FOODS_URL = '/api/foods/';
    const API_MEALS_URL = '/api/meals/';
    const API_MEAL_ITEMS_URL = '/api/meal-items/';

    // --- 2. 核心功能函数 ---

    // 函数：获取食物库并填充datalist
    async function fetchAndPopulateFoodItems() {
        try {
            const response = await fetch(API_FOODS_URL, { credentials: 'include' });
            const foodItems = await response.json();
            
            foodDatalist.innerHTML = ''; // 清空
            foodItems.forEach(food => {
                const option = document.createElement('option');
                option.value = food.name;
                // 把食物ID和热量存到dataset里，方便以后使用
                option.dataset.id = food.id;
                option.dataset.calories = food.calories_per_100g;
                foodDatalist.appendChild(option);
            });
        } catch (error) {
            console.error('获取食物库失败:', error);
        }
    }

    // 函数：获取并渲染当天的餐次记录
    async function fetchAndRenderMeals(dateStr) {
        const url = `${API_MEALS_URL}?record_date=${dateStr}`;
        try {
            const response = await fetch(url, { credentials: 'include' });
            const meals = await response.json();
            
            renderMeals(meals);
            updateTotalCalories(meals);

        } catch (error) {
            console.error('获取餐次数据失败:', error);
            dietDetailsContainer.innerHTML = `<p class="text-danger">数据加载失败: ${error.message}</p>`;
        }
    }
    
    // 辅助函数：渲染餐次列表
    function renderMeals(meals) {
        dietDetailsContainer.innerHTML = ''; // 清空

        if (meals.length === 0) {
            dietDetailsContainer.innerHTML = '<p class="text-center text-muted">当日暂无饮食记录</p>';
            return;
        }

        const mealTypes = { breakfast: '早餐', lunch: '午餐', dinner: '晚餐', snack: '加餐/零食' };
        
        for (const meal of meals) {
            const card = document.createElement('div');
            card.className = 'card mb-3';
            
            // ✨ 修改点：为每个 MealItem 增加修改和删除按钮 ✨
            let mealItemsHtml = '';
            if (meal.meal_items.length > 0) {
                mealItemsHtml = meal.meal_items.map(item => `
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <div>
                            ${item.food_item_name} 
                            <span class="text-muted">(${item.portion}克)</span>
                        </div>
                        <div>
                            <span class="badge bg-primary rounded-pill me-2">${item.calories_calculated.toFixed(0)} 大卡</span>
                            
                            <!-- 修改按钮 -->
                            <button class="btn btn-sm btn-outline-secondary me-1" 
                                    data-bs-toggle="modal" 
                                    data-bs-target="#editMealItemModal"
                                    data-item-id="${item.id}"
                                    data-food-name="${item.food_item_name}"
                                    data-portion="${item.portion}">
                                修改
                            </button>
                            
                            <!-- 删除按钮 -->
                            <button class="btn btn-sm btn-outline-danger" 
                                    onclick="handleDeleteItem(${item.id})"> 
                                删除
                            </button>
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
                <ul class="list-group list-group-flush">
                    ${mealItemsHtml}
                </ul>
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
     * @param {number} itemId - 要删除的MealItem的ID
     */
    async function handleDeleteItem(itemId) {
        if (!confirm('您确定要删除这条食物记录吗？')) {
            return;
        }

        const url = `${API_MEAL_ITEMS_URL}${itemId}/`;
        try {
            const response = await fetch(url, {
                method: 'DELETE',
                headers: { 
                    'X-CSRFToken': getCsrfToken() //直接调用全局函数
                },
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error(`删除失败 (状态码: ${response.status})`);
            }
            
            console.log(`Item ${itemId} 删除成功`);
            
            // 刷新UI
            const todayStr = new Date().toISOString().split('T')[0];
            await fetchAndRenderMeals(todayStr);

        } catch (error) {
            console.error('删除食物记录失败:', error);
            alert(`删除失败: ${error.message}`);
        }
    }
    // 将函数挂载到window对象，以便HTML中的内联onclick可以调用它
    window.handleDeleteItem = handleDeleteItem;


    /**
     * 处理修改表单的提交事件
     * @param {Event} event - 表单提交事件
     */
    async function handleEditFormSubmit(event) {
        event.preventDefault();

        const itemId = document.getElementById('edit-item-id').value;
        const newPortion = document.getElementById('edit-portion').value;

        if (!itemId || !newPortion || parseFloat(newPortion) <= 0) {
            alert('请输入有效的份量！');
            return;
        }

        const url = `${API_MEAL_ITEMS_URL}${itemId}/`;
        const data = {
            portion: parseFloat(newPortion)
        };

        try {
            const response = await fetch(url, {
                method: 'PATCH',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken() //直接调用全局函数
                },
                credentials: 'include',
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(Object.values(errorData).join('\n') || '修改失败');
            }

            console.log(`Item ${itemId} 修改成功`);

            // 成功后，关闭模态框并刷新UI
            const modalEl = document.getElementById('editMealItemModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) {
                modal.hide();
            }
            
            const todayStr = new Date().toISOString().split('T')[0];
            await fetchAndRenderMeals(todayStr);

        } catch (error) {
            console.error('修改食物记录失败:', error);
            alert(`修改失败: ${error.message}`);
        }
    }

    async function handleFormSubmit(event) {
        event.preventDefault();

        // 1. 获取表单数据
        const mealType = document.getElementById('meal-type').value;
        const foodName = document.getElementById('food-item').value;
        const portion = document.getElementById('portion').value;
        
        // 从datalist中找到对应的食物ID
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

        // 获取当天日期
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const recordDate = `${year}-${month}-${day}`;
        
        // ✨ 核心逻辑：“两步走” ✨
        try {
            // 步骤一：获取或创建“餐次”(Meal)
            let mealId = await getOrCreateMeal(recordDate, mealType);

            // 步骤二：创建“餐品条目”(MealItem)
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
            
            // 成功后，刷新整个UI
            alert('食物添加成功！');
            dietForm.reset();
            await fetchAndRenderMeals(recordDate);

        } catch (error) {
            console.error('提交饮食记录失败:', error);
            alert(`提交失败: ${error.message}`);
        }
    }

    // 辅助函数：获取或创建餐次ID
    async function getOrCreateMeal(dateStr, mealType) {
        // 1. 直接向后端发起精确查询
        const checkUrl = `${API_MEALS_URL}?record_date=${dateStr}&meal_type=${mealType}`;
        let response = await fetch(checkUrl, { credentials: 'include' });
        let existingMeals = await response.json();

        // 后端现在能精确返回结果，所以 existingMeals 要么是 [mealObject]，要么是 []
        if (existingMeals.length > 0) {
            // 如果已存在，直接返回它的ID
            return existingMeals[0].id;
        } else {
            // 2. 如果不存在，就创建一个新的
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
    function initializePage() {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const todayStr = `${year}-${month}-${day}`;
        
        // 使用 Promise.all 并行加载初始数据
        Promise.all([
            fetchAndPopulateFoodItems(),
            fetchAndRenderMeals(todayStr)
        ]);

        // (表单提交逻辑稍后添加)
        dietForm.addEventListener('submit', handleFormSubmit);
        const editModalEl = document.getElementById('editMealItemModal');
        const editForm = document.getElementById('edit-meal-item-form');

        if (editModalEl && editForm) {
            // 监听模态框的显示事件，当它弹出时，自动填充数据
            editModalEl.addEventListener('show.bs.modal', function (event) {
                const button = event.relatedTarget; // 触发模态框的那个“修改”按钮
                
                // 从按钮的 data-* 属性中提取数据
                const itemId = button.dataset.itemId;
                const foodName = button.dataset.foodName;
                const portion = button.dataset.portion;

                // 获取模态框内的表单元素
                const modalItemIdInput = document.getElementById('edit-item-id');
                const modalFoodNameInput = document.getElementById('edit-food-name');
                const modalPortionInput = document.getElementById('edit-portion');
                
                // 将数据填充到模态框的表单里
                if(modalItemIdInput) modalItemIdInput.value = itemId;
                if(modalFoodNameInput) modalFoodNameInput.value = foodName;
                if(modalPortionInput) modalPortionInput.value = portion;
            });

            // 为修改表单绑定提交事件
            editForm.addEventListener('submit', handleEditFormSubmit);
        }
    }

    // 启动！
    initializePage();
});