package org.example.back.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import org.example.back.entity.Vehicle;

/**
 * 车辆服务接口
 */
public interface VehicleService extends IService<Vehicle> {
    /**
     * 分页查询车辆
     */
    IPage<Vehicle> pageQuery(Page<Vehicle> page, String plateNumber, String ownerName, String status);
}

