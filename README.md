# Python大作业 学生健康管理系统

BUAA_2025

## 项目当前进度

**阶段一部分完成**。项目的基础架构已经搭建完毕。

*   ✅ **项目初始化**: 已创建Django项目及核心`core`应用。
*   ✅ **数据库模型**: 已定义 `CustomUser`, `SleepRecord`, `SportRecord`, `FoodItem`, `Meal`, `MealItem` 模型并完成首次数据库迁移。
*   ✅ **版本控制**: 项目已初始化为Git仓库，并与远程GitHub仓库关联。
*   ✅ **基础用户API**: 已完成用户**注册、登录、注销**的后端API接口，可供前端调用。

## 技术栈

*   **后端**: Django
*   **数据库**: SQLite (开发阶段)
*   **版本控制**: Git & GitHub
*   **开发环境**: Python 3.x (使用`venv`虚拟环境)

## 环境配置与启动 

1.  **克隆仓库**
    
    ```bash
    git clone https://github.com/Cl0udTide/student-health-system.git
    cd student-health-system
    ```
    
2.  **创建并激活Python虚拟环境**
    ```bash
    # 创建虚拟环境
    python -m venv .venv
    
    # 激活虚拟环境
    # Windows (PowerShell):
    .\.venv\Scripts\activate
    # macOS / Linux:
    source .venv/bin/activate
    ```
    *激活后，命令行前端会出现 `(venv)` 标识。*

3.  **安装项目依赖**
    ```bash
    pip install -r requirements.txt
    ```

4.  **应用数据库迁移**
    此步骤会根据已有的模型文件在本地创建`db.sqlite3`数据库文件。
    ```bash
    python manage.py migrate
    ```

5.  **启动开发服务器**
    ```bash
    python manage.py runserver
    ```
    现在，你可以通过浏览器访问 `http://127.0.0.1:8000/` 来查看项目了。

6.  **访问本地管理员账号**
    可访问 `http://127.0.0.1:8000/admin/` 后台管理界面查看和管理数据。管理员账号密码均为 `BUAA`。
---

## 数据库模型

以下是系统所有数据表的结构详情。

1. **CustomUser (用户信息)**

| 字段名 (Field)  | 数据类型 (Type) | 说明           | 备注                     |
| :-------------- | :-------------- | :------------- | :----------------------- |
| `username`      | `CharField`     | 用户名         | 必填，唯一               |
| `password`      | `CharField`     | 密码（已加密） | Django自动处理           |
| `email`         | `EmailField`    | 邮箱           | 必填                     |
| `gender`        | `CharField`     | 性别           | 可选。'M' (男), 'F' (女) |
| `date_of_birth` | `DateField`     | 出生日期       | 可选                     |

2. **SleepRecord (睡眠记录)**

| 字段名 (Field) | 数据类型 (Type) | 说明     | 备注                                  |
| :------------- | :-------------- | :------- | :------------------------------------ |
| `user`         | `ForeignKey`    | 所属用户 | 关联到`CustomUser`                    |
| `sleep_time`   | `DateTimeField` | 入睡时间 | 前端需提供 `YYYY-MM-DDTHH:MM:SS` 格式 |
| `wakeup_time`  | `DateTimeField` | 起床时间 | 前端需提供 `YYYY-MM-DDTHH:MM:SS` 格式 |
| `duration`     | `DurationField` | 睡眠时长 | **后端自动计算**，无需前端提供        |

3. **SportRecord (运动记录)**

| 字段名 (Field)     | 数据类型 (Type)        | 说明             | 备注                           |
| :----------------- | :--------------------- | :--------------- | :----------------------------- |
| `user`             | `ForeignKey`           | 所属用户         | 关联到`CustomUser`             |
| `sport_type`       | `CharField`            | 运动类型         | 例如 "跑步", "游泳"            |
| `duration_minutes` | `PositiveIntegerField` | 运动时长(分钟)   | 整数                           |
| `calories_burned`  | `FloatField`           | 消耗卡路里(大卡) |                                |
| `record_date`      | `DateField`            | 记录日期         | **后端自动生成**，无需前端提供 |

4. **FoodItem (食物库)**

| 字段名 (Field)      | 数据类型 (Type) | 说明               | 备注               |
| :------------------ | :-------------- | :----------------- | :----------------- |
| `name`              | `CharField`     | 食物名称           | 唯一               |
| `calories_per_100g` | `FloatField`    | 每100g卡路里(大卡) | 由管理员在后台录入 |

