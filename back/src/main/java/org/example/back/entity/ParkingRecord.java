package org.example.back.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 停车记录实体类
 */
@Data
@TableName("parking_record")
public class ParkingRecord {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long vehicleId;
    private String plateNumber;
    private LocalDateTime entryTime;
    private LocalDateTime exitTime;
    private Integer parkingDuration;
    private BigDecimal parkingFee;
    private String gateNumber;
    private String status;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
