document.addEventListener('DOMContentLoaded', function () {
    // --- 昼夜模式和密码显示切换逻辑 ---
    // 这部分逻辑是通用的，已提取到一个公共的 theme.js 文件中
    const themeSwitchButton = document.getElementById("theme-switch");
    themeSwitchButton && document.body.classList.toggle("dark-mode", "dark" === localStorage.getItem("theme") || !localStorage.getItem("theme") && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
    themeSwitchButton && themeSwitchButton.addEventListener("click", () => { document.body.classList.toggle("dark-mode"), localStorage.setItem("theme", document.body.classList.contains("dark-mode") ? "dark" : "light") });

    const togglePasswordButtons = document.querySelectorAll(".toggle-password");
    togglePasswordButtons.forEach(e => {
        e.addEventListener("click", function () {
            const t = this.previousElementSibling;
            const s = this.querySelector(".eye-open");
            const o = this.querySelector(".eye-closed");
            "password" === t.type ? (t.type = "text", s.style.display = "none", o.style.display = "inline-block") : (t.type = "password", s.style.display = "inline-block", o.style.display = "none")
        })
    });

    // --- 登录表单API提交逻辑 ---
    const loginForm = document.getElementById('login-form');
    const responseMessageDiv = document.getElementById('response-message');

    const API_LOGIN_URL = '/api/login/';

    loginForm.addEventListener('submit', function (event) {
        event.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        const data = {
            username: username,
            password: password
        };

        fetch(API_LOGIN_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
            credentials: 'include' // 确保在请求中携带cookies
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => Promise.reject(err));
                }
                return response.json();
            })
            .then(result => {
                responseMessageDiv.style.display = 'block';
                responseMessageDiv.textContent = result.message;
                responseMessageDiv.className = 'response-message success';

                setTimeout(() => {
                    window.location.href = '/dashboard/';
                }, 1500);
            })
            .catch(error => {
                console.error('Login Error:', error);
                responseMessageDiv.style.display = 'block';
                responseMessageDiv.textContent = error.message || '发生网络错误，请稍后重试。';
                responseMessageDiv.className = 'response-message error';
            });
    });
});