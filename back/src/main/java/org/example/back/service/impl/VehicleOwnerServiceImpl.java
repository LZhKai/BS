package org.example.back.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.example.back.entity.VehicleOwner;
import org.example.back.mapper.VehicleOwnerMapper;
import org.example.back.service.VehicleOwnerService;
import org.springframework.stereotype.Service;

/**
 * 车主服务实现类
 */
@Service
public class VehicleOwnerServiceImpl extends ServiceImpl<VehicleOwnerMapper, VehicleOwner> implements VehicleOwnerService {
}
