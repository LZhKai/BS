package org.example.back.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 车主实体类
 */
@Data
@TableName("vehicle_owner")
public class VehicleOwner {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String name;
    private String phone;
    private String address;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
