package org.example.back.service;

import com.baomidou.mybatisplus.extension.service.IService;
import org.example.back.entity.User;

/**
 * 用户服务接口
 */
public interface UserService extends IService<User> {
    /**
     * 根据用户名查询用户
     */
    User getByUsername(String username);
}

