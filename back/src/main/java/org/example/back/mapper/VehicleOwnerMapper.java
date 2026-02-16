package org.example.back.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.example.back.entity.VehicleOwner;

/**
 * 车主 Mapper
 */
@Mapper
public interface VehicleOwnerMapper extends BaseMapper<VehicleOwner> {
}
