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

    const summarySection = document.getElementById('health-summary');
    const summarySuggestionEl = document.getElementById('summary-suggestion');

    const goalsProgressContainer = document.getElementById('goals-progress-container');

    // ===================================================================
    // 3. 定义一个函数来更新UI (我们的“室内设计师”)
    // ===================================================================
    function updateDashboardUI(apiResponse) {
        console.log("--- 1. Entering updateDashboardUI ---");
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

                // 修正点3：在CountUp前加上 countUp.
                const caloriesEatenCountUp = new countUp.CountUp(caloriesEatenEl, data.diet.total_calories_eaten);
                if (!caloriesEatenCountUp.error) {
                    caloriesEatenCountUp.start();
                } else {
                    console.error(caloriesEatenCountUp.error);
                    caloriesEatenEl.textContent = data.diet.total_calories_eaten;
                }
                dietDetailsEl.textContent = '营养均衡，活力满满';

            } else {
                caloriesEatenEl.textContent = '0';
                dietDetailsEl.textContent = '记录饮食，掌控健康';
            }

            // 更新健康小结
            const summaryWrapper = document.getElementById('summary-content-wrapper');
            if (summaryWrapper) {
                const heading = summaryWrapper.querySelector('.alert-heading');
                const suggestionP = summaryWrapper.querySelector('#summary-suggestion');
                if (heading) heading.textContent = "今日小结"; // 确保标题正确
                if (suggestionP) suggestionP.textContent = data.health_summary.suggestion;
            }

            renderGoalsProgress(data);
        }
    }

    /**
     * 【V7 - 融合版】基于V4的完美重叠，并用新技巧消除缝隙
     */
    function renderGoalsProgress(data) {
        if (window.vitalityChart instanceof Chart) {
            window.vitalityChart.destroy();
        }
        const ctx = document.getElementById('vitality-rings-chart');
        if (!ctx) return;

        // --- 数据准备 --- (不变)
        const goalsData = data.goals || {};
        const current_sleep = data.sleep.duration_hours || 0;
        const target_sleep = goalsData.target_sleep_duration || 0;
        const progress_sleep = target_sleep > 0 ? (current_sleep / target_sleep) * 100 : 0;
        const current_sport = data.sports.total_calories_burned || 0;
        const target_sport = goalsData.target_sport_calories || 0;
        const progress_sport = target_sport > 0 ? (current_sport / target_sport) * 100 : 0;
        const current_diet = data.diet.total_calories_eaten || 0;
        const target_diet = goalsData.target_diet_calories || 0;
        const progress_diet = target_diet > 0 ? (current_diet / target_diet) * 100 : 0;

        // --- 更新UI文本 --- (不变)
        document.getElementById('sleep-progress-text').textContent = `睡眠：${current_sleep.toFixed(1)} / ${target_sleep.toFixed(1)} 小时`;
        document.getElementById('sport-progress-text').textContent = `运动：${Math.round(current_sport)} / ${Math.round(target_sport)} 大卡`;
        document.getElementById('diet-progress-text').textContent = `饮食：${Math.round(current_diet)} / ${Math.round(target_diet)} 大卡`;

        let completedGoals = 0;
        if (progress_sleep >= 100) completedGoals++;
        if (progress_sport >= 100) completedGoals++;
        if (progress_diet > 0 && progress_diet <= 100) completedGoals++;
        document.getElementById('vitality-rings-status').textContent = `${completedGoals}/3 目标达成`;

        // --- 准备图表数据 --- (不变)
        const ringColors = {
            sport: { solid: '#ff6384', faded: '#ff638433' },
            sleep: { solid: '#ffcd56', faded: '#ffcd5633' },
            diet: { solid: '#36a2eb', faded: '#36a2eb33' }
        };

        // ⭐ 核心修改在这里：创建数据集的函数
        function createRingDataset(progress, colors) {
            const safeProgress = Math.min(100, Math.max(0, progress));
            const cornerRadius = 20; // 定义统一的圆角大小

            return {
                data: [safeProgress, 100 - safeProgress],
                backgroundColor: [colors.solid, colors.faded],
                borderWidth: 0,
                // 关键技巧：为每个数据段的每个角单独设置 borderRadius
                borderRadius: {
                    // outerStart: 进度条起点的外圆角
                    // outerEnd: 进度条终点的外圆角
                    // innerStart: 进度条起点的内圆角
                    // innerEnd: 进度条终点的内圆角
                    // 我们让整个环的起点和终点是圆角，但中间交界处是直角
                    outerStart: cornerRadius,
                    outerEnd: cornerRadius,
                    innerStart: cornerRadius,
                    innerEnd: cornerRadius,
                },
                // 这是一个非官方但部分版本有效的技巧，用于平滑处理
                borderSkipped: false,
            };
        }

        window.vitalityChart = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                datasets: [
                    createRingDataset(progress_sleep, ringColors.sleep),  // 睡眠 - 外环
                    createRingDataset(progress_sport, ringColors.sport),  // 运动 - 中环
                    createRingDataset(progress_diet, ringColors.diet),    // 饮食 - 内环
                ]
            },
            // options 部分与 V4 保持一致，确保重叠和样式
            options: {
                maintainAspectRatio: false,
                circumference: 270,
                rotation: 225,
                cutout: '50%',
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                },
                // 在新版本Chart.js中，borderRadius的精细控制不再需要写在datasets里，
                // 而是通过上下文(context)在主options里实现
                elements: {
                    arc: {
                        // 使用scriptable options（上下文回调函数）
                        borderRadius: (context) => {
                            // 如果是第一个数据段（深色进度）
                            if (context.dataIndex === 0) {
                                // 只让它的终点是圆角
                                return { outerEnd: 20, innerEnd: 20 };
                            }
                            // 如果是第二个数据段（浅色轨道）
                            else {
                                // 只让它的起点是圆角
                                return { outerStart: 20, innerStart: 20 };
                            }
                        },
                    }
                }
            }
        });
    }

    // ===================================================================
    // 4. 定义主函数来发起API请求
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

            const insightsSection = document.getElementById('insights-section');
            if (insightsSection) {
                insightsSection.innerHTML = `
                    <div class="col-12">
                        <div class="alert alert-danger">
                            <h4 class="alert-heading">加载失败!</h4>
                            <p>${error.message}</p>
                            <hr>
                            <p class="mb-0">请检查网络连接或后台服务是否正常，然后 <a href="#" onclick="event.preventDefault(); location.reload();">刷新页面</a> 重试。</p>
                        </div>
                    </div>`;
            }
        } finally {
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
        dateSelector.addEventListener('change', function () {
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