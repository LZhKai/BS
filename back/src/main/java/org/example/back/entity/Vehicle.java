package org.example.back.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

/**
 * 车辆实体类
 */
@Data
@TableName("vehicle")
public class Vehicle {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String plateNumber;
    private String ownerName;
    private String ownerPhone;
    private String status;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}

