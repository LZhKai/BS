package org.example.back.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.example.back.entity.ParkingRecord;

/**
 * 停车记录 Mapper
 */
@Mapper
public interface ParkingRecordMapper extends BaseMapper<ParkingRecord> {
}
