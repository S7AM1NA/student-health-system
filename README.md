# Python大作业 学生健康管理系统

BUAA_2025

## 项目当前进度

**必做项目大部分完成**。项目的基础架构已经搭建完毕。

*   ✅ **项目初始化**: 已创建Django项目及核心`core`应用。
*   ✅ **数据库模型**: 已定义 `CustomUser`, `SleepRecord`, `SportRecord`, `FoodItem`, `Meal`, `MealItem` 模型并完成首次数据库迁移。
*   ✅ **版本控制**: 项目已初始化为Git仓库，并与远程GitHub仓库关联。
*   ✅ **基础用户API**: 已完成用户**注册、登录、注销**的后端API接口，可供前端调用。
*   ✅ **健康记录API**: 已完成用户增删改查**睡眠、运动、饮食**的后端API接口，可供前端调用。
*   ✅ **前端基本骨架**: 前端已完成开发目录、页脚、主看板以及各个健康信息的页面。并已与后端API对接。

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

6.  **创建本地管理员账号**
    
    ```
    python manage.py createsuperuser
    ```
    
    
    现在，可以访问 `http://127.0.0.1:8000/admin/` 后台管理界面查看和管理数据。
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

| 字段名 (Field)     | 数据类型 (Type)        | 说明             | 备注                                       |
| :----------------- | :--------------------- | :--------------- | :----------------------------------------- |
| `user`             | `ForeignKey`           | 所属用户         | 关联到`CustomUser`                         |
| `sport_type`       | `CharField`            | 运动类型         | 例如 "跑步", "游泳"                        |
| `duration_minutes` | `PositiveIntegerField` | 运动时长(分钟)   | 整数                                       |
| `calories_burned`  | `FloatField`           | 消耗卡路里(大卡) |                                            |
| `record_date`      | `DateField`            | 记录日期         | **前端提供**。前端默认为当天，用户可修改。 |

4. **FoodItem (食物库)**

| 字段名 (Field)      | 数据类型 (Type) | 说明               | 备注               |
| :------------------ | :-------------- | :----------------- | :----------------- |
| `name`              | `CharField`     | 食物名称           | 唯一               |
| `calories_per_100g` | `FloatField`    | 每100g卡路里(大卡) | 由管理员在后台录入 |

5. **Meal (餐次) & MealItem (餐品条目)**
一次饮食记录分为 "**一餐(Meal)**" 和 "**餐里的食物(MealItem)**" 两部分。

- **Meal (餐次)**

| 字段名 (Field)   | 数据类型 (Type) | 说明       | 备注                                       |
| :--------------- | :-------------- | :--------- | :----------------------------------------- |
| `user`           | `ForeignKey`    | 所属用户   | 关联到`CustomUser`                         |
| `meal_type`      | `CharField`     | 餐次类型   | 'breakfast', 'lunch', 'dinner', 'snack'    |
| `record_date`    | `DateField`     | 记录日期   | **前端提供**。前端默认为当天，用户可修改。 |
| `total_calories` | `property`      | 该餐总热量 | **后端自动计算**                           |

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

**除注册和登录接口外，以下所有API都需要用户处于登录状态才能访问。**

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
    
### **4. 用户个人档案 (Profile)**

*   **Endpoint**: `/api/profile/`
*   **核心**: 管理当前登录用户的个人详细信息。

| 操作             | Method | URL             | 说明                     |
| :--------------- | :----- | :-------------- | :----------------------- |
| **获取个人档案** | `GET`  | `/api/profile/` | 获取当前用户的详细档案。 |
| **更新个人档案** | `PUT`  | `/api/profile/` | 更新当前用户的档案信息。 |

* **更新 (PUT) Request Body**: (只需提供需要修改的字段)

  ```json
  {
      "email": "new_email@example.com",
      "gender": "F",
      "date_of_birth": "2001-05-20"
  }
  ```

* **响应 (GET/PUT) Body**:

  ```json
  {
      "username": "your_username",
      "email": "new_email@example.com",
      "gender": "F",
      "date_of_birth": "2001-05-20"
  }
  ```

### **5. 睡眠记录 (Sleep Records)**

*   **Endpoint**: `/api/sleep/`
*   **核心**: 管理当前登录用户的睡眠记录。

