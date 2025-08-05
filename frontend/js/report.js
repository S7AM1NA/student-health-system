// frontend/js/report.js (最终正确版本)

/**
 * 辅助函数：检测当前是否为深色模式。
 * 您的 CSS 使用 .dark-mode 类，所以我们以此为准。
 */
const isDarkMode = () => {
    // 您的主题切换是通过在 <body> 上添加/移除 .dark-mode 类来工作的
    // 所以我们直接检查 body 元素即可。
    return document.body.classList.contains('dark-mode');
};

// 全局变量，用于缓存从API获取的报告数据，避免在主题切换时重复请求。
let currentReportData = null;

document.addEventListener('DOMContentLoaded', function () {
    const getFormattedDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    const today = new Date();
    const todayStr = getFormattedDate(today);

    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(today.getDate() - 6);
    const sevenDaysAgoStr = getFormattedDate(sevenDaysAgo);

    // 1. 首次加载报告
    loadHealthSummaryReport(sevenDaysAgoStr, todayStr);

    // 2. 监听主题切换事件，实现图表动态刷新
    // ✨ 这里是关键修改：将占位符替换为正确的CSS类选择器 ✨
    const themeToggler = document.querySelector('.theme-switch-button');

    if (themeToggler) {
        // 成功找到按钮，为其添加点击事件监听器
        themeToggler.addEventListener('click', () => {
            // 使用 setTimeout 将重绘任务推迟到DOM更新之后执行。
            // 您的切换逻辑可能需要一点时间来给<body>添加/移除class。
            setTimeout(() => {
                redrawReport();
            }, 50);
        });
    } else {
        // 如果因为某些原因（比如JS执行顺序）没找到，给出提示
        console.error("未能立即找到 .theme-switch-button。如果主题切换无效，请检查此项。");
    }
});

/**
 * 重绘报告函数。
 */
function redrawReport() {
    if (currentReportData) {
        renderOverallReport(currentReportData);
    }
}


/**
 * 从服务器加载健康摘要报告数据。
 */
async function loadHealthSummaryReport(startDate, endDate) {
    const API_URL = `/api/reports/health-summary/?start_date=${startDate}&end_date=${endDate}`;
    const reportContainer = document.getElementById('health-report-container');

    try {
        const response = await fetch(API_URL, { credentials: 'include' });
        const result = await response.json();

        if (result.status !== 'success') throw new Error(result.message);

        currentReportData = result.report;
        renderOverallReport(currentReportData);

    } catch (error) {
        console.error('加载综合报告失败:', error);
        if (reportContainer) reportContainer.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
        currentReportData = null;
    }
}

/**
 * 将报告数据渲染成HTML并插入页面。
 */
