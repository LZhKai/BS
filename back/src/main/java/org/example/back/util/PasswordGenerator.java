package org.example.back.util;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

/**
 * 密码生成工具类
 * 用于生成BCrypt加密的密码哈希值
 * 运行main方法可以生成指定密码的BCrypt哈希值
 */
public class PasswordGenerator {
    
    public static void main(String[] args) {
        BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
        String password = "admin123"; // 要加密的密码
        String hashedPassword = encoder.encode(password);
        System.out.println("原始密码: " + password);
        System.out.println("BCrypt哈希值: " + hashedPassword);
    }
}

