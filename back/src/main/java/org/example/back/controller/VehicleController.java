package org.example.back.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import jakarta.validation.Valid;
import org.example.back.common.PageResult;
import org.example.back.common.Result;
import org.example.back.dto.VehicleDTO;
import org.example.back.entity.Vehicle;
import org.example.back.service.VehicleService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 车辆管理控制器
 */
@RestController
@RequestMapping("/api/vehicle")
@CrossOrigin(origins = "*")
public class VehicleController {
    
    @Autowired
    private VehicleService vehicleService;

    /**
     * 分页查询车辆列表
     */
    @GetMapping("/page")
    public Result<PageResult<Vehicle>> page(
            @RequestParam(defaultValue = "1") Long current,
            @RequestParam(defaultValue = "10") Long size,
            @RequestParam(required = false) String plateNumber,
            @RequestParam(required = false) String ownerName,
            @RequestParam(required = false) String status) {
        
        Page<Vehicle> page = new Page<>(current, size);
        IPage<Vehicle> pageResult = vehicleService.pageQuery(page, plateNumber, ownerName, status);
        
        PageResult<Vehicle> result = new PageResult<>(pageResult.getTotal(), pageResult.getRecords());
        return Result.success(result);
    }

    /**
     * 根据ID查询车辆
     */
    @GetMapping("/{id}")
    public Result<Vehicle> getById(@PathVariable Long id) {
        Vehicle vehicle = vehicleService.getById(id);
        if (vehicle == null) {
            return Result.error("车辆不存在");
        }
        return Result.success(vehicle);
    }

    /**
     * 新增车辆
     */
    @PostMapping
    public Result<String> save(@Valid @RequestBody VehicleDTO vehicleDTO) {
        // 检查车牌号是否已存在
        Vehicle existVehicle = vehicleService.lambdaQuery()
                .eq(Vehicle::getPlateNumber, vehicleDTO.getPlateNumber())
                .one();
        if (existVehicle != null) {
            return Result.error("车牌号已存在");
        }
        
        Vehicle vehicle = new Vehicle();
        BeanUtils.copyProperties(vehicleDTO, vehicle);
        if (vehicle.getStatus() == null) {
            vehicle.setStatus("NORMAL");
        }
        
        vehicleService.save(vehicle);
        return Result.success("新增成功");
    }

    /**
     * 更新车辆信息
     */
    @PutMapping("/{id}")
    public Result<String> update(@PathVariable Long id, @Valid @RequestBody VehicleDTO vehicleDTO) {
        Vehicle vehicle = vehicleService.getById(id);
        if (vehicle == null) {
            return Result.error("车辆不存在");
        }
        
        // 检查车牌号是否被其他车辆使用
        Vehicle existVehicle = vehicleService.lambdaQuery()
                .eq(Vehicle::getPlateNumber, vehicleDTO.getPlateNumber())
                .ne(Vehicle::getId, id)
                .one();
        if (existVehicle != null) {
            return Result.error("车牌号已被其他车辆使用");
        }
        
        BeanUtils.copyProperties(vehicleDTO, vehicle);
        vehicle.setId(id);
        vehicleService.updateById(vehicle);
        return Result.success("更新成功");
    }

    /**
     * 删除车辆
     */
    @DeleteMapping("/{id}")
    public Result<String> delete(@PathVariable Long id) {
        Vehicle vehicle = vehicleService.getById(id);
        if (vehicle == null) {
            return Result.error("车辆不存在");
        }
        vehicleService.removeById(id);
        return Result.success("删除成功");
    }

    /**
     * 批量删除车辆
     */
    @DeleteMapping("/batch")
    public Result<String> deleteBatch(@RequestBody List<Long> ids) {
        vehicleService.removeByIds(ids);
        return Result.success("批量删除成功");
    }

    /**
     * 获取所有车辆（不分页）
     */
    @GetMapping("/list")
    public Result<List<Vehicle>> list() {
        List<Vehicle> list = vehicleService.list();
        return Result.success(list);
    }
}

