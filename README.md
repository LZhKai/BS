# 智能小区车辆管理系统

## 项目简介

本项目是一个基于前后端分离架构的智能小区车辆管理系统，采用 Spring Boot + Vue3 技术栈开发。

## 技术栈

### 后端
- Spring Boot 3.0.2
- MyBatis-Plus 3.5.3.1
- MySQL 5.7+
- JWT 认证
- Lombok

### 前端
- Vue 3.3.4
- Element Plus 2.4.4
- Vue Router 4.2.5
- Axios 1.6.0
- Vite 5.0.0

## 项目结构

```
project/
├── back/                    # 后端项目
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/
│   │   │   │   └── org/example/back/
│   │   │   │       ├── common/          # 公共类
│   │   │   │       ├── config/          # 配置类
│   │   │   │       ├── controller/      # 控制器
│   │   │   │       ├── dto/             # 数据传输对象
│   │   │   │       ├── entity/          # 实体类
│   │   │   │       ├── mapper/          # Mapper接口
│   │   │   │       ├── service/         # 服务层
│   │   │   │       └── util/            # 工具类
│   │   │   └── resources/
│   │   │       ├── db/                  # 数据库脚本
│   │   │       └── application.properties
│   │   └── pom.xml
│   └── README.md
├── front/                   # 前端项目
│   ├── src/
│   │   ├── api/            # API接口
│   │   ├── layout/         # 布局组件
│   │   ├── router/         # 路由配置
│   │   ├── views/          # 页面组件
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 快速开始

### 环境要求
- JDK 17+
- Maven 3.6+
- Node.js 16+
- MySQL 5.7+

### 数据库配置

1. 创建数据库：
```sql
CREATE DATABASE vehicle_management DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. 执行数据库脚本：
```bash
# 在MySQL中执行
source back/src/main/resources/db/schema.sql
```

或者直接导入 `back/src/main/resources/db/schema.sql` 文件。

3. 修改数据库配置：
编辑 `back/src/main/resources/application.properties`，修改数据库连接信息：
```properties
spring.datasource.url=jdbc:mysql://localhost:3306/vehicle_management?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai
spring.datasource.username=root
spring.datasource.password=your_password
```

### 后端启动

1. 进入后端目录：
```bash
cd back
```

2. 编译项目：
```bash
mvn clean compile
```

3. 运行项目：
```bash
mvn spring-boot:run
```

或者使用IDE直接运行 `BackApplication.java`

后端服务将在 `http://localhost:8080` 启动

### 前端启动

1. 进入前端目录：
```bash
cd front
```

2. 安装依赖：
```bash
npm install
```

3. 启动开发服务器：
```bash
npm run dev
```

前端服务将在 `http://localhost:3000` 启动

## 默认账号

- 用户名：`admin`
- 密码：`admin123`

## API接口说明

### 认证接口
- `POST /api/auth/login` - 用户登录

### 车辆管理接口
- `GET /api/vehicle/page` - 分页查询车辆列表
- `GET /api/vehicle/{id}` - 根据ID查询车辆
- `POST /api/vehicle` - 新增车辆
- `PUT /api/vehicle/{id}` - 更新车辆信息
- `DELETE /api/vehicle/{id}` - 删除车辆
- `DELETE /api/vehicle/batch` - 批量删除车辆
- `GET /api/vehicle/list` - 获取所有车辆（不分页）

## 功能特性

- ✅ 用户登录认证（JWT）
- ✅ 车辆信息管理（CRUD）
- ✅ 车辆信息查询（支持车牌号、车主姓名、状态筛选）
- ✅ 分页查询
- ✅ 批量删除
- ✅ 响应式UI设计

## 后续开发计划

- [ ] 停车记录管理
- [ ] 车流量统计与可视化
- [ ] 实时告警功能
- [ ] 视频监控集成
- [ ] 智能问答（RAG）
- [ ] 车辆识别与车牌识别

## 注意事项

1. 首次运行前请确保数据库已创建并执行了初始化脚本
2. 默认管理员密码已加密存储在数据库中，如需修改请使用BCrypt加密后更新
3. 前端开发时已配置代理，API请求会自动转发到后端服务
4. 生产环境部署时请修改JWT密钥和数据库密码等敏感信息

## 许可证

MIT License
