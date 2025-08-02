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