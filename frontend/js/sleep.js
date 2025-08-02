// frontend/js/sleep.js

document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. 定义常量和获取DOM元素 ---
    const sleepForm = document.getElementById('sleep-form');
    const sleepDurationDisplay = document.getElementById('sleep-duration-display');
    const sleepRangeDisplay = document.getElementById('sleep-range-display');
    const sleepRecordModalEl = document.getElementById('sleepRecordModal');
    // 使用Bootstrap的官方方式获取模态框实例，方便用JS控制
    const sleepRecordModal = new bootstrap.Modal(sleepRecordModalEl);

    // API的URL
    const API_SLEEP_URL = '/api/sleep/';

    // --- 2. 核心功能函数 ---

    // 函数：获取并渲染睡眠记录
    async function fetchAndRenderSleep(dateStr) {
        // 睡眠记录是“跨天”的，API按起床日期筛选
        const url = `${API_SLEEP_URL}?record_date=${dateStr}`;
        
        try {
            const response = await fetch(url, { credentials: 'include' });
            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    alert('请先登录！');
                    window.location.href = '/login/';
                    return;
                }
                throw new Error('获取睡眠数据失败');
            }
            
            const sleepRecords = await response.json();
            
            // 通常一天只有一条睡眠记录，我们取第一条
            const todaySleepRecord = sleepRecords.length > 0 ? sleepRecords[0] : null;

            // 渲染UI
            renderSleepData(todaySleepRecord);

        } catch (error) {
            console.error(error);
            sleepDurationDisplay.textContent = '加载失败';
            sleepRangeDisplay.textContent = error.message;
        }
    }

    // 辅助函数：渲染睡眠数据到UI
    function renderSleepData(record) {
        if (record) {
            // 如果有记录
            // 后端返回的 duration 是 "HH:MM:SS" 格式，我们简化一下
            const durationParts = record.duration.split(':');
            const hours = parseInt(durationParts[0], 10);
            const minutes = parseInt(durationParts[1], 10);
            sleepDurationDisplay.textContent = `${hours}h ${minutes}m`;

            const sleepTime = new Date(record.sleep_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
            const wakeupTime = new Date(record.wakeup_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
            sleepRangeDisplay.textContent = `${sleepTime} - ${wakeupTime}`;
            
            // 把记录ID存到表单上，方便“修改”
            sleepForm.dataset.editingId = record.id;
        } else {
            // 如果没有记录
            sleepDurationDisplay.textContent = '-- 小时';
            sleepRangeDisplay.textContent = '未记录';
            // 确保没有残留的编辑ID
            sleepForm.removeAttribute('data-editing-id');
        }
    }

    // 函数：处理表单提交
    async function handleFormSubmit(event) {
        event.preventDefault();

        // 1. 从表单获取数据
        const sleepTimeInput = document.getElementById('sleep-time').value;
        const wakeupTimeInput = document.getElementById('wakeup-time').value;

        if (!sleepTimeInput || !wakeupTimeInput) {
            alert('请填写入睡和起床时间！');
            return;
        }
        
        // 2. 构建要发送到API的JSON数据
        const submitData = {
            sleep_time: sleepTimeInput,
            wakeup_time: wakeupTimeInput,
        };
        
        // 3. 判断是新建模式还是编辑模式
        const editingId = sleepForm.dataset.editingId;
        const isEditing = !!editingId;

        const url = isEditing ? `${API_SLEEP_URL}${editingId}/` : API_SLEEP_URL;
        const method = isEditing ? 'PUT' : 'POST';

        const submitButton = sleepForm.closest('.modal-content').querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.textContent = '正在保存...';

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
            
            // 4. 操作成功后，关闭模态框并刷新数据
            sleepRecordModal.hide(); // 关闭模态框
            const message = isEditing ? '记录更新成功！' : '记录添加成功！';
            alert(message);
            
            // 获取今天的日期并重新加载数据
            const today = new Date();
            const year = today.getFullYear();
            const month = String(today.getMonth() + 1).padStart(2, '0');
            const day = String(today.getDate()).padStart(2, '0');
            const todayStr = `${year}-${month}-${day}`;
            await fetchAndRenderSleep(todayStr);

        } catch (error) {
            console.error('操作记录失败:', error);
            alert(`操作失败: ${error.message}`);
        } finally {
            // 5. 重置表单状态
            submitButton.disabled = false;
            // 模态框标题和按钮文字可以在“编辑”时修改，这里恢复
            document.getElementById('sleepRecordModalLabel').textContent = '记录你的睡眠';
            submitButton.textContent = '保存记录';
        }
    }
    
    // ✨ 新增：处理模态框打开前的逻辑 ✨
    //    用于判断是“添加”还是“修改”，并预填充表单
    async function handleModalOpen() {
        const editingId = sleepForm.dataset.editingId;
        const modalTitle = document.getElementById('sleepRecordModalLabel');
        const submitButton = sleepForm.closest('.modal-content').querySelector('button[type="submit"]');

        if (editingId) {
            // --- 编辑模式 ---
            modalTitle.textContent = '修改睡眠记录';
            submitButton.textContent = '更新记录';
            
            // 获取该条记录的详细数据来填充表单
            const url = `${API_SLEEP_URL}${editingId}/`;
            const response = await fetch(url, { credentials: 'include' });
            const record = await response.json();

            // 将ISO格式的日期时间转换为 <input type="datetime-local"> 需要的格式
            const formatDateTimeLocal = (isoString) => {
                const date = new Date(isoString);
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                const hours = String(date.getHours()).padStart(2, '0');
                const minutes = String(date.getMinutes()).padStart(2, '0');

                // 拼接成 "YYYY-MM-DDTHH:MM" 格式
                return `${year}-${month}-${day}T${hours}:${minutes}`;
            };
            
            document.getElementById('sleep-time').value = formatDateTimeLocal(record.sleep_time);
            document.getElementById('wakeup-time').value = formatDateTimeLocal(record.wakeup_time);

        } else {
            // --- 添加模式 ---
            modalTitle.textContent = '添加睡眠记录';
            submitButton.textContent = '保存记录';
            sleepForm.reset(); // 清空表单
        }
    }

    // --- 3. 初始化和事件绑定 ---
    function initializePage() {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const todayStr = `${year}-${month}-${day}`;
        
        fetchAndRenderSleep(todayStr);

        if (sleepForm) {
            sleepForm.addEventListener('submit', handleFormSubmit);
        }
        
        // 监听模态框的 'show.bs.modal' 事件
        sleepRecordModalEl.addEventListener('show.bs.modal', handleModalOpen);
    }

    // 启动！
    initializePage();
});