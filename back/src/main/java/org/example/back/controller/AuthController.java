package org.example.back.controller;

import jakarta.validation.Valid;
import org.example.back.common.Result;
import org.example.back.dto.LoginDTO;
import org.example.back.entity.User;
import org.example.back.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * 认证控制器
 */
@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = "*")
public class AuthController {
    
    @Autowired
    private UserService userService;

    /**
     * 用户登录
     */
    @PostMapping("/login")
    public Result<Map<String, Object>> login(@Valid @RequestBody LoginDTO loginDTO) {
        User user = userService.getByUsername(loginDTO.getUsername());
        
        if (user == null) {
            return Result.error("用户名或密码错误");
        }
        
        // 明文密码比较
        if (!loginDTO.getPassword().equals(user.getPassword())) {
            return Result.error("用户名或密码错误");
        }
        
        if (user.getStatus() == 0) {
            return Result.error("账户已被禁用");
        }
        
        Map<String, Object> data = new HashMap<>();
        data.put("user", user);
        
        return Result.success("登录成功", data);
    }
}

