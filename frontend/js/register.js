document.addEventListener('DOMContentLoaded', function () {
    // --- 昼夜模式和密码显示切换通用逻辑 ---
    // (未来可以将这部分提取到 app.js 中，供所有页面复用)
    const themeSwitchButton = document.getElementById("theme-switch");
    if (themeSwitchButton) {
        const isDarkMode = localStorage.getItem("theme") === "dark" ||
            (!localStorage.getItem("theme") && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
        document.body.classList.toggle("dark-mode", isDarkMode);

        themeSwitchButton.addEventListener("click", () => {
            document.body.classList.toggle("dark-mode");
            localStorage.setItem("theme", document.body.classList.contains("dark-mode") ? "dark" : "light");
        });
    }

    const togglePasswordButtons = document.querySelectorAll(".toggle-password");
    togglePasswordButtons.forEach(button => {
        button.addEventListener("click", function () {
            const passwordInput = this.previousElementSibling;
            const eyeOpen = this.querySelector(".eye-open");
            const eyeClosed = this.querySelector(".eye-closed");
            if (passwordInput.type === "password") {
                passwordInput.type = "text";
                eyeOpen.style.display = "none";
                eyeClosed.style.display = "inline-block";
            } else {
                passwordInput.type = "password";
                eyeOpen.style.display = "inline-block";
                eyeClosed.style.display = "none";
            }
        });
    });

    // --- 注册表单API提交逻辑 ---
    const registerForm = document.getElementById('register-form');
    const responseMessageDiv = document.getElementById('response-message');
    const API_REGISTER_URL = '/api/register/';

    registerForm.addEventListener('submit', function (event) {
        event.preventDefault();

        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const password_confirm = document.getElementById('password_confirm').value;

        // 前端先行验证两次密码是否一致
        if (password !== password_confirm) {
            responseMessageDiv.style.display = 'block';
            responseMessageDiv.className = 'response-message error';
            responseMessageDiv.textContent = '两次输入的密码不一致！';
            return;
        }

        const data = {
            username: username,
            email: email,
            password: password
        };

        fetch(API_REGISTER_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => Promise.reject(err));
                }
                return response.json();
            })
            .then(result => {
                responseMessageDiv.style.display = 'block';
                responseMessageDiv.textContent = result.message + ' 即将跳转到登录页面...';
                responseMessageDiv.className = 'response-message success';

                // 注册成功后，提示用户并跳转到登录页面
                setTimeout(() => {
                    window.location.href = '/login/';
                }, 2000); // 2秒后跳转
            })
            .catch(error => {
                console.error('Registration Error:', error);
                responseMessageDiv.style.display = 'block';
                responseMessageDiv.textContent = error.message || '发生网络错误，请稍后重试。';
                responseMessageDiv.className = 'response-message error';
            });
    });
});