5. **Meal (餐次) & MealItem (餐品条目)**
一次饮食记录分为 "**一餐(Meal)**" 和 "**餐里的食物(MealItem)**" 两部分。

- **Meal (餐次)**

| 字段名 (Field)   | 数据类型 (Type) | 说明       | 备注                                    |
| :--------------- | :-------------- | :--------- | :-------------------------------------- |
| `user`           | `ForeignKey`    | 所属用户   | 关联到`CustomUser`                      |
| `meal_type`      | `CharField`     | 餐次类型   | 'breakfast', 'lunch', 'dinner', 'snack' |
| `record_date`    | `DateField`     | 记录日期   | **后端自动生成**                        |
| `total_calories` | `property`      | 该餐总热量 | **后端自动计算**                        |

- **MealItem (餐品条目)**

| 字段名 (Field)        | 数据类型 (Type) | 说明       | 备注                             |
| :-------------------- | :-------------- | :--------- | :------------------------------- |
| `meal`                | `ForeignKey`    | 所属餐次   | 关联到`Meal`                     |
| `food_item`           | `ForeignKey`    | 食物条目   | 关联到`FoodItem`，用户从库中选择 |
| `portion`             | `FloatField`    | 份量(克)   | 用户输入                         |
| `calories_calculated` | `FloatField`    | 计算卡路里 | **后端自动计算**                 |

---

##  API接口文档

以下是当前可用的后端API接口，主要供前端开发人员使用。所有接口都暂时关闭了CSRF保护，方便直接调用。

### 1. 用户注册

*   **URL**: `/api/register/`
*   **Method**: `POST`
*   **Request Body** (JSON):
    ```json
    {
        "username": "your_username",
        "password": "your_password",
        "email": "your_email@example.com"
    }
    ```
*   **Success Response** (`201 Created`):
    ```json
    {
        "status": "success",
        "message": "用户注册成功"
    }
    ```
*   **Error Response** (`400 Bad Request`):
    ```json
    {
        "status": "error",
        "message": "用户名已存在" // 或其他错误信息
    }
    ```

### 2. 用户登录

*   **URL**: `/api/login/`
*   **Method**: `POST`
*   **Request Body** (JSON):
    ```json
    {
        "username": "your_username",
        "password": "your_password"
    }
    ```
*   **Success Response** (`200 OK`):
    ```json
    {
        "status": "success",
        "message": "登录成功",
        "user_id": 1,
        "username": "your_username"
    }
    ```

### 3. 用户注销

*   **URL**: `/api/logout/`
*   **Method**: `POST`
*   **Request Body**: (Empty)
*   **Success Response** (`200 OK`):
    ```json
    {
        "status": "success",
        "message": "已成功注销"
    }
    ```
---

## 当前（第一、二阶段）开发任务

#### **成员B (后端核心)**
**目标**: 编写三大模块的数据增删改查(CRUD) API接口。

*   **任务1**: 实现睡眠记录API (`/api/sleep/`)
*   **任务2**: 实现运动记录API (`/api/sport/`)
*   **任务3**: 实现饮食记录相关API (`/api/fooditems/`, `/api/meals/`, `/api/meal-items/`)
*   **任务4**: 通过Django Admin后台录入一批常见的食物及其热量数据。

#### **成员C (前端组长)**
**目标**: 搭建网页骨架并对接后端API，让用户可以提交数据。

*   **任务1**: 搭建基础HTML模板和静态页面布局。
*   **任务2**: 将静态的注册、登录页面与后端API对接。
*   **任务3**: 创建三大模块的数据录入表单并与后端API对接。

#### **成员D (前端核心)**
**目标**: 开发主看板，为用户提供直观的数据概览。

*   **任务**: **开发系统主看板 (Dashboard)**。调用后端API获取并展示用户**当日**的健康数据概览（如今日睡眠时长、运动消耗、饮食摄入总热量等）。

#### **成员A (后端组长)**
*   **任务**: 协助 **成员B** 进行API的开发与调试，确保接口的稳定性和正确性，为前端提供支持。
---

## 协作规范

1.  **分支管理**:
    *   `main` 分支是受保护的稳定分支。
    *   所有开发工作请**创建新的特性分支**，命名规则：`feature/xxx` (例如 `feature/login-page` 或 `feature/sleep-api`)。
    *   完成开发后，通过 `Pull Request` (PR) 合并到 `main` 分支。

2.  **代码提交**:
    *   提交代码前，请确保在本地测试通过。
    *   Commit Message应清晰明了，描述本次提交的主要内容，例如 `Feat: Implement user login API` 或 `Fix: Correct sleep duration calculation`。