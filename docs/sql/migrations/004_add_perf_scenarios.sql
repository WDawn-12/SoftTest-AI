-- 004: 性能测试场景表（性能压测模块）
CREATE TABLE IF NOT EXISTS `perf_scenarios` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '场景ID',
  `project_id` BIGINT NOT NULL COMMENT '所属项目ID',
  `name` VARCHAR(200) NOT NULL COMMENT '场景名称',
  `description` VARCHAR(500) DEFAULT NULL COMMENT '场景描述',
  `thread_count` INT NOT NULL DEFAULT 50 COMMENT '并发用户数',
  `loop_count` INT NOT NULL DEFAULT 10 COMMENT '循环次数',
  `ramp_up` INT NOT NULL DEFAULT 10 COMMENT '启动时间（秒）',
  `think_time_ms` INT NOT NULL DEFAULT 500 COMMENT '思考时间（毫秒）',
  `base_url` VARCHAR(200) NOT NULL DEFAULT 'localhost' COMMENT '目标主机/IP（不含协议端口）',
  `base_port` VARCHAR(10) NOT NULL DEFAULT '8000' COMMENT '目标端口',
  `interface_ids` TEXT COMMENT '关联接口ID列表（JSON 数组，空=全部接口）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_perf_scenario_project` (`project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='性能测试场景表';
