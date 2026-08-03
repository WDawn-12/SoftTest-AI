-- ============================================================
-- AITestAgent 数据库初始化脚本
-- 项目：基于 AI Agent 的软件测试辅助平台
-- 适用：MySQL 8.0
-- 说明：Docker Compose 首次启动 MySQL 时自动执行；
--       也可手动执行：mysql -u root -p < docs/sql/init.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS `aitest_agent`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `aitest_agent`;

-- ------------------------------------------------------------
-- 1. 用户表 users
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
  `id`            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username`      VARCHAR(50)  NOT NULL COMMENT '用户名',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希（bcrypt）',
  `nickname`      VARCHAR(50)  DEFAULT NULL COMMENT '昵称',
  `email`         VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
  `role`          VARCHAR(20)  NOT NULL DEFAULT 'user' COMMENT '角色：admin/user',
  `status`        TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1启用 0禁用',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_users_username` (`username`),
  KEY `idx_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ------------------------------------------------------------
-- 2. 项目表 projects
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '项目ID',
  `name`        VARCHAR(100) NOT NULL COMMENT '项目名称',
  `description` TEXT         DEFAULT NULL COMMENT '项目描述',
  `status`      VARCHAR(20)  NOT NULL DEFAULT 'active' COMMENT '状态：active/finished/archived',
  `owner_id`    BIGINT       DEFAULT NULL COMMENT '创建人用户ID',
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_projects_owner_id` (`owner_id`),
  CONSTRAINT `fk_projects_owner` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测试项目表';

