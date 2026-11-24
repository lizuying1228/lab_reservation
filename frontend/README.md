# 实验室预约管理系统前端

Vue 3 + TypeScript + Vite + Element Plus + Pinia + Axios。该项目连接现有 Django REST Framework 后端，不包含对后端业务逻辑的替代实现。

## 启动

要求 Node.js 20+。

```bash
npm install
cp .env.example .env
# 按实际后端地址修改 VITE_API_BASE_URL
npm run dev
```

默认后端地址：`http://127.0.0.1:8000/api`。开发服务器通常运行在 `http://localhost:5173`。如果前后端不同源，需要在 Django 后端配置允许该前端来源的 CORS。

## 构建

```bash
npm run build
npm run preview
```

## 页面与业务覆盖

- 登录、注册、JWT Access/Refresh 自动刷新、退出登录
- 个人资料查询和邮箱/手机号修改
- 工作台：预约数、待审核数、实验室数、可预约时段数、最近预约
- 预约管理：按状态/关键词筛选；学生申请预约、取消自己的预约；管理员审核通过/拒绝
- 实验室管理：列表、新建、软删除；避免在前端提供绕过后端状态变更规则的通用编辑入口
- 预约时段：列表、新建、软删除；时段使用后端的 `morning`、`afternoon`、`evening` 值
- 学生档案：列表、新建（绑定已有用户或同时创建账号）、编辑姓名/出生日期、软删除
- 实验室管理员：列表、新建账号和档案、编辑姓名/出生日期、软删除
- 用户管理：查看用户、软删除用户
- 资源列表分页、搜索；角色菜单和路由限制仅用于界面体验，最终权限仍由后端控制

## 对接的后端 API

- `/api/users/`：register、login、token/refresh、logout、me、用户列表/删除
- `/api/students/`、`/api/labadmins/`、`/api/labs/`、`/api/reservationtimes/`
- `/api/reservations/`：创建时提交 `reservationtime_id`；审核 PATCH `/{id}/review/`，提交 `status: approved | rejected`；取消 PATCH `/{id}/cancel/`

## 注意

1. 前端不会绕过后端权限和业务校验。预约冲突、七天预约窗口、时段取消截止时间、管理员归属、实验室状态通知等规则仍以 Django 服务端校验为准。
2. 当前前端按后端序列化器定义的字段提交数据；如果后端接口字段发生变化，需要同步调整 `src/views` 中对应页面。
3. 本项目不包含 Django 后端，也不会自动修改后端 CORS、数据库或环境变量配置。
