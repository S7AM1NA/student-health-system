// 使用 'DOMContentLoaded' 事件确保在HTML完全加载后再执行我们的JS代码
document.addEventListener('DOMContentLoaded', function () {
    // ===================================================================
    // ✨ 新增：昼夜模式切换逻辑 ✨
    // ===================================================================
    const themeSwitchButton = document.getElementById('theme-switch');
    const body = document.body;

    // 函数：应用主题
    const applyTheme = (theme) => {
        if (theme === 'dark') {
            body.classList.add('dark-mode');
        } else {
            body.classList.remove('dark-mode');
        }
    };

    // 函数：切换主题
    const toggleTheme = () => {
        // 判断当前是否是暗黑模式
        const currentThemeIsDark = body.classList.contains('dark-mode');
        const newTheme = currentThemeIsDark ? 'light' : 'dark';

        // 应用新主题
        applyTheme(newTheme);

        // 将用户的选择保存到localStorage，以便下次访问时记住
        localStorage.setItem('theme', newTheme);
    };

    // 按钮点击事件
    themeSwitchButton.addEventListener('click', toggleTheme);

    // 页面加载时，检查localStorage里是否保存了用户之前的选择
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        // 如果有保存的设置，则应用它
        applyTheme(savedTheme);
    } else {
        // 如果没有保存的设置，可以默认跟随系统设置 (可选)
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        applyTheme(prefersDark ? 'dark' : 'light');
    }


    // ===================================================================
    // 1. 定义常量 (我们的“地址簿”)
    // ===================================================================
    const API_BASE_URL = 'http://127.0.0.1:8000/api'; // 后端服务器的地址

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
    async function fetchDashboardData() {
        try {
            // `credentials: 'include'` 是关键，它告诉浏览器在发送请求时
            // 要自动带上 http-only cookies (比如我们的 sessionid)
            const response = await fetch(DASHBOARD_API_URL, { credentials: 'include' });

            const data = await response.json();

            // 检查HTTP状态码。如果是401或403，意味着未授权
            if (response.status === 401 || response.status === 403) {
                // 将后端返回的错误信息（如 "Authentication credentials..."）传递给UI更新函数
                // 这样 updateDashboardUI 里的逻辑就能处理跳转了
                updateDashboardUI({
                    status: 'error',
                    message: data.detail || '您需要登录才能访问此页面。'
                });
                return; // 提前结束函数
            }

            if (!response.ok) {
                // 处理其他类型的HTTP错误 (如 500 服务器内部错误)
                throw new Error(`HTTP错误! 状态码: ${response.status}, 消息: ${data.message || '未知错误'}`);
            }

            // 如果一切正常，调用UI更新函数
            updateDashboardUI(data);

        } catch (error) {
            console.error('无法从服务器获取数据:', error);
            // 这里可以显示一个更友好的全屏错误消息
            document.body.innerHTML = `<div class="container mt-5"><div class="alert alert-danger" role="alert">
                <h4 class="alert-heading">加载失败!</h4>
                <p>无法连接到健康数据服务器。请检查您的网络连接，并确认后端服务正在运行。</p>
                <hr>
                <p class="mb-0">您可以尝试 <a href="#" onclick="location.reload();">刷新页面</a> 重试。</p>
              </div></div>`;
        }
    }


    // ===================================================================
    // 5. 启动引擎！
    // ===================================================================
    fetchDashboardData();
});