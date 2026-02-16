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

-- 车主表
CREATE TABLE IF NOT EXISTS `vehicle_owner` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '车主ID',
  `name` VARCHAR(50) NOT NULL COMMENT '车主姓名',
  `phone` VARCHAR(20) DEFAULT NULL COMMENT '手机号',
  `address` VARCHAR(200) DEFAULT NULL COMMENT '地址',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_phone` (`phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='车主表';

-- 车辆表（关联车主表）
CREATE TABLE IF NOT EXISTS `vehicle` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '车辆ID',
  `plate_number` VARCHAR(20) NOT NULL COMMENT '车牌号',
  `owner_id` BIGINT DEFAULT NULL COMMENT '车主ID',
  `owner_name` VARCHAR(50) DEFAULT NULL COMMENT '车主姓名（冗余，便于列表展示）',
  `owner_phone` VARCHAR(20) DEFAULT NULL COMMENT '车主电话（冗余）',
  `brand_model` VARCHAR(100) DEFAULT NULL COMMENT '品牌型号',
  `description` TEXT DEFAULT NULL COMMENT '车辆特性描述（可写较多内容）',
  `status` VARCHAR(20) DEFAULT 'NORMAL' COMMENT '状态：NORMAL-正常，BLACKLIST-黑名单，EXPIRED-过期',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_plate_number` (`plate_number`),
  KEY `idx_owner_id` (`owner_id`),
  KEY `idx_owner_phone` (`owner_phone`),
  CONSTRAINT `fk_vehicle_owner` FOREIGN KEY (`owner_id`) REFERENCES `vehicle_owner` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='车辆表';

-- 停车记录表（关联车辆表）
CREATE TABLE IF NOT EXISTS `parking_record` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `vehicle_id` BIGINT NOT NULL COMMENT '车辆ID',
  `plate_number` VARCHAR(20) NOT NULL COMMENT '车牌号',
  `entry_time` DATETIME NOT NULL COMMENT '进入时间',
  `exit_time` DATETIME DEFAULT NULL COMMENT '离开时间',
  `parking_duration` INT DEFAULT NULL COMMENT '停车时长（分钟）',
  `parking_fee` DECIMAL(10,2) DEFAULT 0.00 COMMENT '停车费用',
  `gate_number` VARCHAR(20) DEFAULT NULL COMMENT '出入口编号',
  `status` VARCHAR(20) DEFAULT 'PARKING' COMMENT '状态：PARKING-停车中，EXITED-已离开',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_vehicle_id` (`vehicle_id`),
  KEY `idx_plate_number` (`plate_number`),
  KEY `idx_entry_time` (`entry_time`),
  CONSTRAINT `fk_parking_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicle` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='停车记录表';

-- 插入默认管理员用户（密码：admin123，明文存储）
INSERT INTO `sys_user` (`username`, `password`, `real_name`, `role`, `status`) 
VALUES ('admin', 'admin123', '系统管理员', 'ADMIN', 1);

-- 插入车主测试数据
INSERT INTO `vehicle_owner` (`name`, `phone`, `address`) VALUES
('张三', '13800138001', '1号楼101'),
('李四', '13800138002', '2号楼202'),
('王五', '13800138003', '3号楼303');

