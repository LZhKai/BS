package org.example.back.dto;

import lombok.Data;
import jakarta.validation.constraints.NotBlank;

/**
 * 车辆DTO
 */
@Data
public class VehicleDTO {
    private Long id;
    
    @NotBlank(message = "车牌号不能为空")
    private String plateNumber;
    
    private Long ownerId;
    private String ownerName;
    private String ownerPhone;
    /** 品牌型号 */
    private String brandModel;
    /** 车辆特性描述 */
    private String description;
    private String status;
}

