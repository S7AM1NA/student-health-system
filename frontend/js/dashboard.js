// 使用 'DOMContentLoaded' 事件确保在HTML完全加载后再执行我们的JS代码
document.addEventListener('DOMContentLoaded', function () {

    // ===================================================================
    // 1. 定义常量
    // ===================================================================
    const API_BASE_URL = 'http://127.0.0.1:8000/api'; // 后端服务器的地址
    const dateSelector = document.getElementById('date-selector');

    // 获取当前日期并格式化为 YYYY-MM-DD
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0'); // 月份从0开始，所以+1
    const day = String(today.getDate()).padStart(2, '0');
    const todayDateStr = `${year}-${month}-${day}`;

    // 使用格式化后的日期字符串来构建最终的API URL
    const DASHBOARD_API_URL = `${API_BASE_URL}/dashboard/${todayDateStr}/`;


    // ===================================================================
    // 2. 获取所有需要操作的HTML元素 (我们的“工具箱”)
    // ===================================================================
    const usernameDisplay = document.getElementById('username-display');
    const todayDateDisplay = document.getElementById('today-date');

    const sleepDurationEl = document.getElementById('sleep-duration');
    const sleepTimeRangeEl = document.getElementById('sleep-time-range');

    const caloriesBurnedEl = document.getElementById('calories-burned');
    const sportDetailsEl = document.getElementById('sport-details');

    const caloriesEatenEl = document.getElementById('calories-eaten');
    const dietDetailsEl = document.getElementById('diet-details');

    const dietProgressBarEl = document.getElementById('diet-progress-bar');
    const dietProgressContainer = document.querySelector('.progress');

    const summarySection = document.getElementById('health-summary');
    const summarySuggestionEl = document.getElementById('summary-suggestion');

    // ===================================================================
    // 3. 定义一个函数来更新UI (我们的“室内设计师”)
    // ===================================================================
    function updateDashboardUI(apiResponse) {
        if (apiResponse.status === 'success') {
            const data = apiResponse.data;

            // 更新问候语和日期
            usernameDisplay.textContent = apiResponse.user.username;
            todayDateDisplay.textContent = data.date;

            // 更新睡眠卡片
            if (data.sleep.record_exists) {
                const sleepOptions = {
                    decimalPlaces: 1, // 保留一位小数
                    suffix: ' 小时'    // 在数字后面加上单位
                };
                // 修正点1：在CountUp前加上 countUp.
                const sleepCountUp = new countUp.CountUp(sleepDurationEl, data.sleep.duration_hours, sleepOptions);
                if (!sleepCountUp.error) {
                    sleepCountUp.start();
                } else {
                    console.error(sleepCountUp.error);
                    sleepDurationEl.textContent = `${data.sleep.duration_hours.toFixed(1)} 小时`;
                }
                const sleepTime = new Date(data.sleep.sleep_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
                const wakeupTime = new Date(data.sleep.wakeup_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
                sleepTimeRangeEl.textContent = `${sleepTime} - ${wakeupTime}`;
            } else {
                sleepDurationEl.textContent = '暂无记录';
                sleepTimeRangeEl.textContent = '一夜好眠，从记录开始';
            }

            // 更新运动卡片
            if (data.sports.record_exists) {
                // 修正点2：在CountUp前加上 countUp.
                const caloriesBurnedCountUp = new countUp.CountUp(caloriesBurnedEl, data.sports.total_calories_burned);
                if (!caloriesBurnedCountUp.error) {
                    caloriesBurnedCountUp.start();
                } else {
                    console.error(caloriesBurnedCountUp.error);
                    caloriesBurnedEl.textContent = data.sports.total_calories_burned;
                }
                sportDetailsEl.textContent = `共 ${data.sports.count} 次运动，总时长 ${data.sports.total_duration_minutes} 分钟`;
            } else {
                caloriesBurnedEl.textContent = '0';
                sportDetailsEl.textContent = '今天你运动了吗？';
            }

            // 更新饮食卡片
            if (data.diet.record_exists) {
                const dietProgressBarEl = document.getElementById('diet-progress-bar');
                const dietProgressContainer = dietProgressBarEl.parentElement;

                // 修正点3：在CountUp前加上 countUp.
                const caloriesEatenCountUp = new countUp.CountUp(caloriesEatenEl, data.diet.total_calories_eaten);
                if (!caloriesEatenCountUp.error) {
                    caloriesEatenCountUp.start();
                } else {
                    console.error(caloriesEatenCountUp.error);
                    caloriesEatenEl.textContent = data.diet.total_calories_eaten;
                }
                dietDetailsEl.textContent = '营养均衡，活力满满';

                const dietGoal = 2000;
                const progressPercentage = (data.diet.total_calories_eaten / dietGoal) * 100;

                dietProgressBarEl.style.width = `${Math.min(progressPercentage, 100)}%`;

                let progressColor = '#198754';
                if (progressPercentage > 90) {
                    progressColor = '#dc3545';
                } else if (progressPercentage > 70) {
                    progressColor = '#ffc107';
                }
                dietProgressBarEl.style.setProperty('--progress-color', progressColor);
                dietProgressContainer.setAttribute('aria-valuenow', data.diet.total_calories_eaten);
                dietProgressContainer.style.display = 'block';

            } else {
                const dietProgressContainer = document.querySelector('.progress');
                if (dietProgressContainer) {
                    dietProgressContainer.style.display = 'none';
                }

                caloriesEatenEl.textContent = '0';
                dietDetailsEl.textContent = '记录饮食，掌控健康';
            }

            // 更新健康小结
            summarySuggestionEl.textContent = data.health_summary.suggestion;
            const statusMap = {
                'BALANCED': 'alert-success',
                'HIGH_INTAKE': 'alert-warning',
                'LOW_INTAKE': 'alert-info',
                'NEUTRAL': 'alert-secondary'
            };
            summarySection.className = `mt-4 alert ${statusMap[data.health_summary.status_code] || 'alert-info'}`;

        } else {
            alert(`获取数据失败: ${apiResponse.message}`);
            if (apiResponse.error_code === 'AUTH_REQUIRED') {
                setTimeout(() => {
                    window.location.href = '/login.html';
                }, 3000);
            }
        }
    }

    // ===================================================================
    // 4. 定义主函数来发起API请求 (我们的“快递员”)
    // ===================================================================
    async function fetchDashboardData(dateStr) {
        // 1. 使用传入的日期字符串来构建API URL
        const DASHBOARD_API_URL = `${API_BASE_URL}/dashboard/${dateStr}/`;
        
        // 2. 显示一个加载中的状态
        document.body.style.cursor = 'wait';
        // 你可以更进一步，比如让卡片内容暂时模糊或显示一个加载动画
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => card.style.opacity = '0.5');


        try {
            // 3. 发起API请求，保留了 credentials: 'include'
            const response = await fetch(DASHBOARD_API_URL, { credentials: 'include' });
            const data = await response.json();

            // 4. 检查HTTP状态码
            if (response.status === 401 || response.status === 403) {
                updateDashboardUI({
                    status: 'error',
                    message: data.detail || '您需要登录才能访问此页面。',
                    error_code: 'AUTH_REQUIRED' // 明确错误类型
                });
            } else if (!response.ok) {
                // 5. 处理其他HTTP错误
                throw new Error(`HTTP错误! 状态码: ${response.status}, 消息: ${data.message || '未知服务器错误'}`);
            } else {
                // 6. 如果一切正常，调用UI更新函数
                updateDashboardUI(data);
            }

        } catch (error) {
            console.error('无法从服务器获取数据:', error);

            // 7. catch块错误处理
            const mainContent = document.querySelector('main');
            if (mainContent) {
                const summarySection = document.getElementById('health-summary');
                if(summarySection) {
                    summarySection.className = 'mt-4 alert alert-danger';
                    summarySection.innerHTML = `<h4 class="alert-heading">加载失败!</h4><p>${error.message}</p><p class="mb-0">请检查网络或稍后 <a href="#" onclick="event.preventDefault(); location.reload();">刷新页面</a> 重试。</p>`;
                } else {
                    mainContent.innerHTML = `<div class="alert alert-danger">...</div>`;
                }
            } else {
                alert(`加载失败: ${error.message}`);
            }
        } finally {
            // 8. 无论成功还是失败，都取消加载中状态
            document.body.style.cursor = 'default';
            cards.forEach(card => card.style.opacity = '1');
        }
    }

    function initializeDashboard() {
        // 1. 创建一个函数来获取并格式化日期
        const getFormattedDate = (date) => {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        };

        const today = new Date();
        const todayStr = getFormattedDate(today);

        // 2. 页面加载时，设置日期选择器的默认值为今天
        dateSelector.value = todayStr;

        // 3. 首次加载页面时，获取今天的数据
        fetchDashboardData(todayStr);

        // 4. 监听日期选择器的 'change' 事件
        dateSelector.addEventListener('change', function() {
            // 当用户选择了新的日期
            const selectedDate = this.value;
            if (selectedDate) {
                // 使用新选择的日期去获取数据
                fetchDashboardData(selectedDate);
            }
        });
    }

    // ===================================================================
    // 5. 启动引擎！
    // ===================================================================
    initializeDashboard();
});