-- 智能小区车辆管理系统数据库表结构

-- 用户表
CREATE TABLE IF NOT EXISTS `sys_user` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` VARCHAR(50) NOT NULL COMMENT '用户名',
  `password` VARCHAR(255) NOT NULL COMMENT '密码',
  `real_name` VARCHAR(50) DEFAULT NULL COMMENT '真实姓名',
  `phone` VARCHAR(20) DEFAULT NULL COMMENT '手机号',
  `role` VARCHAR(20) DEFAULT 'USER' COMMENT '角色：ADMIN-管理员，USER-普通用户',
  `status` TINYINT DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 车辆表
CREATE TABLE IF NOT EXISTS `vehicle` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '车辆ID',
  `plate_number` VARCHAR(20) NOT NULL COMMENT '车牌号',
  `owner_name` VARCHAR(50) DEFAULT NULL COMMENT '车主姓名',
  `owner_phone` VARCHAR(20) DEFAULT NULL COMMENT '车主电话',
  `status` VARCHAR(20) DEFAULT 'NORMAL' COMMENT '状态：NORMAL-正常，BLACKLIST-黑名单，EXPIRED-过期',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_plate_number` (`plate_number`),
  KEY `idx_owner_phone` (`owner_phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='车辆表';

-- 插入默认管理员用户（密码：admin123，明文存储）
INSERT INTO `sys_user` (`username`, `password`, `real_name`, `role`, `status`) 
VALUES ('admin', 'admin123', '系统管理员', 'ADMIN', 1);

-- 插入车辆测试数据
INSERT INTO `vehicle` (`plate_number`, `owner_name`, `owner_phone`, `status`) VALUES
('京A12345', '张三', '13800138001', 'NORMAL'),
('京B67890', '李四', '13800138002', 'NORMAL'),
('京C11111', '王五', '13800138003', 'NORMAL'),
('京D22222', '赵六', '13800138004', 'NORMAL'),
('京E33333', '钱七', '13800138005', 'NORMAL'),
('京F44444', '孙八', '13800138006', 'BLACKLIST'),
('京G55555', '周九', '13800138007', 'NORMAL'),
('京H66666', '吴十', '13800138008', 'EXPIRED'),
('京J77777', '郑一', '13800138009', 'NORMAL'),
('京K88888', '王二', '13800138010', 'NORMAL'),
('京L99999', '李三', '13800138011', 'NORMAL'),
('京M00000', '张四', '13800138012', 'BLACKLIST'),
('沪A12345', '刘五', '13900139001', 'NORMAL'),
('沪B67890', '陈六', '13900139002', 'NORMAL'),
('粤A12345', '黄七', '13700137001', 'NORMAL');

