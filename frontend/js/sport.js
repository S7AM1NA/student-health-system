// frontend/js/sport.js

document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. 定义常量和获取DOM元素 ---
    const sportForm = document.getElementById('sport-form');
    const sportListEl = document.getElementById('sport-list');
    const totalCaloriesEl = document.getElementById('total-calories-display');

    // API的URL
    const API_SPORTS_URL = '/api/sports/';

    // --- 2. 核心功能函数 ---

    // 函数：获取并渲染运动记录
    async function fetchAndRenderSports(dateStr) {
        // 构造带日期查询参数的URL
        const url = `${API_SPORTS_URL}?record_date=${dateStr}`;
        
        try {
            const response = await fetch(url, { credentials: 'include' });
            if (!response.ok) {
                // 如果是401/403，跳转到登录页
                if (response.status === 401 || response.status === 403) {
                    alert('请先登录！');
                    window.location.href = '/login/';
                    return;
                }
                throw new Error('获取运动数据失败');
            }
            
            const sports = await response.json(); // sports 是一个包含当天记录的数组

            // 渲染列表和总热量
            renderSportList(sports);
            updateTotalCalories(sports);

        } catch (error) {
            console.error(error);
            sportListEl.innerHTML = `<li class="list-group-item text-danger">数据加载失败: ${error.message}</li>`;
        }
    }

    // 辅助函数：渲染运动列表
    function renderSportList(sports) {
        sportListEl.innerHTML = ''; // 清空现有列表

        if (sports.length === 0) {
            sportListEl.innerHTML = '<li class="list-group-item text-center text-muted">当日暂无运动记录</li>';
            return;
        }

        sports.forEach(sport => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';
            li.dataset.id = sport.id; // 把记录ID存到li上，方便以后删除
            
            li.innerHTML = `
                <span>
                    <strong>${sport.sport_type}</strong> - ${sport.duration_minutes}分钟
                    <small class="text-muted">(${sport.calories_burned.toFixed(1)} 大卡)</small>
                </span>
                
                <div>
                    <button class="btn btn-sm btn-outline-secondary me-2 edit-btn">编辑</button>
                    <button class="btn btn-sm btn-outline-danger delete-btn">删除</button>
                </div>
            `;
            sportListEl.appendChild(li);
        });
    }

    // 辅助函数：更新总热量
    function updateTotalCalories(sports) {
        const totalCalories = sports.reduce((sum, sport) => sum + sport.calories_burned, 0);
        if (totalCaloriesEl) {
            totalCaloriesEl.textContent = totalCalories.toFixed(1);
        }
    }

    // 函数：处理表单提交 [最终版本 - 总是全局刷新UI]
    async function handleFormSubmit(event) {
        event.preventDefault(); // 阻止表单默认的刷新页面的行为

        // 1. 从表单获取数据
        const sportTypeInput = document.getElementById('sport-type');
        const durationInput = document.getElementById('duration');
        const caloriesInput = document.getElementById('calories');
        
        // 基本的客户端验证
        if (!sportTypeInput.value || !durationInput.value || !caloriesInput.value) {
            alert('请填写所有字段！');
            return;
        }

        // TODO: 未来可以让用户选择日期来添加/修改历史记录
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const recordDate = `${year}-${month}-${day}`;

        // 2. 构建要发送到API的JSON数据
        const submitData = {
            sport_type: sportTypeInput.value,
            duration_minutes: parseInt(durationInput.value, 10),
            calories_burned: parseFloat(caloriesInput.value),
            record_date: recordDate,
        };
        
        // 3. 判断是新建模式还是编辑模式
        const editingId = sportForm.dataset.editingId;
        const isEditing = !!editingId;

        const url = isEditing ? `${API_SPORTS_URL}${editingId}/` : API_SPORTS_URL;
        const method = isEditing ? 'PUT' : 'POST';

        // ✨ 新增：在提交前禁用按钮，防止重复提交
        const submitButton = sportForm.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.textContent = isEditing ? '正在更新...' : '正在添加...';


        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                credentials: 'include',
                body: JSON.stringify(submitData),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(JSON.stringify(errorData.detail || errorData || '未知错误'));
            }

            // 4. ✨ 核心修改：操作成功后，不再进行复杂的局部UI更新 ✨
            const message = isEditing ? '记录更新成功！' : '记录添加成功！';
            alert(message);

            // 调用主渲染函数来刷新整个列表和总数，保证数据绝对一致
            await fetchAndRenderSports(recordDate);

        } catch (error) {
            console.error('操作记录失败:', error);
            alert(`操作失败: ${error.message}`);
        } finally {
            // 5. 重置表单状态，并重新启用按钮
            sportForm.reset();
            sportForm.removeAttribute('data-editing-id');
            submitButton.disabled = false;
            submitButton.textContent = '添加记录';
        }
    }

    async function handleDelete(recordId, listItemElement) {
        if (!confirm('您确定要删除这条记录吗？')) {
            return; // 用户取消了操作
        }

        const url = `${API_SPORTS_URL}${recordId}/`;

        try {
            const response = await fetch(url, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                },
                credentials: 'include',
            });

            // DELETE 请求成功时，后端通常返回 204 No Content
            if (response.status === 204) {
                // 1. 从UI上移除这一项
                listItemElement.remove();
                
                // 2. ✨ 重新计算并更新总卡路里 ✨
                //    一个简单的方法是重新获取所有显示的li，然后计算
                const allItems = Array.from(sportListEl.querySelectorAll('li'));
                const sportsData = allItems.map(item => {
                    // 从HTML中解析出数据，这有点脆弱，更好的方式是在删除成功后重新fetch
                    const text = item.querySelector('small').textContent;
                    const calories = parseFloat(text.match(/(\d+\.?\d*)/)[0]);
                    return { calories_burned: calories };
                });
                updateTotalCalories(sportsData);
                
            } else {
                const errorData = await response.json();
                throw new Error(JSON.stringify(errorData));
            }
        } catch (error) {
            console.error('删除失败:', error);
            alert(`删除失败: ${error.message}`);
        }
    }

    async function handleEdit(recordId) {
        // 1. 根据ID获取这条记录的详细数据
        const url = `${API_SPORTS_URL}${recordId}/`;
        try {
            const response = await fetch(url, { credentials: 'include' });
            const recordData = await response.json();
            
            // 2. 将数据填充到左侧的表单中
            document.getElementById('sport-type').value = recordData.sport_type;
            document.getElementById('duration').value = recordData.duration_minutes;
            document.getElementById('calories').value = recordData.calories_burned;
            
            // 3. ✨ 改变表单的行为 ✨
            //    - 我们可以改变按钮的文字为“更新记录”
            //    - 最重要的是，我们需要一个地方暂存正在编辑的记录ID
            const submitButton = sportForm.querySelector('button[type="submit"]');
            submitButton.textContent = '更新记录';
            sportForm.dataset.editingId = recordId; // 把ID存到form的dataset上

            // (可选) 滚动到页面顶部，让用户能看到表单
            window.scrollTo(0, 0);

        } catch (error) {
            console.error('获取待编辑数据失败:', error);
            alert('无法加载记录，请重试。');
        }
    }

    // 辅助函数：在列表顶部添加一个运动项
    function addSportToList(sport) {
        // 如果列表是“暂无记录”状态，先清空
        if (sportListEl.querySelector('.text-muted')) {
            sportListEl.innerHTML = '';
        }

        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        li.dataset.id = sport.id;

        li.innerHTML = `
            <span>
                <strong>${sport.sport_type}</strong> - ${sport.duration_minutes}分钟
                <small class="text-muted">(${sport.calories_burned.toFixed(1)} 大卡)</small>
            </span>
            
            <div>
                <button class="btn btn-sm btn-outline-secondary me-2 edit-btn">编辑</button>
                <button class="btn btn-sm btn-outline-danger delete-btn">删除</button>
            </div>
        `;
        // 使用 prepend 可以在列表最上方添加
        sportListEl.prepend(li);
    }


    // --- 3. 初始化和事件绑定 ---
    
    // 初始化页面
    function initializePage() {
        // 获取今天的日期 (未来可以从URL参数或一个全局状态获取)
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const todayStr = `${year}-${month}-${day}`;
        
        // 页面加载时，获取并渲染今天的数据
        fetchAndRenderSports(todayStr);

        // 绑定表单提交事件
        // sportForm.addEventListener('submit', handleFormSubmit);
        console.log('获取到的sportForm元素是:', sportForm);
        if (sportForm) { // ✨ 加上安全检查 ✨
            sportForm.addEventListener('submit', handleFormSubmit);
            sportListEl.addEventListener('click', function(event) {
                const target = event.target;

                // ✨ 诊断点1：打印出被点击的元素 ✨
                console.log('列表被点击，点击的元素是:', target);

                if (target.classList.contains('delete-btn')) {
                    console.log('删除按钮被点击');
                    const listItem = target.closest('li');
                    if (listItem) {
                        const recordId = listItem.dataset.id;
                        handleDelete(recordId, listItem);
                    }
                } else if (target.classList.contains('edit-btn')) {
                    // ✨ 诊断点2：确认是否进入了编辑逻辑 ✨
                    console.log('编辑按钮被点击');
                    const listItem = target.closest('li');
                    if (listItem) {
                        const recordId = listItem.dataset.id;
                        console.log('准备编辑的记录ID是:', recordId); // ✨ 诊断点3
                        handleEdit(recordId);
                    }
                }
            });
        } else {
            console.error('致命错误：无法在HTML中找到id为 "sport-form" 的元素！');
        }
    }

    // 启动！
    initializePage();

});