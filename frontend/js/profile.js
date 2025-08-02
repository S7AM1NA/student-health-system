document.addEventListener('DOMContentLoaded', function() {
    // 1. 获取表单和所有需要操作的元素
    const profileForm = document.getElementById('profile-form');
    const emailInput = document.getElementById('email');
    const genderSelect = document.getElementById('gender');
    const dobInput = document.getElementById('date_of_birth');
    const submitButton = profileForm.querySelector('button[type="submit"]');

    // 2. 监听表单的提交事件
    profileForm.addEventListener('submit', function(event) {
        event.preventDefault(); // 阻止表单的默认提交行为（页面刷新）

        // 3. 获取表单中的最新数据
        const formData = {
            email: emailInput.value,
            gender: genderSelect.value,
            // 如果日期为空，我们应该发送 null 或者不发送该字段，这里我们选择发送空字符串，让后端处理
            date_of_birth: dobInput.value || null 
        };

        // 4. 发起API请求来更新档案
        updateProfile(formData);
    });

    // 5. 定义API请求函数
    async function updateProfile(data) {
        const originalButtonText = submitButton.innerHTML;
        
        // a. 禁用按钮并显示加载状态，防止重复提交
        submitButton.disabled = true;
        submitButton.innerHTML = `
            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            正在更新...
        `;

        const csrfToken = profileForm.querySelector('input[name="csrfmiddlewaretoken"]').value;
        try {
            // b. 定义API端点
            const API_URL = '/api/profile/'; // 假设这是后端提供的更新接口

            // c. 使用fetch发送PUT请求
            const response = await fetch(API_URL, {
                method: 'PUT', // 或者 'PATCH'，根据后端API定义
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken 
                    // 如果后端需要CSRF Token，需要在这里添加
                },
                credentials: 'include', // 确保会带上sessionid等认证信息
                body: JSON.stringify(data) // 将JS对象转换为JSON字符串
            });

            // d. 解析响应
            const result = await response.json();

            // e. 根据响应结果给出反馈
            if (response.ok) {
                // 更新成功
                showToast('档案更新成功！', 'success');
            } else {
                // 更新失败，显示后端返回的错误信息
                const errorMessage = Object.values(result).join('\n') || '更新失败，请检查输入。';
                showToast(errorMessage, 'danger');
            }

        } catch (error) {
            // f. 处理网络错误等
            console.error('更新档案时发生错误:', error);
            showToast('网络错误，请稍后重试。', 'danger');
        } finally {
            // g. 无论成功失败，都恢复按钮状态
            submitButton.disabled = false;
            submitButton.innerHTML = originalButtonText;
        }
    }

    // 6. 定义一个漂亮的Toast提示函数 (可选，但能极大提升用户体验)
    function showToast(message, type = 'info') {
        // 检查页面上是否已存在toast容器，没有则创建
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }

        const toastId = `toast-${Date.now()}`;
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 }); // 3秒后自动消失
        toast.show();

        // 动画结束后，从DOM中移除toast元素，避免堆积
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
});