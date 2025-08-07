/**
 * =================================================================================
 * friends.js
 *
 * 学生健康管理系统 - 好友社交页面交互逻辑
 *
 * 负责处理：
 * 1. 好友列表、好友请求的加载与渲染
 * 2. 发送、接受、拒绝/删除好友关系
 * 3. 加载并渲染好友的健康动态信息流 (Feed)
 * 4. 发表和展示对动态的评论
 * =================================================================================
 */

document.addEventListener('DOMContentLoaded', function () {
    // --- 全局变量与DOM元素获取 ---
    // 关系管理
    const addFriendForm = document.getElementById('add-friend-form');
    const searchUserInput = document.getElementById('search-user-input');
    const friendRequestsList = document.getElementById('friend-requests-list');
    const friendsList = document.getElementById('friends-list');
    // 动态信息流
    const healthFeedContainer = document.getElementById('health-feed-container');

    // 存储当前用户信息，【重要】见文件末尾的说明
    let CURRENT_USER = {
        id: null,
        username: null,
    };

    /**
     * -----------------------------------------------------------------------------
     * @Helper: 获取CSRF Token的辅助函数
     * Django开启CSRF保护后，所有POST, PUT, DELETE请求都需要这个
     * -----------------------------------------------------------------------------
     */
    function getCSRFToken() {
        // 这是一个标准方法，用于从cookie中获取Django的CSRF令牌
        return document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    }


    /**
     * -----------------------------------------------------------------------------
     * @Section 1: 初始化函数
     * 页面加载后，获取所有必要的数据并设置事件监听
     * -----------------------------------------------------------------------------
     */
    async function initializePage() {
        // 尝试从localStorage获取用户信息
        const storedUserId = localStorage.getItem('user_id');
        const storedUsername = localStorage.getItem('username');

        if (storedUserId && storedUsername) {
            CURRENT_USER.id = parseInt(storedUserId, 10);
            CURRENT_USER.username = storedUsername;
        } else {
            console.error("无法获取用户信息，请确保登录时已存储。");
            healthFeedContainer.innerHTML = '<div class="alert alert-danger">无法加载用户信息，请重新登录。</div>';
            return;
        }

        // 并发加载好友关系和动态信息流，提升速度
        await Promise.all([
            loadFriendsAndRequests(),
            loadHealthFeed()
        ]);

        // 设置事件监听器
        addFriendForm.addEventListener('submit', handleSendFriendRequest);
        friendsList.addEventListener('click', handleFriendListActions);
        friendRequestsList.addEventListener('click', handleRequestListActions);
        healthFeedContainer.addEventListener('submit', handleCommentSubmit);
    }


    /**
     * -----------------------------------------------------------------------------
     * @Section 2: 好友关系管理 (加载、渲染、操作)
     * -----------------------------------------------------------------------------
     */

    // 加载好友列表和待处理请求
    async function loadFriendsAndRequests() {
        try {
            const [friendsRes, requestsRes] = await Promise.all([
                fetch('/api/friendships/?status=accepted'),
                fetch('/api/friendships/?status=pending')
            ]);
            const friends = await friendsRes.json();
            const requests = await requestsRes.json();
            renderFriendsList(friends);
            renderRequestsList(requests);
        } catch (error) {
            console.error('加载好友关系失败:', error);
        }
    }

    // 渲染好友列表
    function renderFriendsList(friends) {
        friendsList.innerHTML = '';
        if (friends.length === 0) {
            friendsList.innerHTML = '<li class="list-group-item text-center text-muted">你还没有好友，快去添加吧！</li>';
            return;
        }
        friends.forEach(friendship => {
            // 从关系中找出好友那一方的信息
            const friendInfo = friendship.from_user_info.id === CURRENT_USER.id ? friendship.to_user_info : friendship.from_user_info;
            let isAuthorized = false;
            if (friendship.from_user_info.id === CURRENT_USER.id) {
                // 我是发起者，看我是否授权了接收者
                isAuthorized = friendship.from_user_can_be_viewed;
            } else {
                // 我是接收者，看我是否授权了发起者
                isAuthorized = friendship.to_user_can_be_viewed;
            }
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';
            li.innerHTML = `
            <span>${friendInfo.username}</span>
            <div class="d-flex align-items-center">
                <div class="form-check form-switch me-3" title="是否授权对方查看我的动态">
                    <input 
                        class="form-check-input permission-switch" 
                        type="checkbox" 
                        role="switch" 
                        id="permission-switch-${friendship.id}"
                        data-id="${friendship.id}"
                        ${isAuthorized ? 'checked' : ''}
                    >
                    <label class="form-check-label small" for="permission-switch-${friendship.id}">
                        ${isAuthorized ? '已授权' : '未授权'}
                    </label>
                </div>
                <button class="btn btn-sm btn-outline-danger btn-delete-friend" data-id="${friendship.id}" title="删除好友">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;
            friendsList.appendChild(li);
        });
    }

    // 渲染好友请求列表
    function renderRequestsList(requests) {
        friendRequestsList.innerHTML = '';
        const pendingRequests = requests.filter(req => req.to_user_info.id === CURRENT_USER.id);

        if (pendingRequests.length === 0) {
            friendRequestsList.innerHTML = '<li class="list-group-item text-center text-muted">暂无新的好友请求</li>';
            return;
        }

        pendingRequests.forEach(request => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';
            li.innerHTML = `
                <span>${request.from_user_info.username}</span>
                <div>
                    <button class="btn btn-sm btn-success me-2 btn-accept-request" data-id="${request.id}">接受</button>
                    <button class="btn btn-sm btn-secondary btn-reject-request" data-id="${request.id}">拒绝</button>
                </div>
            `;
            friendRequestsList.appendChild(li);
        });
    }

    // 处理发送好友请求的表单提交
    async function handleSendFriendRequest(event) {
        event.preventDefault();
        const friendIdentifier = searchUserInput.value.trim();
        if (!friendIdentifier) return;
        
        // 注意：API需要用户ID。实际应用中，你可能需要一个通过用户名搜索ID的API。
        // 此处我们假设用户直接输入了ID。
        try {
            const res = await fetch('/api/friendships/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ to_user_username: friendIdentifier })
            });
            if (res.ok) {
                alert('好友请求已发送！');
                searchUserInput.value = '';
                // 可以只刷新请求列表，或者全部刷新
                loadFriendsAndRequests();
            } else {
                const error = await res.json();
                alert(`发送失败: ${error.message || '请检查用户ID是否正确'}`);
            }
        } catch (error) {
            console.error('发送好友请求异常:', error);
            alert('操作失败，请稍后重试。');
        }
    }

    // 统一处理好友列表中的点击事件（删除）
    async function handleFriendListActions(event) {
        const target = event.target;

        // --- 处理删除好友按钮 ---
        if (target.closest('.btn-delete-friend')) {
            const friendshipId = target.closest('.btn-delete-friend').dataset.id;
            if (confirm('确定要删除这位好友吗？')) {
                await deleteFriendship(friendshipId);
            }
            return; // 处理完毕，退出函数
        }

        // --- 【新增】处理权限开关的切换 ---
        if (target.classList.contains('permission-switch')) {
            const friendshipId = target.dataset.id;
            const canView = target.checked; // 开关切换后的状态 (true 或 false)

            // 更新开关旁边的文字
            const label = target.nextElementSibling;
            label.textContent = canView ? '已授权' : '未授权';

            // 调用API更新后端数据
            await updateFriendPermission(friendshipId, canView);
        }
    }

    async function updateFriendPermission(id, canView) {
        try {
            const res = await fetch(`/api/friendships/${id}/set-permission/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ can_view: canView })
            });
            if (!res.ok) {
                // 如果更新失败，可以在这里给用户提示
                console.error('权限更新失败!');
                alert('权限更新失败，请稍后重试。');
            }
            // 成功则无需提示，UI已经即时响应
        } catch (error) {
            console.error('更新好友权限时发生网络错误:', error);
            alert('权限更新失败，请检查网络连接。');
        }
    }
    
    // 统一处理请求列表中的点击事件（接受/拒绝）
    async function handleRequestListActions(event) {
        const button = event.target;
        const friendshipId = button.dataset.id;
        if (button.classList.contains('btn-accept-request')) {
            await acceptFriendRequest(friendshipId);
        } else if (button.classList.contains('btn-reject-request')) {
            await deleteFriendship(friendshipId); // 拒绝就是删除这条关系记录
        }
    }

    // API调用：接受请求
    async function acceptFriendRequest(id) {
        try {
            await fetch(`/api/friendships/${id}/accept/`, { method: 'PUT', headers: {'X-CSRFToken': getCSRFToken()} });
            loadFriendsAndRequests();
            loadHealthFeed();
        } catch (error) { console.error('接受请求失败:', error); }
    }

    // API调用：删除关系（用于拒绝请求或删除好友）
    async function deleteFriendship(id) {
        try {
            await fetch(`/api/friendships/${id}/`, { method: 'DELETE', headers: {'X-CSRFToken': getCSRFToken()} });
            loadFriendsAndRequests();
            loadHealthFeed();
        } catch (error) { console.error('删除关系失败:', error); }
    }

    /**
     * -----------------------------------------------------------------------------
     * @Section 3: 好友动态信息流 (加载、渲染、评论)
     * -----------------------------------------------------------------------------
     */
    
    // 加载并渲染好友动态
    async function loadHealthFeed() {
        try {
            const res = await fetch('/api/feed/');
            const feedItems = await res.json();
            healthFeedContainer.innerHTML = ''; // 清空加载动画

            if (feedItems.length === 0) {
                healthFeedContainer.innerHTML = '<div class="text-center p-5 bg-light rounded">好友们很安静，还没有任何动态。</div>';
                return;
            }

            feedItems.forEach(item => {
                // 1. 创建卡片
                const card = createFeedCard(item);
                // 2. 【先】把卡片添加到页面上
                healthFeedContainer.appendChild(card);
                // 3. 【后】再为这个刚刚添加的卡片加载评论
                loadComments(item.content_type_model, item.object_id);
            });
        } catch (error) {
            console.error('加载好友动态失败:', error);
            healthFeedContainer.innerHTML = '<div class="alert alert-warning">无法加载好友动态，请稍后重试。</div>';
        }
    }

    // 创建单个动态卡片的HTML结构
    function createFeedCard(item) {
        const card = document.createElement('div');
        card.className = 'card mb-3';
        const formattedDate = new Date(item.timestamp).toLocaleString();

        card.innerHTML = `
            <div class="card-body">
                <div class="d-flex align-items-center mb-2">
                    <div class="fw-bold me-2">${item.user.username}</div>
                    <div class="text-muted small">${formattedDate}</div>
                </div>
                <p class="card-text">${item.content}</p>
                <hr>
                <div class="comments-section">
                    <div class="comments-list" id="comments-for-${item.content_type_model}-${item.object_id}">
                        </div>
                    <form class="comment-form mt-2">
                        <input type="hidden" name="content_type" value="${item.content_type_model}">
                        <input type="hidden" name="object_id" value="${item.object_id}">
                        <div class="input-group">
                            <input type="text" name="text" class="form-control form-control-sm" placeholder="添加评论..." required>
                            <button type="submit" class="btn btn-sm btn-outline-primary">发送</button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        // 删除了 loadComments(...) 这一行
        return card;
    }

    // 加载并渲染某条动态的评论
    async function loadComments(contentType, objectId) {
        const container = document.getElementById(`comments-for-${contentType}-${objectId}`);
        try {
            const res = await fetch(`/api/comments/?content_type_model=${contentType}&object_id=${objectId}`);
            const comments = await res.json();
            console.log(`获取到的评论 for ${contentType} #${objectId}:`, comments);
            container.innerHTML = ''; // 清空
            if (comments.length > 0) {
                comments.forEach(comment => {
                    const p = document.createElement('p');
                    p.className = 'small mb-1 bg-light p-2 rounded';
                    p.innerHTML = `<strong class="me-2">${comment.author_username}</strong>: ${comment.text}`;
                    container.appendChild(p);
                });
            }
        } catch (error) {
            console.error(`加载评论失败 for ${contentType}-${objectId}:`, error);
        }
    }

    // 处理评论表单的提交
    async function handleCommentSubmit(event) {
        if (event.target.classList.contains('comment-form')) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            try {
                const res = await fetch('/api/comments/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify(data)
                });
                if (res.ok) {
                    form.reset(); // 清空表单
                    // 重新加载这条动态的评论区
                    loadComments(data.content_type, data.object_id);
                } else {
                    alert('评论失败！');
                }
            } catch (error) {
                console.error('评论提交异常:', error);
            }
        }
    }

    // --- 页面启动 ---
    initializePage();
});