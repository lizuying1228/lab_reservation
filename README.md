# 实验室预约系统（Lab Reservation System）

一个基于 Django REST Framework 开发的实验室预约管理系统，提供用户认证、学生与实验室管理员管理、实验室管理、预约时段管理以及预约申请与审核等功能。

项目目前专注于后端 RESTful API 的开发，支持 JWT 身份认证、角色权限控制、数据过滤、分页、软删除以及预约并发处理。

## 技术栈

| 技术 | 用途 |
|---|---|
| Python 3.14+ | 开发语言 |
| Django 6.1 | Web 开发框架 |
| Django REST Framework | RESTful API |
| MySQL 8.4 | 关系型数据库 |
| Simple JWT | JWT 身份认证 |
| django-filter | API 数据过滤 |
| drf-spectacular | OpenAPI 文档生成 |
| django-environ | 环境变量管理 |
| uv | Python 项目与依赖管理 |
| Docker Compose | MySQL 容器管理 |
| mypy | 静态类型检查 |

## 功能模块

### 1. 用户与身份认证

- 用户注册、登录和退出登录
- JWT Access Token 和 Refresh Token
- 获取和修改个人资料
- 用户管理与软删除
- 基于角色的接口权限控制
- 支持 Superuser、Student 和 LabAdmin 三种身份

### 2. 学生管理

- 学生档案管理
- 学生信息查询
- 学生信息修改
- 学生档案软删除
- 学号唯一性约束

### 3. 实验室管理员管理

- 实验室管理员档案管理
- 管理员与用户账号关联
- 管理员信息查询与修改
- 管理员软删除及关联账号禁用

### 4. 实验室管理

- 实验室创建、查询、修改和软删除
- 实验室编号唯一性约束
- 实验室状态管理：
  - OPEN：开放
  - CLOSED：关闭
  - MAINTENANCE：维修
- 实验室与管理员关联
- 实验室预约历史相关业务限制

### 5. 预约时段管理

- 预约时段创建、查询、修改和软删除
- 支持上午、下午、晚上三个时段
- 预约时段状态管理：
  - AVAILABLE：可预约
  - OCCUPIED：已占用
- 仅允许为开放的实验室创建预约时段
- 预约日期限制为未来七天的预约窗口
- 同一实验室、日期和时段不能重复创建

### 6. 预约申请与审核

- 学生提交预约申请
- 实验室管理员审核预约
- 学生取消预约
- 预约状态管理：
  - PENDING：待审核
  - APPROVED：已通过
  - REJECTED：已拒绝
  - CANCELLED：已取消
- 允许同一时段存在多个待审核申请
- 审核时检查时段是否已被其他预约占用
- 预约取消后，根据其他已通过预约情况更新时段状态
- 已通过预约的取消受到对应时段开始时间限制

## 核心业务设计

### 身份与权限

系统通过自定义 User 模型管理账号，并通过 Student、LabAdmin 档案区分业务身份。

- 一个普通用户账号最多绑定一种业务身份：Student 或 LabAdmin。
- Superuser 使用 Django 内置超级用户身份区分。
- 不同身份具有不同的接口访问权限。
- 实验室管理员只能管理自己负责的实验室及相关业务。

### 软删除

用户、学生档案、管理员档案、实验室和预约时段采用软删除机制。

通过 `is_deleted` 和 `deleted_at` 字段记录删除状态与时间，避免直接删除重要业务数据。

### 预约并发控制

预约申请与审核涉及多个用户同时操作同一预约时段的情况。

系统通过数据库事务和 `select_for_update()` 行级锁控制关键业务操作，避免并发审核导致同一时段出现多个已通过预约。

同时，在事务中执行必要的业务检查和状态更新，保证预约记录与预约时段状态的一致性。

## 项目结构

```text
lab_reservation/
├── config/
│   ├── common/
│   │   ├── exceptions.py       # 全局异常处理
│   │   ├── filters.py          # 公共过滤配置
│   │   └── pagination.py       # 统一分页配置
│   ├── settings.py             # 项目配置
│   ├── urls.py                 # 项目总路由
│   ├── asgi.py
│   └── wsgi.py
│
├── users/                      # 用户与身份认证
├── students/                   # 学生管理
├── lab_admins/                 # 实验室管理员管理
├── labs/                       # 实验室管理
├── reservation_times/          # 预约时段管理
├── reservations/               # 预约申请与审核
│
├── src/
│   └── lab_reservation/
├── compose.yaml                # MySQL 容器配置
├── manage.py
├── pyproject.toml              # 项目依赖与配置
├── uv.lock                     # 依赖锁定文件
├── mypy.ini                    # mypy 配置
└── README.md
```

