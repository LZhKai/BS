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
    
    private String ownerName;
    private String ownerPhone;
    private String status;
}