-- 插入车辆测试数据（关联车主）
INSERT INTO `vehicle` (`plate_number`, `owner_id`, `owner_name`, `owner_phone`, `brand_model`, `description`, `status`) VALUES
('京A12345', 1, '张三', '13800138001', '大众帕萨特', '黑色轿车，常停地库A区，车况良好。', 'NORMAL'),
('京B67890', 2, '李四', '13800138002', '丰田汉兰达', '白色SUV，七座，经常周末出行。', 'NORMAL'),
('京C11111', 3, '王五', '13800138003', '别克GL8', '银色商务车，用于接送客户。', 'NORMAL'),
('京D22222', NULL, '赵六', '13800138004', '本田雅阁', '深灰色轿车，地库B区固定车位。', 'NORMAL'),
('京E33333', NULL, '钱七', '13800138005', '比亚迪汉EV', '新能源绿牌，充电桩在B1-12。', 'NORMAL'),
('京F44444', NULL, '孙八', '13800138006', '长城哈弗H6', '红色SUV，曾多次占用他人车位，已列入黑名单。', 'BLACKLIST'),
('京G55555', NULL, '周九', '13800138007', '日产轩逸', '白色家用轿车，工作日早出晚归。', 'NORMAL'),
('京H66666', NULL, '吴十', '13800138008', '奥迪A4L', '蓝色轿车，月卡已过期待续费。', 'EXPIRED'),
('京J77777', NULL, '郑一', '13800138009', '特斯拉Model 3', '黑色纯电动，常停地面充电位。', 'NORMAL'),
('京K88888', NULL, '王二', '13800138010', '宝马3系', '白色运动型轿车，地库C区。', 'NORMAL'),
('京L99999', NULL, '李三', '13800138011', '吉利博越', '棕色SUV，家庭用车。', 'NORMAL'),
('京M00000', NULL, '张四', '13800138012', '现代伊兰特', '灰色轿车，多次违规停车已拉黑。', 'BLACKLIST'),
('沪A12345', NULL, '刘五', '13900139001', '荣威RX5', '白色紧凑型SUV，上海牌照。', 'NORMAL'),
('沪B67890', NULL, '陈六', '13900139002', '大众朗逸', '银色轿车，临时访客车辆登记。', 'NORMAL'),
('粤A12345', NULL, '黄七', '13700137001', '广汽传祺GS8', '黑色七座SUV，广东牌照。', 'NORMAL'),
('京N11111', NULL, '林八', '13600136001', '小鹏P7', '灰色新能源轿跑，地库有固定充电桩。', 'NORMAL'),
('京P22222', NULL, '何九', '13500135001', '理想ONE', '绿色增程式SUV，六座家用。', 'NORMAL'),
('京Q33333', NULL, '徐十', '13400134001', '奔驰E级', '黑色商务轿车，地库A区VIP位。', 'NORMAL'),
('浙A12345', NULL, '沈一', '13300133001', '领克01', '蓝色SUV，杭州牌照访客。', 'NORMAL'),
('苏A67890', NULL, '韩二', '13200132001', '奇瑞瑞虎8', '白色中型SUV，南京牌照。', 'NORMAL');

-- 插入停车记录
INSERT INTO `parking_record` (`vehicle_id`, `plate_number`, `entry_time`, `exit_time`, `parking_duration`, `parking_fee`, `gate_number`, `status`) VALUES
(1, '京A12345', '2025-02-16 08:00:00', NULL, NULL, 0.00, '东门入口', 'PARKING'),
(2, '京B67890', '2025-02-16 07:30:00', '2025-02-16 18:45:00', 675, 25.00, '东门入口', 'EXITED'),
(3, '京C11111', '2025-02-15 09:00:00', '2025-02-15 17:30:00', 510, 18.00, '南门入口', 'EXITED'),
(4, '京D22222', '2025-02-16 06:50:00', NULL, NULL, 0.00, '西门入口', 'PARKING'),
(5, '京E33333', '2025-02-16 00:20:00', NULL, NULL, 0.00, '东门入口', 'PARKING'),
(7, '京G55555', '2025-02-15 22:10:00', '2025-02-16 07:00:00', 530, 15.00, '北门入口', 'EXITED'),
(9, '京J77777', '2025-02-16 09:15:00', NULL, NULL, 0.00, '东门入口', 'PARKING'),
(10, '京K88888', '2025-02-14 10:00:00', '2025-02-14 20:30:00', 630, 22.00, '南门入口', 'EXITED'),
(11, '京L99999', '2025-02-16 08:30:00', NULL, NULL, 0.00, '西门入口', 'PARKING'),
(12, '京M00000', '2025-02-13 14:00:00', '2025-02-13 16:30:00', 150, 8.00, '东门入口', 'EXITED'),
(13, '沪A12345', '2025-02-15 12:00:00', '2025-02-16 09:00:00', 1260, 45.00, '南门入口', 'EXITED'),
(14, '沪B67890', '2025-02-16 11:00:00', NULL, NULL, 0.00, '东门入口', 'PARKING'),
(15, '粤A12345', '2025-02-16 10:20:00', NULL, NULL, 0.00, '北门入口', 'PARKING'),
(16, '京N11111', '2025-02-15 18:00:00', '2025-02-16 08:00:00', 840, 30.00, '东门入口', 'EXITED'),
(17, '京P22222', '2025-02-16 07:00:00', NULL, NULL, 0.00, '西门入口', 'PARKING'),
(1, '京A12345', '2025-02-14 08:30:00', '2025-02-14 19:00:00', 630, 22.00, '东门入口', 'EXITED'),
(2, '京B67890', '2025-02-13 09:00:00', '2025-02-13 18:30:00', 570, 20.00, '南门入口', 'EXITED'),
(5, '京E33333', '2025-02-14 23:00:00', '2025-02-15 07:30:00', 510, 15.00, '东门入口', 'EXITED'),
(18, '京Q33333', '2025-02-16 06:00:00', NULL, NULL, 0.00, '地库专用', 'PARKING'),
(19, '浙A12345', '2025-02-16 14:00:00', NULL, NULL, 0.00, '南门入口', 'PARKING');