各业务 App 采用相对独立的结构，主要包含：

- `models.py`：数据库模型
- `serializers.py`：请求数据校验与序列化
- `views.py`：API 接口
- `services.py`：业务逻辑
- `permissions.py`：业务权限
- `urls.py`：应用路由
- `tests.py`：测试代码

## 环境要求

- Python 3.14 或更高版本
- uv
- Docker 和 Docker Compose
- MySQL 8.4（也可以使用已有的 MySQL 实例）

## 项目运行

### 1. 克隆项目

```bash
git clone <your-repository-url>
cd lab_reservation
```

### 2. 安装依赖

```bash
uv sync
```

### 3. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

MYSQL_DATABASE=lab_reservation
MYSQL_USER=lab_user
MYSQL_PASSWORD=your-database-password
MYSQL_ROOT_PASSWORD=your-root-password
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
```

请根据实际运行环境修改配置。不要将真实 `.env` 文件提交到 Git 仓库。

### 4. 启动 MySQL

```bash
docker compose up -d
```

项目通过 Docker Compose 启动 MySQL 8.4，默认将容器的 3306 端口映射到宿主机的 3307 端口。

### 5. 执行数据库迁移

```bash
uv run python manage.py migrate
```

### 6. 创建超级管理员

```bash
uv run python manage.py createsuperuser
```

### 7. 启动 Django 服务

```bash
uv run python manage.py runserver
```

默认访问地址：

```text
http://127.0.0.1:8000/
```

## API 文档

项目使用 drf-spectacular 生成 OpenAPI 接口文档。

启动服务后，可以访问：

| 文档 | 地址 |
|---|---|
| OpenAPI Schema | http://127.0.0.1:8000/api/schema/ |
| Swagger UI | http://127.0.0.1:8000/api/docs/ |
| ReDoc | http://127.0.0.1:8000/api/redoc/ |

## API 路由概览

所有业务 API 统一使用 `/api/` 前缀。

| 模块 | 路由 |
|---|---|
| 用户认证与管理 | `/api/users/` |
| 学生管理 | `/api/students/` |
| 实验室管理员管理 | `/api/labadmins/` |
| 实验室管理 | `/api/labs/` |
| 预约时段管理 | `/api/reservationtimes/` |
| 预约申请与审核 | `/api/reservations/` |

用户认证相关接口：

| 方法 | 路由 | 功能 |
|---|---|---|
| POST | `/api/users/register/` | 用户注册 |
| POST | `/api/users/login/` | 用户登录 |
| POST | `/api/users/token/refresh/` | 刷新 Token |
| POST | `/api/users/logout/` | 用户退出登录 |
| GET | `/api/users/me/` | 获取个人资料 |
| PATCH | `/api/users/me/` | 修改个人资料 |

预约业务还提供审核和取消操作，具体请求参数与响应格式以 Swagger 文档为准。

## 认证方式

项目使用 JWT 进行身份认证。

登录成功后获取 Access Token，在需要身份认证的请求中添加：

```http
Authorization: Bearer <access_token>
```

系统默认要求登录后才能访问 API，公开注册、登录等接口按照各自权限配置执行。

## 分页、过滤与异常处理

项目统一配置了：

- 默认分页：每页 8 条数据
- django-filter：支持字段过滤
- SearchFilter：支持关键词搜索
- OrderingFilter：支持排序
- 自定义全局异常处理：统一 API 异常响应格式

具体支持的过滤字段和排序字段以各接口配置为准。

## 项目状态

目前已完成后端核心业务模块、JWT 身份认证、角色权限控制、API 文档、数据库迁移以及核心预约流程测试。

已对预约审核和取消等关键业务进行并发测试，验证事务与行级锁对预约时段状态一致性的保护。

后续计划：开发配套前端界面，与现有后端 API 对接。

## License

暂未指定开源许可证。