| 操作             | Method        | URL                       | 说明                               |
| :--------------- | :------------ | :------------------------ | :--------------------------------- |
| **获取列表**     | `GET`         | `/api/sleep/`             | 获取该用户的所有睡眠记录。         |
| **检查今日记录** | `GET`         | `/api/sleep/today-check/` | 轻量级接口，检查今天是否已有记录。 |
| **创建新记录**   | `POST`        | `/api/sleep/`             | 新增一条睡眠记录。                 |
| **获取单条详情** | `GET`         | `/api/sleep/{id}/`        | 查看某条具体记录的详情。           |
| **更新记录**     | `PUT`/`PATCH` | `/api/sleep/{id}/`        | 更新某条记录。                     |
| **删除记录**     | `DELETE`      | `/api/sleep/{id}/`        | 删除某条记录。                     |

*   **筛选功能**:
    
    *   此列表接口支持按**起床日期**筛选: `GET /api/sleep/?record_date=2025-07-31`
*   **创建 (POST) Request Body**:
    
    ```json
    {
        "sleep_time": "2025-07-29T23:00:00",
        "wakeup_time": "2025-07-30T07:30:00"
    }
    ```
*   **响应 (GET/POST/PUT/PATCH) Body**:
    
    ```json
    {
        "id": 1,
        "sleep_time": "2025-07-29T23:00:00Z",
        "wakeup_time": "2025-07-30T07:30:00Z",
        "duration": "08:30:00"
    }
    ```

### **6. 运动记录 (Sport Records)**

*   **Endpoint**: `/api/sports/`
*   **核心**: 管理用户的运动记录。接口结构与睡眠记录相同。

| 操作             | Method        | URL                        | 说明                       |
| :--------------- | :------------ | :------------------------- | :------------------------- |
| **获取列表**     | `GET`         | `/api/sports/`             | 获取该用户的所有运动记录。 |
| **检查今日记录** | `GET`         | `/api/sports/today-check/` | 检查今天是否已有运动记录。 |
| **创建新记录**   | `POST`        | `/api/sports/`             | 新增一条运动记录。         |
| **获取单条详情** | `GET`         | `/api/sports/{id}/`        | 查看某条具体记录的详情。   |
| **更新记录**     | `PUT`/`PATCH` | `/api/sports/{id}/`        | 更新某条记录。             |
| **删除记录**     | `DELETE`      | `/api/sports/{id}/`        | 删除某条记录。             |

* **筛选功能**:

  *   此列表接口支持按**记录日期**筛选: `GET /api/sports/?record_date=2025-07-31`

* **检查今日记录 (GET `/today-check/`) 响应**:

  ```json
  { "record_exists": true, "record_id": 45 }
  ```

* **创建 (POST) Request Body**:

  ```json
  {
      "sport_type": "跑步",
      "duration_minutes": 30,
      "calories_burned": 250.5,
      "record_date": "2025-07-28"
  }
  ```

* **响应 Body**:

  ```json
  {
      "id": 1,
      "sport_type": "跑步",
      "duration_minutes": 30,
      "calories_burned": 250.5,
      "record_date": "2025-07-28"
  }
  ```

### **7. 食物库 (Food Items)**

*   **Endpoint**: `/api/foods/`
*   **核心**: **只读接口**，用于搜索和展示食物库信息。

| 操作             | Method | URL                | 说明                       |
| :--------------- | :----- | :----------------- | :------------------------- |
| **获取列表**     | `GET`  | `/api/foods/`      | 获取食物库列表，支持搜索。 |
| **获取单条详情** | `GET`  | `/api/foods/{id}/` | 查看某个食物的详细信息。   |

*   **响应 Body**:
    ```json
    {
        "id": 101,
        "name": "苹果",
        "calories_per_100g": 52.0
    }
    ```

### **8. 饮食记录 (Meals & Meal Items)**

#### **8.1 餐次 (Meal)**

*   **Endpoint**: `/api/meals/`
*   **核心**: 管理一餐的整体信息，如“早餐”、“午餐”。

