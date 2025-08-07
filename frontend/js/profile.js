document.addEventListener('DOMContentLoaded', function() {
    // 1. 获取表单和所有需要操作的元素
    const profileForm = document.getElementById('profile-form');
    const emailInput = document.getElementById('email');
    const genderSelect = document.getElementById('gender');
    const dobInput = document.getElementById('date_of_birth');
    const submitButton = profileForm.querySelector('button[type="submit"]');

    const goalsForm = document.getElementById('goals-form');
    const sleepTargetInput = document.getElementById('target_sleep_duration');
    const sportTargetInput = document.getElementById('target_sport_calories');
    const dietTargetInput = document.getElementById('target_diet_calories');
    const API_GOALS_URL = '/api/goals/'

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

    /**
     * 函数：获取用户已有的目标并填充表单
     */
    async function fetchAndSetGoals() {
        try {
            const response = await fetch(API_GOALS_URL, { credentials: 'include' });
            if (!response.ok) return;
            const goalsData = await response.json();

            // 将获取到的数据填充到表单输入框中
            if(goalsData.target_sleep_duration) sleepTargetInput.value = goalsData.target_sleep_duration;
            if(goalsData.target_sport_calories) sportTargetInput.value = goalsData.target_sport_calories;
            if(goalsData.target_diet_calories) dietTargetInput.value = goalsData.target_diet_calories;

        } catch (error) {
            console.error('获取健康目标失败:', error);
        }
    }

    /**
     * 函数：处理目标表单的提交
     */
    async function handleGoalsFormSubmit(event) {
        event.preventDefault();

        const dataToSubmit = {
            target_sleep_duration: parseFloat(sleepTargetInput.value) || null,
            target_sport_calories: parseInt(sportTargetInput.value, 10) || null,
            target_diet_calories: parseInt(dietTargetInput.value, 10) || null,
        };

        const submitButton = goalsForm.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = '正在保存...';

        try {
            const response = await fetch(API_GOALS_URL, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                credentials: 'include',
                body: JSON.stringify(dataToSubmit)
            });
            
            if (!response.ok) throw new Error('保存目标失败');
            
            showToast('健康目标已更新！', 'success', 'check-circle-fill');

        } catch (error) {
            console.error('保存目标失败:', error);
            showToast('保存失败，请重试。', 'danger', 'exclamation-triangle-fill');
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
        }
    }

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

    // 页面加载时，获取并设置已有的目标
    fetchAndSetGoals();

    // 为目标表单绑定提交事件
    if (goalsForm) {
        goalsForm.addEventListener('submit', handleGoalsFormSubmit);
    }
});