-- ------------------------------------------------------------
-- 3. 需求文档表 requirements
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `requirements` (
  `id`            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '需求ID',
  `project_id`    BIGINT       NOT NULL COMMENT '所属项目ID',
  `file_name`     VARCHAR(255) NOT NULL COMMENT '原始文件名',
  `file_path`     VARCHAR(500) NOT NULL COMMENT '文件存储路径',
  `file_type`     VARCHAR(20)  DEFAULT NULL COMMENT '文件类型：docx/pdf/txt',
  `file_size`     BIGINT       DEFAULT NULL COMMENT '文件大小（字节）',
  `content`       TEXT         DEFAULT NULL COMMENT '文档提取的纯文本内容',
  `parse_status`  VARCHAR(20)  NOT NULL DEFAULT 'pending' COMMENT '解析状态：pending/parsing/completed/failed',
  `parse_result`  TEXT         DEFAULT NULL COMMENT 'AI 解析结果（JSON 文本）',
  `error_message` VARCHAR(500) DEFAULT NULL COMMENT '解析失败原因',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_requirements_project_id` (`project_id`),
  CONSTRAINT `fk_requirements_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='需求文档表';

-- ------------------------------------------------------------
-- 4. 功能模块表 modules
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `modules` (
  `id`             BIGINT       NOT NULL AUTO_INCREMENT COMMENT '模块ID',
  `project_id`     BIGINT       NOT NULL COMMENT '所属项目ID',
  `requirement_id` BIGINT       DEFAULT NULL COMMENT '来源需求ID',
  `name`           VARCHAR(100) NOT NULL COMMENT '模块名称',
  `description`    TEXT         DEFAULT NULL COMMENT '模块描述',
  `sort_order`     INT          NOT NULL DEFAULT 0 COMMENT '排序号',
  `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_modules_project_id` (`project_id`),
  KEY `idx_modules_requirement_id` (`requirement_id`),
  CONSTRAINT `fk_modules_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_modules_requirement` FOREIGN KEY (`requirement_id`) REFERENCES `requirements` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='功能模块表';

-- ------------------------------------------------------------
-- 5. 测试用例表 test_cases（字段与 Excel 导出格式对应）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `test_cases` (
  `id`              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '用例ID',
  `project_id`      BIGINT       NOT NULL COMMENT '所属项目ID',
  `requirement_id`  BIGINT       DEFAULT NULL COMMENT '来源需求ID',
  `module_id`       BIGINT       DEFAULT NULL COMMENT '所属模块ID',
  `case_no`         VARCHAR(50)  NOT NULL COMMENT '用例编号',
  `title`           VARCHAR(200) NOT NULL COMMENT '功能名称',
  `test_point`      VARCHAR(500) DEFAULT NULL COMMENT '测试点',
  `priority`        VARCHAR(20)  NOT NULL DEFAULT '中' COMMENT '优先级：高/中/低',
  `preconditions`   TEXT         DEFAULT NULL COMMENT '前置条件',
  `steps`           TEXT         DEFAULT NULL COMMENT '测试步骤',
  `expected_result` TEXT         DEFAULT NULL COMMENT '预期结果',
  `remark`          VARCHAR(500) DEFAULT NULL COMMENT '备注',
  `status`          VARCHAR(20)  NOT NULL DEFAULT 'draft' COMMENT '状态：draft/approved',
  `created_by`      BIGINT       DEFAULT NULL COMMENT '创建人用户ID',
  `created_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_test_cases_project_id` (`project_id`),
  KEY `idx_test_cases_requirement_id` (`requirement_id`),
  KEY `idx_test_cases_module_id` (`module_id`),
  KEY `idx_test_cases_created_by` (`created_by`),
  CONSTRAINT `fk_test_cases_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_test_cases_requirement` FOREIGN KEY (`requirement_id`) REFERENCES `requirements` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_test_cases_module` FOREIGN KEY (`module_id`) REFERENCES `modules` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_test_cases_creator` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测试用例表';

-- ------------------------------------------------------------
-- 6. AI 聊天记录表 chat_history
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `chat_history` (
  `id`         BIGINT      NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `user_id`    BIGINT      NOT NULL COMMENT '用户ID',
  `project_id` BIGINT      DEFAULT NULL COMMENT '关联项目ID（可空）',
  `role`       VARCHAR(20) NOT NULL COMMENT '角色：user/assistant',
  `content`    TEXT        NOT NULL COMMENT '消息内容',
  `created_at` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_chat_history_user_id` (`user_id`),
  KEY `idx_chat_history_project_id` (`project_id`),
  CONSTRAINT `fk_chat_history_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_chat_history_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI 聊天记录表';

-- ------------------------------------------------------------
-- 7. 操作日志表 operation_logs
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `operation_logs` (
  `id`         BIGINT       NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `user_id`    BIGINT       DEFAULT NULL COMMENT '操作用户ID',
  `action`     VARCHAR(100) NOT NULL COMMENT '操作动作',
  `module`     VARCHAR(50)  NOT NULL COMMENT '操作模块',
  `detail`     TEXT         DEFAULT NULL COMMENT '操作详情',
  `ip`         VARCHAR(50)  DEFAULT NULL COMMENT '操作来源 IP',
  `created_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_operation_logs_user_id` (`user_id`),
  CONSTRAINT `fk_operation_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- ------------------------------------------------------------
-- 8. 测试点表 test_points
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `test_points` (
  `id`             BIGINT       NOT NULL AUTO_INCREMENT COMMENT '测试点ID',
  `project_id`     BIGINT       NOT NULL COMMENT '所属项目ID',
  `requirement_id` BIGINT       DEFAULT NULL COMMENT '来源需求ID',
  `module_id`      BIGINT       DEFAULT NULL COMMENT '所属模块ID',
  `name`           VARCHAR(255) NOT NULL COMMENT '测试点描述',
  `category`       VARCHAR(50)  NOT NULL DEFAULT 'normal' COMMENT '类别：normal/exception/boundary/security/compatibility',
  `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_test_points_project_id` (`project_id`),
  KEY `idx_test_points_requirement_id` (`requirement_id`),
  KEY `idx_test_points_module_id` (`module_id`),
  CONSTRAINT `fk_test_points_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_test_points_requirement` FOREIGN KEY (`requirement_id`) REFERENCES `requirements` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_test_points_module` FOREIGN KEY (`module_id`) REFERENCES `modules` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测试点表';

-- ------------------------------------------------------------
-- 初始数据：管理员账号 admin / admin123
-- 密码为 bcrypt 哈希；登录功能上线后请立即修改默认密码。
-- ------------------------------------------------------------
INSERT INTO `users` (`username`, `password_hash`, `nickname`, `role`)
VALUES ('admin', '$2b$12$7Gq7//syYe5etUjTyutQMuPc2IihEomU1TnoMe1S9YZUtdoMeSRTq', '系统管理员', 'admin')
ON DUPLICATE KEY UPDATE `username` = `username`;