| 操作             | Method | URL                       | 说明                                       |
| :--------------- | :----- | :------------------------ | :----------------------------------------- |
| **获取列表**     | `GET`  | `/api/meals/`             | 获取该用户的所有餐次记录。                 |
| **检查今日记录** | `GET`  | `/api/meals/today-check/` | 检查今天是否已有任何餐次记录。             |
| **创建新记录**   | `POST` | `/api/meals/`             | 新增一条餐次记录。                         |
| ...              | ...    | `/api/meals/{id}/`        | 其他 `GET`/`PUT`/`DELETE` 操作与之前相同。 |

* **筛选功能**:

  此列表接口支持通过 URL 查询参数进行灵活的筛选：

  * **按记录日期 (`record_date`) 筛选**，获取指定日期的所有餐次记录：

    ```
    GET /api/meals/?record_date=2025-07-31
    ```

  * **按餐次类型 (`meal_type`) 筛选**，获取所有指定类型的餐次记录（例如，所有午餐）：

    ```
    GET /api/meals/?meal_type=lunch
    ```

  * **组合筛选**，同时按日期和餐次类型进行精确查找：

    ```
    GET /api/meals/?record_date=2025-07-31&meal_type=lunch
    ```

  

* **检查今日记录 (GET `/today-check/`) 响应**:

  ```json
  { "record_exists": true, "record_id": 25 }
  ```

* **创建 (POST) Request Body**:

  ```json
  {
      "meal_type": "breakfast", // 'breakfast', 'lunch', 'dinner', 'snack'
      "record_date": "2025-07-28"
  }
  ```

* **获取列表/详情 (GET) 响应 Body**:

  ```json
  {
      "id": 25,
      "user": 1,
      "meal_type": "breakfast",
      "record_date": "2025-07-28",
      "total_calories": 354.0,
      "meal_items": [
          {
              "id": 50,
              "meal": 25,
              "food_item": 101,
              "food_item_name": "苹果",
              "portion": 150.0,
              "calories_calculated": 78.0
          }
      ]
  }
  ```

#### **8.2 餐品条目 (MealItem)**

*   **Endpoint**: `/api/meal-items/`
*   **核心**: 向一个**已存在**的餐次中添加、修改或删除具体的食物条目。

*   **创建 (POST) Request Body**:
    ```json
    {
        "meal": 25, // 必须提供所属餐次的ID
        "food_item": 102, // 必须提供食物库中食物的ID
        "portion": 250.0 // 份量（克）
    }
    ```
*   **响应 Body**:
    ```json
    {
        "id": 51,
        "meal": 25,
        "food_item": 102,
        "food_item_name": "牛奶",
        "portion": 250.0,
        "calories_calculated": 276.0
    }
    ```

### **9. 每日健康看板 (Dashboard)**

