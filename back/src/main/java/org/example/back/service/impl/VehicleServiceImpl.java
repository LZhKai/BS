package org.example.back.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.example.back.entity.Vehicle;
import org.example.back.mapper.VehicleMapper;
import org.example.back.service.VehicleService;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

/**
 * 车辆服务实现类
 */
@Service
public class VehicleServiceImpl extends ServiceImpl<VehicleMapper, Vehicle> implements VehicleService {
    
    @Override
    public IPage<Vehicle> pageQuery(Page<Vehicle> page, String plateNumber, String ownerName, String status) {
        LambdaQueryWrapper<Vehicle> wrapper = new LambdaQueryWrapper<>();
        
        if (StringUtils.hasText(plateNumber)) {
            wrapper.like(Vehicle::getPlateNumber, plateNumber);
        }
        if (StringUtils.hasText(ownerName)) {
            wrapper.like(Vehicle::getOwnerName, ownerName);
        }
        if (StringUtils.hasText(status)) {
            wrapper.eq(Vehicle::getStatus, status);
        }
        
        wrapper.orderByDesc(Vehicle::getCreateTime);
        return page(page, wrapper);
    }
}

