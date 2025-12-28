# 后端项目说明

## 快速启动

1. 确保MySQL数据库已启动，并创建数据库：
```sql
CREATE DATABASE vehicle_management DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. 执行数据库初始化脚本：
```sql
source src/main/resources/db/schema.sql
```

3. 修改 `src/main/resources/application.properties` 中的数据库连接信息

4. 运行项目：
```bash
mvn spring-boot:run
```

或者使用IDE运行 `BackApplication.java`

## 默认账号

- 用户名：admin
- 密码：admin123

## 生成新密码哈希

如果需要生成新的密码哈希值，可以运行 `PasswordGenerator.java` 的main方法。

