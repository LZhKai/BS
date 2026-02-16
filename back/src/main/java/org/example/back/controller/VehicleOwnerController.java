package org.example.back.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.example.back.common.PageResult;
import org.example.back.common.Result;
import org.example.back.entity.VehicleOwner;
import org.example.back.service.VehicleOwnerService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 车主管理控制器
 */
@RestController
@RequestMapping("/api/owner")
@CrossOrigin(origins = "*")
public class VehicleOwnerController {

    @Autowired
    private VehicleOwnerService vehicleOwnerService;

    @GetMapping("/page")
    public Result<PageResult<VehicleOwner>> page(
            @RequestParam(defaultValue = "1") Long current,
            @RequestParam(defaultValue = "10") Long size,
            @RequestParam(required = false) String name,
            @RequestParam(required = false) String phone) {
        Page<VehicleOwner> page = new Page<>(current, size);
        var wrapper = new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<VehicleOwner>();
        if (name != null && !name.isBlank()) {
            wrapper.like(VehicleOwner::getName, name);
        }
        if (phone != null && !phone.isBlank()) {
            wrapper.like(VehicleOwner::getPhone, phone);
        }
        wrapper.orderByDesc(VehicleOwner::getCreateTime);
        IPage<VehicleOwner> pageResult = vehicleOwnerService.page(page, wrapper);
        return Result.success(new PageResult<>(pageResult.getTotal(), pageResult.getRecords()));
    }

    @GetMapping("/{id}")
    public Result<VehicleOwner> getById(@PathVariable Long id) {
        VehicleOwner owner = vehicleOwnerService.getById(id);
        if (owner == null) {
            return Result.error("车主不存在");
        }
        return Result.success(owner);
    }

    @PostMapping
    public Result<String> save(@RequestBody VehicleOwner owner) {
        if (owner.getName() == null || owner.getName().isBlank()) {
            return Result.error("车主姓名不能为空");
        }
        vehicleOwnerService.save(owner);
        return Result.success("新增成功");
    }

    @PutMapping("/{id}")
    public Result<String> update(@PathVariable Long id, @RequestBody VehicleOwner owner) {
        if (vehicleOwnerService.getById(id) == null) {
            return Result.error("车主不存在");
        }
        owner.setId(id);
        vehicleOwnerService.updateById(owner);
        return Result.success("更新成功");
    }

    @DeleteMapping("/{id}")
    public Result<String> delete(@PathVariable Long id) {
        if (vehicleOwnerService.getById(id) == null) {
            return Result.error("车主不存在");
        }
        vehicleOwnerService.removeById(id);
        return Result.success("删除成功");
    }

    @GetMapping("/list")
    public Result<List<VehicleOwner>> list() {
        return Result.success(vehicleOwnerService.list());
    }
}