*   **URL**: `/api/dashboard/{date_str}/`
*   **Method**: `GET`
*   **URL 参数**: `date_str` - 必需。格式为 `YYYY-MM-DD` 的日期字符串。
*   **核心**: 获取指定日期的综合健康数据看板。
*   **Success Response (`200 OK`)**:
    ```json
    {
        "status": "success",
        "message": "2025-07-28 的健康数据获取成功",
        "user": { "username": "your_username", "user_id": 1 },
        "data": {
            "date": "2025-07-28",
            "sleep": {
                    "duration_hours": 6.47,
                    "sleep_time": "2025-07-28T00:32:00",
                    "wakeup_time": "2025-07-28T07:10:00",
                    "record_exists": true
            },
            "sports": {
                "total_calories_burned": 250.5,
                "total_duration_minutes": 30,
                "count": 1,
                "record_exists": true
            },
            "diet": {
                "total_calories_eaten": 2100.0,
                "record_exists": true
            },
            "health_summary": {
                "suggestion": "今天摄入的热量有点多哦，注意控制饮食！",
                "status_code": "HIGH_INTAKE"
            }
        }
    }
    ```
    
    ### **10. 周度睡眠数据报告 (Weekly Sleep Report)**
    
    *   **URL**: `/api/reports/weekly-sleep/{end_date_str}/`
    *   **Method**: `GET`
    *   **Authentication**: 需要 (Authentication Required)
    *   **URL 参数**:
        *   `end_date_str` - **必需**。报告周期的结束日期，格式为 `YYYY-MM-DD`。API将返回此日期（含）及之前6天，共7天的数据。
    *   **核心功能**: 获取一个连续7天的睡眠时长列表，主要用于前端渲染可视化图表，如柱状图。此API经过时区优化，能可靠地处理跨天记录。
    *   **Success Response (`200 OK`)**:
        ```json
        {
            "status": "success",
            "message": "获取 2023-10-21 到 2023-10-27 的睡眠数据成功",
            "data": [
                {
                    "date": "2023-10-21",
                    "duration_hours": 0
                },
                {
                    "date": "2023-10-22",
                    "duration_hours": 7.5
                },
                {
                    "date": "2023-10-23",
                    "duration_hours": 8.1
                },
                {
                    "date": "2023-10-24",
                    "duration_hours": 6.8
                },
                {
                    "date": "2023-10-25",
                    "duration_hours": 0
                },
                {
                    "date": "2023-10-26",
                    "duration_hours": 7.2
                },
                {
                    "date": "2023-10-27",
                    "duration_hours": 7.9
                }
            ]
        }
        ```
    *   **字段说明**:
        *   `data`: 一个包含7个对象的数组，代表从 `end_date_str` 倒推的连续7天。
        *   `data.date`: 日期字符串 (`YYYY-MM-DD`)。
        *   `data.duration_hours`: 该日的睡眠时长（单位：小时）。**如果当天没有记录，则为 `0`**，确保前端可以稳定渲染。
    *   **Error Response (`400 Bad Request`)**:
        ```json
        {
            "status": "error",
            "message": "日期格式错误，请使用 YYYY-MM-DD"
        }
        ```
        *   当 `end_date_str` 格式不正确时返回。
    
    ### **11. 周期性综合健康报告 (Periodic Health Report)**
    
    *   **URL**: `/api/reports/health-summary/`
    *   **Method**: `GET`
    *   **Authentication**: 需要 (Authentication Required)
    *   **URL 参数**: 无
    *   **Query Parameters**:
        *   `start_date` - **必需**。报告周期的开始日期，格式为 `YYYY-MM-DD`。
        *   `end_date` - **必需**。报告周期的结束日期，格式为 `YYYY-MM-DD`。
    *   **核心功能**: 生成一个指定时间周期内的、高度详细的健康分析报告。报告会对睡眠、运动、饮食三个维度进行独立评分和深度分析，并最终给出一个综合评分、热量平衡分析和智能化的优先改进建议。
    *   **Success Response (`200 OK`)**:
        ```json
        {
            "status": "success",
            "report": {
                "period": {
                    "start_date": "2023-10-20",
                    "end_date": "2023-10-26",
                    "total_days": 7
                },
                "overall_summary": {
                    "title": "基本均衡，但有提升空间",
                    "overall_score": 72,
                    "calorie_balance": {
                        "average_intake": 2057,
                        "average_activity_burn": 250,
                        "estimated_bmr": 1800,
                        "net_calories": 7,
                        "comment": "热量基本平衡"
                    },
                    "priority_suggestions": [
                        "本周期您需要在“饮食”方面投入更多关注。",
                        "日均热量摄入 2057 大卡，可能偏高。请关注高热量食物的摄入。",
                        "晚餐热量占比较高，建议将更多热量分配到早餐和午餐。"
                    ]
                },
                "sleep_analysis": {
                    "score": 82,
                    "suggestions": [ "...", "..." ],
                    "record_count": 7,
                    "average_duration_hours": 7.6,
                    "consistency": {
                        "sleep_time_std_dev_minutes": 55,
                        "wakeup_time_std_dev_minutes": 48,
                        "comment": "作息规律性一般"
                    },
                    "extremes": {
                        "shortest_sleep_hours": 6.5,
                        "longest_sleep_hours": 8.9
                    },
                    "data_coverage_percent": 100
                },
                "sports_analysis": {
                    "score": 70,
                    "suggestions": [ "..." ],
                    "record_count": 4,
                    "total_duration_minutes": 120,
                    "total_calories_burned": 1750,
                    "frequency_per_week": 4.0,
                    "most_frequent_activity": "跑步",
                    "data_coverage_percent": 57
                },
                "diet_analysis": {
                    "score": 60,
                    "suggestions": [ "...", "..." ],
                    "average_daily_calories": 2057,
                    "calorie_distribution": {
                        "breakfast": 3500,
                        "lunch": 5200,
                        "dinner": 5700,
                        "snack": 0
                    },
                    "data_coverage_percent": 100
                }
            }
        }
        ```
    *   **字段说明**:
        *   `report.period`: 报告覆盖的周期信息。
            *   `total_days`: 周期内的总天数。
        *   `report.overall_summary`: 报告的整体摘要。
            *   `title`: 基于总分的报告标题，如 "优秀！健康生活方式的典范"。
            *   `overall_score`: 综合健康得分 (0-100)，由各分项加权计算。
            *   `calorie_balance`: 热量平衡分析。
                *   `average_intake`: 周期内日均摄入热量 (大卡)。
                *   `average_activity_burn`: 周期内日均运动消耗热量 (大卡)。
                *   `estimated_bmr`: 估算的基础代谢率 (大卡)。
                *   `net_calories`: 净热量差值 (`摄入 - 运动消耗 - 基础代谢`)。
                *   `comment`: 基于 `net_calories` 的一个简短评价，如 "热量盈余" 或 "热量亏损"。
            *   `priority_suggestions`: 一个建议数组，**优先展示得分最低维度的建议**，帮助用户聚焦核心问题。
        *   `report.sleep_analysis`: 睡眠维度的详细分析。
            *   `score`: 睡眠健康得分 (0-100)。
            *   `suggestions`: 针对睡眠的建议列表。
            *   `record_count`: 周期内睡眠记录的总条数。
            *   `average_duration_hours`: 平均睡眠时长 (小时)。
            *   `consistency`: 睡眠规律性分析。
                *   `sleep_time_std_dev_minutes`: 入睡时间的标准差 (分钟)，值越小越规律。
                *   `wakeup_time_std_dev_minutes`: 起床时间的标准差 (分钟)。
                *   `comment`: 基于标准差的规律性评价，如 "作息非常规律"。
            *   `extremes`: 极值数据。
                *   `shortest_sleep_hours`: 最短一次睡眠的时长。
                *   `longest_sleep_hours`: 最长一次睡眠的时长。
            *   `data_coverage_percent`: 数据记录覆盖率，即有睡眠记录的天数占总天数的百分比。
        *   `report.sports_analysis`: 运动维度的详细分析。
            *   `score`: 运动健康得分 (0-100)。
            *   `total_duration_minutes`: 周期内总运动时长 (分钟)。
            *   `total_calories_burned`: 周期内总消耗热量 (大卡)。
            *   `frequency_per_week`: 每周等效运动次数。
            *   `most_frequent_activity`: 周期内最常进行的运动类型。
        *   `report.diet_analysis`: 饮食维度的详细分析。
            *   `score`: 饮食健康得分 (0-100)。
            *   `average_daily_calories`: 日均摄入热量 (大卡)。
            *   `calorie_distribution`: 周期内总热量的餐次分布情况 (大卡)。
    *   **Error Responses (`400 Bad Request`)**:
        *   当 `start_date` 或 `end_date` 缺失时:
            ```json
            { "status": "error", "message": "必须提供 start_date 和 end_date 查询参数" }
            ```
        *   当日期格式不正确时:
            ```json
            { "status": "error", "message": "日期格式错误，请使用 YYYY-MM-DD" }
            ```
        *   当 `start_date` 在 `end_date` 之后时:
            ```json
            { "status": "error", "message": "开始日期不能晚于结束日期" }
            ```
---

## 当前（必做阶段）开发任务

**前端：**

1.  在“睡眠”页面，调用后端的图表数据API，使用Chart.is绘制一个漂亮的周度睡眠时长折线图或柱状图。
2. 创建一个新的“健康报告"页面，调用报告API，展示一周数据汇总，并将后端生成的文本报告美化后展示出来。

---

## 协作规范

1.  **分支管理**:
    *   `main` 分支是受保护的稳定分支。
    *   所有开发工作请**创建新的特性分支**，命名规则：`feature/xxx` (例如 `feature/login-page` 或 `feature/sleep-api`)。
    *   完成开发后，通过 `Pull Request` (PR) 合并到 `main` 分支。

2.  **代码提交**:
    *   提交代码前，请确保在本地测试通过。
    *   Commit Message应清晰明了，描述本次提交的主要内容，例如 `Feat: Implement user login API` 或 `Fix: Correct sleep duration calculation`。