function renderOverallReport(report) {
    const container = document.getElementById('health-report-container');
    if (!container) return;

    const getScoreColorClass = (score) => {
        if (score >= 80) return 'text-success';
        if (score >= 60) return 'text-warning';
        return 'text-danger';
    };

    const overallHtml = `
        <div class="card mb-4">
            <div class="card-header bg-primary">
                <h4 class="mb-0 text-white">本周总览: ${report.overall_summary.title}</h4>
            </div>
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-4 text-center border-end">
                        <p class="text-muted mb-1">综合健康得分</p>
                        <h1 class="display-3 fw-bold ${getScoreColorClass(report.overall_summary.overall_score)}">
                            ${report.overall_summary.overall_score}
                        </h1>
                    </div>
                    <div class="col-md-8">
                        <h5 class="card-title">核心改进建议</h5>
                        <ul class="list-unstyled">
                            ${report.overall_summary.priority_suggestions.map(suggestion => `
                                <li class="mb-2"><i class="bi bi-pin-angle-fill text-primary me-2"></i>${suggestion}</li>
                            `).join('')}
                        </ul>
                        <hr>
                        <p class="card-text">
                            <strong>热量平衡分析:</strong> 
                            日均摄入 <span class="fw-bold">${report.overall_summary.calorie_balance.average_intake}</span> 大卡，
                            日均运动消耗 <span class="fw-bold">${report.overall_summary.calorie_balance.average_activity_burn}</span> 大卡。
                            <span class="badge bg-secondary">${report.overall_summary.calorie_balance.comment}</span>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    `;

    const analysisHtml = `
        <div class="row">
            <div class="col-lg-4 mb-3"><div class="card h-100"><div class="card-body"><h5 class="card-title d-flex justify-content-between"><span>睡眠分析</span><span class="fw-bold ${getScoreColorClass(report.sleep_analysis.score)}">${report.sleep_analysis.score}/100</span></h5><ul class="list-group list-group-flush"><li class="list-group-item">平均时长: <strong>${report.sleep_analysis.average_duration_hours.toFixed(1)} 小时</strong></li><li class="list-group-item">作息规律性: <strong>${report.sleep_analysis.consistency.comment}</strong></li><li class="list-group-item">数据覆盖率: <strong>${report.sleep_analysis.data_coverage_percent}%</strong></li></ul></div></div></div>
            <div class="col-lg-4 mb-3"><div class="card h-100"><div class="card-body"><h5 class="card-title d-flex justify-content-between"><span>运动分析</span><span class="fw-bold ${getScoreColorClass(report.sports_analysis.score)}">${report.sports_analysis.score}/100</span></h5><ul class="list-group list-group-flush"><li class="list-group-item">周均频率: <strong>${report.sports_analysis.frequency_per_week.toFixed(1)} 次</strong></li><li class="list-group-item">总消耗: <strong>${report.sports_analysis.total_calories_burned} 大卡</strong></li><li class="list-group-item">最常进行: <strong>${report.sports_analysis.most_frequent_activity || '无'}</strong></li></ul></div></div></div>
            <div class="col-lg-4 mb-3"><div class="card h-100"><div class="card-body"><h5 class="card-title d-flex justify-content-between"><span>饮食分析</span><span class="fw-bold ${getScoreColorClass(report.diet_analysis.score)}">${report.diet_analysis.score}/100</span></h5><ul class="list-group list-group-flush"><li class="list-group-item">日均摄入: <strong>${report.diet_analysis.average_daily_calories} 大卡</strong></li><li class="list-group-item">数据覆盖率: <strong>${report.diet_analysis.data_coverage_percent}%</strong></li></ul><canvas id="diet-pie-chart" class="mt-3" style="max-height: 150px;"></canvas></div></div></div>
        </div>
    `;

    container.innerHTML = overallHtml + analysisHtml;
    renderDietPieChart(report.diet_analysis.calorie_distribution);
}

/**
 * 渲染饮食分布饼图，并根据夜间模式自动调整字体颜色。
 */
function renderDietPieChart(distributionData) {
    const ctx = document.getElementById('diet-pie-chart');
    if (!ctx) return;

    const chartTextColor = isDarkMode() ? '#fff' : '#666';
    const chartBorderColor = isDarkMode() ? '#4a5568' : '#fff'; // 使用您的暗色卡片背景色作为边框色

    const labels = Object.keys(distributionData).map(key => ({
        'breakfast': '早餐', 'lunch': '午餐', 'dinner': '晚餐', 'snack': '加餐'
    }[key]));

    const data = Object.values(distributionData);

    const existingChart = Chart.getChart(ctx);
    if (existingChart) {
        existingChart.destroy();
    }

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                label: '热量分布 (大卡)',
                data: data,
                backgroundColor: ['rgba(255, 99, 132, 0.7)', 'rgba(54, 162, 235, 0.7)', 'rgba(255, 206, 86, 0.7)', 'rgba(75, 192, 192, 0.7)'],
                borderColor: chartBorderColor,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 10, font: { size: 10 }, color: chartTextColor } },
                tooltip: { titleColor: chartTextColor, bodyColor: chartTextColor }
            }
        }
    });
}