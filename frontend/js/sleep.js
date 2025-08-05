document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. 定义常量和获取DOM元素 ---
    const sleepForm = document.getElementById('sleep-form');
    const sleepDurationDisplay = document.getElementById('sleep-duration-display');
    const sleepRangeDisplay = document.getElementById('sleep-range-display');
    const sleepRecordModalEl = document.getElementById('sleepRecordModal');
    const sleepRecordModal = new bootstrap.Modal(sleepRecordModalEl);

    // 获取新的操作按钮
    const addSleepBtn = document.getElementById('add-sleep-btn');
    const editSleepBtn = document.getElementById('edit-sleep-btn');

    const dateSelector = document.getElementById('date-selector');
    const displayDateEl = document.getElementById('display-date');

    // API的URL
    const API_SLEEP_URL = '/api/sleep/';

    // --- 2. 核心功能函数 ---

    /**
     * @param {string} dateStr - 'YYYY-MM-DD'格式的日期
     */
    async function fetchAndRenderSleep(dateStr) {
        // 更新UI上的日期显示
        displayDateEl.textContent = dateStr;
        sleepDurationDisplay.innerHTML = `<div class="spinner-border spinner-border-sm"></div>`;
        sleepRangeDisplay.textContent = '加载中...';

        const url = `${API_SLEEP_URL}?record_date=${dateStr}`;
        try {
            const response = await fetch(url, { credentials: 'include' });
            if (!response.ok) throw new Error('获取睡眠数据失败');
            const sleepRecords = await response.json();
            const record = sleepRecords.length > 0 ? sleepRecords[0] : null;
            renderSleepData(record);
        } catch (error) {
            console.error(error);
            sleepDurationDisplay.textContent = '加载失败';
            sleepRangeDisplay.textContent = error.message;
            // 确保出错时也隐藏修改按钮
            editSleepBtn.classList.add('d-none');
        }
    }

    /**
     * 根据记录数据更新UI
     * @param {object|null} record - 睡眠记录对象或null
     */
    function renderSleepData(record) {
        if (record) {
            const durationParts = record.duration.split(':');
            const hours = parseInt(durationParts[0], 10);
            const minutes = parseInt(durationParts[1], 10);
            sleepDurationDisplay.textContent = `${hours}h ${minutes}m`;

            const sleepTime = new Date(record.sleep_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
            const wakeupTime = new Date(record.wakeup_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
            sleepRangeDisplay.textContent = `${sleepTime} - ${wakeupTime}`;
            
            // 将记录ID存到“修改”按钮上，并显示它
            editSleepBtn.dataset.editingId = record.id;
            editSleepBtn.classList.remove('d-none');
        } else {
            sleepDurationDisplay.textContent = '-- 小时';
            sleepRangeDisplay.textContent = '未记录';

            // 确保没有残留的编辑ID，并隐藏“修改”按钮
            editSleepBtn.removeAttribute('data-editing-id');
            editSleepBtn.classList.add('d-none');
        }
    }

    /**
     * 处理表单提交（新增或修改）
     * @param {Event} event - 表单提交事件
     */
    async function handleFormSubmit(event) {
        event.preventDefault();

        const sleepTimeInput = document.getElementById('sleep-time').value;
        const wakeupTimeInput = document.getElementById('wakeup-time').value;

        if (!sleepTimeInput || !wakeupTimeInput) {
            alert('请填写入睡和起床时间！');
            return;
        }
        
        const submitData = {
            sleep_time: sleepTimeInput,
            wakeup_time: wakeupTimeInput,
        };
        
        // 从模态框内部的隐藏input获取ID，决定是新增还是修改
        const editingId = document.getElementById('editing-id-input').value;
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

            const updatedRecord = await response.json();

            if (!response.ok) {
                throw new Error(JSON.stringify(updatedRecord.detail || updatedRecord || '未知错误'));
            }
            
            sleepRecordModal.hide();
            const message = isEditing ? '记录更新成功！' : '记录添加成功！';
            alert(message);
            
            const recordWakeupDate = new Date(updatedRecord.wakeup_time);
            const recordWakeupDateStr = getFormattedDate(recordWakeupDate);
            
            await fetchAndRenderSleep(dateSelector.value);
            
            const todayStr = getFormattedDate(new Date());
            await loadWeeklySleepChart(todayStr);

        } catch (error) {
            console.error('操作记录失败:', error);
            alert(`操作失败: ${error.message}`);
        } finally {
            submitButton.disabled = false;
        }
    }
    
    /**
     * 处理模态框打开事件，根据触发按钮决定是“添加”还是“修改”模式
     * @param {Event} event - Bootstrap模态框事件
     */
    function handleModalOpen(event) {
        const button = event.relatedTarget; // 获取触发模态框的按钮
        const modalTitle = document.getElementById('sleepRecordModalLabel');
        const submitButton = sleepForm.closest('.modal-content').querySelector('button[type="submit"]');
        const editingIdInput = document.getElementById('editing-id-input');
        
        sleepForm.reset(); // 每次打开都先清空表单

        if (button && button.id === 'edit-sleep-btn') {
            // --- 编辑模式 ---
            const editingId = button.dataset.editingId;
            modalTitle.textContent = '修改睡眠记录';
            submitButton.textContent = '更新记录';
            editingIdInput.value = editingId;
            
            // 异步获取数据并填充表单
            fillFormForEditing(editingId);
        } else {
            // --- 添加模式 ---
            modalTitle.textContent = '添加新记录';
            submitButton.textContent = '保存记录';
            editingIdInput.value = ''; // 确保隐藏ID为空
        }
    }

    /**
     * 异步获取单条记录详情并填充到编辑表单中
     * @param {string} recordId - 记录的ID
     */
    async function fillFormForEditing(recordId) {
        try {
            const url = `${API_SLEEP_URL}${recordId}/`;
            const response = await fetch(url, { credentials: 'include' });
            if (!response.ok) throw new Error('获取记录详情失败');
            const record = await response.json();
            
            const formatDateTimeLocal = (isoString) => {
                if (!isoString) return '';
                // 增加时区偏移处理，确保显示的是本地时间
                const date = new Date(isoString);
                date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
                return date.toISOString().slice(0, 16);
            };
            
            document.getElementById('sleep-time').value = formatDateTimeLocal(record.sleep_time);
            document.getElementById('wakeup-time').value = formatDateTimeLocal(record.wakeup_time);
        } catch (error) {
            console.error('获取待编辑数据失败:', error);
            alert('无法加载记录详情，请重试。');
            sleepRecordModal.hide();
        }
    }
    
    /**
     * [从report.js迁移过来] 获取并渲染周度睡眠图表
     * @param {string} endDateStr - 报告周期的结束日期
     */
    async function loadWeeklySleepChart(endDateStr) {
        const API_URL = `/api/reports/weekly-sleep/${endDateStr}/`;
        try {
            const response = await fetch(API_URL, { credentials: 'include' });
            const result = await response.json();
            if (result.status !== 'success') throw new Error(result.message);
            
            const reportData = result.data;
            const labels = reportData.map(item => {
                const parts = item.date.split('-');
                const month = parseInt(parts[1], 10); // 月份
                const day = parseInt(parts[2], 10);   // 日期
                return `${month}-${day}`;
            });
            const data = reportData.map(item => item.duration_hours);
            renderSleepChart(labels, data);
        } catch (error) {
            console.error('加载睡眠图表失败:', error);
        }
    }

    /**
     * [从report.js迁移过来] 使用Chart.js渲染睡眠图表
     * @param {string[]} labels - X轴的标签 (日期)
     * @param {number[]} data - Y轴的数据 (睡眠时长)
     */
    function renderSleepChart(labels, data) {
        const ctx = document.getElementById('sleep-chart').getContext('2d');
        if (window.mySleepChart instanceof Chart) {
            window.mySleepChart.destroy();
        }
        window.mySleepChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '睡眠时长 (小时)',
                    data: data,
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: '小时' } }
                },
                responsive: true,
                maintainAspectRatio: false,
            }
        });
    }

    async function loadHealthSummaryReport(startDate, endDate) {
        const API_URL = `/api/reports/health-summary/?start_date=${startDate}&end_date=${endDate}`;
        const reportContainer = document.getElementById('health-report-container');
        const sleepSummaryContainer = document.getElementById('sleep-summary-container');
        
        try {
            const response = await fetch(API_URL, { credentials: 'include' });
            const result = await response.json();

            if (result.status !== 'success') throw new Error(result.message);

            const report = result.report;
            
            // ✨ 渲染睡眠摘要 ✨
            renderSleepSummary(report.sleep_analysis);

        } catch (error) {
            console.error('加载综合报告失败:', error);
            if(reportContainer) reportContainer.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
            if(sleepSummaryContainer) sleepSummaryContainer.innerHTML = `<div class="alert alert-warning">数据不足</div>`;
        }
    }

    function renderSleepSummary(sleepData) {
        const container = document.getElementById('sleep-summary-container');
        if (!container) return;

        container.innerHTML = `
            <h5 class="mb-3">数据摘要</h5>
            <ul class="list-group list-group-flush">
                <li class="list-group-item d-flex justify-content-between">
                    <span>健康得分</span>
                    <strong class="text-primary">${sleepData.score}/100</strong>
                </li>
                <li class="list-group-item d-flex justify-content-between">
                    <span>平均睡眠</span>
                    <strong>${sleepData.average_duration_hours.toFixed(1)} 小时</strong>
                </li>
                <li class="list-group-item d-flex justify-content-between">
                    <span>作息规律性</span>
                    <span class="badge bg-info">${sleepData.consistency.comment}</span>
                </li>
                <li class="list-group-item d-flex justify-content-between">
                    <span>记录覆盖率</span>
                    <strong>${sleepData.data_coverage_percent}%</strong>
                </li>
            </ul>
            <h6 class="mt-4">智能建议:</h6>
            <p class="text-muted small">${sleepData.suggestions.join(' ')}</p>
        `;
    }

    // --- 3. 初始化和事件绑定 ---
    function initializePage() {
        const today = new Date();
        const todayStr = getFormattedDate(today);

        // 1. 设置日期选择器的默认值为今天
        dateSelector.value = todayStr;

        // 2. 页面首次加载时，获取并渲染今天的数据
        fetchAndRenderSleep(todayStr);

        // 3. ✨ 周度报告和图表，始终基于今天的日期加载 ✨
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(today.getDate() - 6);
        const sevenDaysAgoStr = getFormattedDate(sevenDaysAgo);
        loadWeeklySleepChart(todayStr);
        loadHealthSummaryReport(sevenDaysAgoStr, todayStr);

        // 4. 监听日期选择器的变化
        dateSelector.addEventListener('change', function() {
            const selectedDate = this.value;
            if (selectedDate) {
                // ✨ 只刷新顶部的每日数据，不刷新下面的周度报告 ✨
                fetchAndRenderSleep(selectedDate);
            }
        });

        // 5. 绑定表单和模态框的事件监听（保持不变）
        if (sleepForm) {
            sleepForm.addEventListener('submit', handleFormSubmit);
        }
        sleepRecordModalEl.addEventListener('show.bs.modal', handleModalOpen);
    }

    // 启动！
    initializePage();
});