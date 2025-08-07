/**
 * 将 Date 对象格式化为 'YYYY-MM-DD' 字符串
 * @param {Date} date - 要格式化的日期对象
 * @returns {string}
 */
function getFormattedDate(date) {
    if (!(date instanceof Date) || isNaN(date)) {
        return ''; // 处理无效日期
    }
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function getCsrfToken() {
    // 优先从HTML中的隐藏输入框获取
    const tokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (tokenInput) {
        return tokenInput.value;
    }
    // 如果找不到，尝试从cookie中获取（作为备用方案）
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length, cookie.length);
        }
    }
    return null;
}

/**
 * [全局函数] 显示一个Bootstrap Toast提示
 * @param {string} message - 要显示的消息
 * @param {string} type - 'success', 'danger', 'warning', 'info' (对应Bootstrap背景色)
 * @param {string} iconName - Bootstrap Icons的图标名 (e.g., 'check-circle-fill')
 */
function showToast(message, type = 'info', iconName = 'info-circle-fill') {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1100'; // 确保在最上层
        document.body.appendChild(toastContainer);
    }

    const toastId = `toast-${Date.now()}`;
    // ✨ 增加了图标显示 ✨
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${iconName} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 }); // 持续5秒
    toast.show();

    toastElement.addEventListener('hidden.bs.toast', () => toastElement.remove());
}

document.addEventListener('DOMContentLoaded', function() {
    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(event) {
            event.preventDefault(); // 阻止<a>标签的默认跳转行为

            if (confirm('您确定要注销吗？')) {
                fetch('/api/logout/', {
                    method: 'POST',
                    headers: {
                        // Django的@csrf_exempt暂时不需要这个，但加上是好习惯
                        // 'X-CSRFToken': getCookie('csrftoken'), 
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        alert('您已成功注销！');
                        // 注销成功后，跳转到登录页面
                        window.location.href = '/login/'; 
                    } else {
                        alert('注销失败: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('注销请求失败:', error);
                    alert('注销时发生网络错误。');
                });
            }
        });
    }

    async function checkHealthAlerts() {
        if (!logoutLink) return;

        try {
            const response = await fetch('/api/alerts/check/', { credentials: 'include' });
            if (!response.ok) return;
            
            const alerts = await response.json();

            if (Array.isArray(alerts) && alerts.length > 0) {
                alerts.forEach((alert, index) => {
                    // a. 为每条警告创建一个唯一的key，用 alert_code
                    const alertKey = `alert_shown_${alert.alert_code}`;

                    // b. ✨ 关键检查：在显示之前，先看看sessionStorage里有没有记录 ✨
                    if (!sessionStorage.getItem(alertKey)) {
                        
                        // c. 如果没有记录，说明是本次会话第一次看到，那么就显示它
                        setTimeout(() => {
                            showToast(alert.message, 'warning', 'exclamation-triangle-fill');
                            
                            // d. ✨ 显示之后，立刻在sessionStorage里“盖个章” ✨
                            //    值设为 'true'，表示已经显示过了
                            sessionStorage.setItem(alertKey, 'true');
                        }, index * 1000);
                    }
                });
            }
        } catch (error) {
            console.error('检查健康预警失败:', error);
        }
    }

    // 页面加载完成后，延迟一点再检查，避免影响主内容加载
    setTimeout(checkHealthAlerts, 2000); // 延迟2秒

    const themeSwitchButton = document.getElementById('theme-switch');
    if (themeSwitchButton) { 
        // 函数：应用主题 [已升级]
        const applyTheme = (theme) => {
            // 直接在 <html> 根元素上设置 data-bs-theme 属性，这是Bootstrap 5.3+的官方方式
            document.documentElement.setAttribute('data-bs-theme', theme);
            
            // 为了兼容我们自己写的 .dark-mode 类，可以保留这个class
            if (theme === 'dark') {
                document.body.classList.add('dark-mode');
            } else {
                document.body.classList.remove('dark-mode');
            }
        };

        // 函数：切换主题
        const toggleTheme = () => {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
            localStorage.setItem('theme', newTheme);
        };

        // 按钮点击事件
        themeSwitchButton.addEventListener('click', toggleTheme);
    }

    // [关键] 页面加载时的主题应用逻辑，需要放在按钮判断逻辑之外，确保所有页面都执行
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // 优先使用用户保存的主题，否则跟随系统设置
    const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');

    // 立即应用初始主题
    // 注意：这里的 applyTheme 需要在全局作用域可访问，或者像现在这样重新定义
    const applyInitialTheme = (theme) => {
        document.documentElement.setAttribute('data-bs-theme', theme);
        if (theme === 'dark') {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
    };
    applyInitialTheme(initialTheme);
});