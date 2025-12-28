package org.example.back.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.example.back.entity.Vehicle;
import org.apache.ibatis.annotations.Mapper;

/**
 * 车辆Mapper
 */
@Mapper
public interface VehicleMapper extends BaseMapper<Vehicle> {
}

