/**
 * body_metrics.js - 身体指标页面 JavaScript (Member B)
 * 功能: 加载、添加、显示身体指标数据，渲染 ECharts 趋势图
 */

document.addEventListener('DOMContentLoaded', function () {
    // DOM 元素
    const currentWeight = document.getElementById('current-weight');
    const currentHeight = document.getElementById('current-height');
    const currentBmi = document.getElementById('current-bmi');
    const bmiStatus = document.getElementById('bmi-status');
    const historyTbody = document.getElementById('history-tbody');
    const bodyMetricForm = document.getElementById('body-metric-form');
    const weightInput = document.getElementById('weight-input');
    const heightInput = document.getElementById('height-input');
    const recordDateInput = document.getElementById('record-date-input');
    const editingIdInput = document.getElementById('editing-id');
    const previewBmiValue = document.getElementById('preview-bmi-value');
    const previewBmiStatus = document.getElementById('preview-bmi-status');
    const chartRangeSelect = document.getElementById('chart-range');
    const bodyMetricModal = document.getElementById('bodyMetricModal');

    // ECharts 实例
    let trendChart = null;
    let allMetrics = [];

    // 初始化
    init();

    function init() {
        // 设置默认日期为今天
        recordDateInput.value = new Date().toISOString().slice(0, 10);

        // 初始化 ECharts
        trendChart = echarts.init(document.getElementById('trend-chart'));
        window.addEventListener('resize', () => trendChart.resize());

        // 加载数据
        loadMetrics();

        // 事件监听
        bodyMetricForm.addEventListener('submit', handleFormSubmit);
        weightInput.addEventListener('input', updateBmiPreview);
        heightInput.addEventListener('input', updateBmiPreview);
        chartRangeSelect.addEventListener('change', () => renderChart(allMetrics));

        // 模态框打开时重置表单
        bodyMetricModal.addEventListener('show.bs.modal', function (event) {
            const btn = event.relatedTarget;
            if (!btn || !btn.dataset.id) {
                // 新增模式
                bodyMetricForm.reset();
                editingIdInput.value = '';
                recordDateInput.value = new Date().toISOString().slice(0, 10);
                previewBmiValue.textContent = '--';
                previewBmiStatus.textContent = '--';
                previewBmiStatus.className = 'badge ms-2';
            }
        });
    }

    // 加载所有身体指标数据
    async function loadMetrics() {
        try {
            const response = await fetch('/api/body-metrics/', {
                credentials: 'include'
            });
            if (!response.ok) throw new Error('加载失败');

            allMetrics = await response.json();
            updateCurrentDisplay(allMetrics);
            renderHistoryTable(allMetrics);
            renderChart(allMetrics);
        } catch (error) {
            console.error('加载身体指标失败:', error);
            historyTbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">加载失败</td></tr>';
        }
    }

    // 更新当前显示的数据卡片
    function updateCurrentDisplay(metrics) {
        if (metrics.length === 0) {
            currentWeight.textContent = '-- kg';
            currentHeight.textContent = '-- cm';
            currentBmi.textContent = '--';
            bmiStatus.textContent = '暂无数据';
            bmiStatus.className = 'badge bg-secondary';
            return;
        }

        const latest = metrics[0]; // 按日期倒序，第一个是最新的
        currentWeight.textContent = `${latest.weight} kg`;
        currentHeight.textContent = `${latest.height} cm`;
        currentBmi.textContent = latest.bmi ? latest.bmi.toFixed(2) : '--';

        const status = getBmiStatus(latest.bmi);
        bmiStatus.textContent = status.text;
        bmiStatus.className = `badge ${status.class}`;
    }

    // 获取 BMI 状态
    function getBmiStatus(bmi) {
        if (!bmi) return { text: '未知', class: 'bg-secondary' };
        if (bmi < 18.5) return { text: '偏瘦', class: 'bg-info' };
        if (bmi < 24) return { text: '正常', class: 'bg-success' };
        if (bmi < 28) return { text: '超重', class: 'bg-warning' };
        return { text: '肥胖', class: 'bg-danger' };
    }

    // 渲染历史记录表格
    function renderHistoryTable(metrics) {
        if (metrics.length === 0) {
            historyTbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">暂无记录，点击"添加记录"开始</td></tr>';
            return;
        }

        historyTbody.innerHTML = metrics.map(m => {
            const status = getBmiStatus(m.bmi);
            return `
                <tr>
                    <td>${m.record_date}</td>
                    <td>${m.weight}</td>
                    <td>${m.height}</td>
                    <td>${m.bmi ? m.bmi.toFixed(2) : '--'}</td>
                    <td><span class="badge ${status.class}">${status.text}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteMetric(${m.id})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // 渲染 ECharts 趋势图
    function renderChart(metrics) {
        if (metrics.length === 0) {
            trendChart.setOption({
                title: { text: '暂无数据', left: 'center', top: 'center' }
            });
            return;
        }

        const days = parseInt(chartRangeSelect.value);
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - days);

        // 过滤并按日期正序排列
        const filtered = metrics
            .filter(m => new Date(m.record_date) >= cutoffDate)
            .sort((a, b) => new Date(a.record_date) - new Date(b.record_date));

        const dates = filtered.map(m => m.record_date);
        const weights = filtered.map(m => m.weight);
        const bmis = filtered.map(m => m.bmi);

        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'cross' }
            },
            legend: {
                data: ['体重 (kg)', 'BMI'],
                bottom: 0
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: dates,
                axisLabel: {
                    rotate: 45
                }
            },
            yAxis: [
                {
                    type: 'value',
                    name: '体重 (kg)',
                    position: 'left',
                    min: function (value) { return Math.floor(value.min - 5); },
                    max: function (value) { return Math.ceil(value.max + 5); }
                },
                {
                    type: 'value',
                    name: 'BMI',
                    position: 'right',
                    min: 15,
                    max: 35,
                    splitLine: { show: false }
                }
            ],
            series: [
                {
                    name: '体重 (kg)',
                    type: 'line',
                    data: weights,
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 8,
                    lineStyle: { width: 3 },
                    itemStyle: { color: '#5470c6' }
                },
                {
                    name: 'BMI',
                    type: 'line',
                    yAxisIndex: 1,
                    data: bmis,
                    smooth: true,
                    symbol: 'diamond',
                    symbolSize: 8,
                    lineStyle: { width: 2, type: 'dashed' },
                    itemStyle: { color: '#91cc75' },
                    markLine: {
                        silent: true,
                        data: [
                            { yAxis: 18.5, name: '偏瘦', lineStyle: { color: '#17a2b8' } },
                            { yAxis: 24, name: '正常上限', lineStyle: { color: '#28a745' } },
                            { yAxis: 28, name: '超重', lineStyle: { color: '#ffc107' } }
                        ]
                    }
                }
            ]
        };

        trendChart.setOption(option, true);
    }

    // 更新 BMI 预览
    function updateBmiPreview() {
        const weight = parseFloat(weightInput.value);
        const height = parseFloat(heightInput.value);

        if (weight > 0 && height > 0) {
            const bmi = weight / Math.pow(height / 100, 2);
            previewBmiValue.textContent = bmi.toFixed(2);
            const status = getBmiStatus(bmi);
            previewBmiStatus.textContent = status.text;
            previewBmiStatus.className = `badge ms-2 ${status.class}`;
        } else {
            previewBmiValue.textContent = '--';
            previewBmiStatus.textContent = '--';
            previewBmiStatus.className = 'badge ms-2';
        }
    }

    // 表单提交处理
    async function handleFormSubmit(e) {
        e.preventDefault();

        const data = {
            weight: parseFloat(weightInput.value),
            height: parseFloat(heightInput.value),
            record_date: recordDateInput.value
        };

        const editingId = editingIdInput.value;
        const url = editingId ? `/api/body-metrics/${editingId}/` : '/api/body-metrics/';
        const method = editingId ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(data),
                credentials: 'include'
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(JSON.stringify(errData));
            }

            // 关闭模态框
            bootstrap.Modal.getInstance(bodyMetricModal).hide();

            // 重新加载数据
            loadMetrics();

        } catch (error) {
            console.error('保存失败:', error);
            alert('保存失败: ' + error.message);
        }
    }

    // 删除记录 (全局函数，供表格按钮调用)
    window.deleteMetric = async function (id) {
        if (!confirm('确定要删除这条记录吗？')) return;

        try {
            const response = await fetch(`/api/body-metrics/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                credentials: 'include'
            });

            if (!response.ok) throw new Error('删除失败');

            loadMetrics();
        } catch (error) {
            console.error('删除失败:', error);
            alert('删除失败');
        }
    };
});
