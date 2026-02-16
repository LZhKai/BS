package org.example.back.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.example.back.common.PageResult;
import org.example.back.common.Result;
import org.example.back.entity.ParkingRecord;
import org.example.back.service.ParkingRecordService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 停车记录控制器
 */
@RestController
@RequestMapping("/api/parking")
@CrossOrigin(origins = "*")
public class ParkingRecordController {

    @Autowired
    private ParkingRecordService parkingRecordService;

    @GetMapping("/page")
    public Result<PageResult<ParkingRecord>> page(
            @RequestParam(defaultValue = "1") Long current,
            @RequestParam(defaultValue = "10") Long size,
            @RequestParam(required = false) Long vehicleId,
            @RequestParam(required = false) String plateNumber,
            @RequestParam(required = false) String status) {
        Page<ParkingRecord> page = new Page<>(current, size);
        var wrapper = new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<ParkingRecord>();
        if (vehicleId != null) {
            wrapper.eq(ParkingRecord::getVehicleId, vehicleId);
        }
        if (plateNumber != null && !plateNumber.isBlank()) {
            wrapper.like(ParkingRecord::getPlateNumber, plateNumber);
        }
        if (status != null && !status.isBlank()) {
            wrapper.eq(ParkingRecord::getStatus, status);
        }
        wrapper.orderByDesc(ParkingRecord::getEntryTime);
        IPage<ParkingRecord> pageResult = parkingRecordService.page(page, wrapper);
        return Result.success(new PageResult<>(pageResult.getTotal(), pageResult.getRecords()));
    }

    @GetMapping("/{id}")
    public Result<ParkingRecord> getById(@PathVariable Long id) {
        ParkingRecord record = parkingRecordService.getById(id);
        if (record == null) {
            return Result.error("记录不存在");
        }
        return Result.success(record);
    }

    @PostMapping
    public Result<String> save(@RequestBody ParkingRecord record) {
        if (record.getVehicleId() == null || record.getPlateNumber() == null || record.getEntryTime() == null) {
            return Result.error("车辆ID、车牌号、进入时间不能为空");
        }
        if (record.getStatus() == null) {
            record.setStatus("PARKING");
        }
        parkingRecordService.save(record);
        return Result.success("新增成功");
    }

    @PutMapping("/{id}")
    public Result<String> update(@PathVariable Long id, @RequestBody ParkingRecord record) {
        if (parkingRecordService.getById(id) == null) {
            return Result.error("记录不存在");
        }
        record.setId(id);
        parkingRecordService.updateById(record);
        return Result.success("更新成功");
    }

    @DeleteMapping("/{id}")
    public Result<String> delete(@PathVariable Long id) {
        if (parkingRecordService.getById(id) == null) {
            return Result.error("记录不存在");
        }
        parkingRecordService.removeById(id);
        return Result.success("删除成功");
    }

    @GetMapping("/list")
    public Result<List<ParkingRecord>> list(@RequestParam(required = false) Long vehicleId) {
        var wrapper = new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<ParkingRecord>();
        if (vehicleId != null) {
            wrapper.eq(ParkingRecord::getVehicleId, vehicleId);
        }
        wrapper.orderByDesc(ParkingRecord::getEntryTime);
        return Result.success(parkingRecordService.list(wrapper));
    }
}
