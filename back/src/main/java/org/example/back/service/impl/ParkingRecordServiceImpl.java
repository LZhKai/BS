package org.example.back.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.example.back.entity.ParkingRecord;
import org.example.back.mapper.ParkingRecordMapper;
import org.example.back.service.ParkingRecordService;
import org.springframework.stereotype.Service;

/**
 * 停车记录服务实现类
 */
@Service
public class ParkingRecordServiceImpl extends ServiceImpl<ParkingRecordMapper, ParkingRecord> implements ParkingRecordService {
}
